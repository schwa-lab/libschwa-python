# vim: set ts=2 et:
import inspect

import msgpack

from .constants import FIELD_TYPE_NAME, FIELD_TYPE_POINTER_TO, FIELD_TYPE_IS_SLICE, FIELD_TYPE_IS_SELF_POINTER
from .exceptions import ReaderException
from .runtime import RTField, RTStore, RTAnn, RTManager
from .meta import Ann, Doc
from .schema import DocSchema

__all__ = ['Reader']


class Reader(object):
  __slots__ = ('_doc', '_doc_schema', '_unpacker')

  WIRE_VERSION = 2  # version of the wire protocol the reader knows how to process

  def __init__(self, arg):
    if isinstance(arg, DocSchema):
      self._doc_schema = arg
    elif inspect.isclass(arg) and issubclass(arg, Doc):
      self._doc_schema = arg.schema()
    else:
      raise TypeError('Invalid value for arg. Must be either a DocSchema instance or a Doc subclass')
    self._doc = None
    self._unpacker = None

  def __iter__(self):
    return self

  def next(self):
    self._read_doc()
    if self._doc is None:
      raise StopIteration()
    return self._doc

  def stream(self, istream):
    self._unpacker = msgpack.Unpacker(istream)
    return self

  def _read_doc(self):
    # read in the version number
    version = self._unpacker.unpack()
    if version is None:
      self._doc = None
      return

    # validate wire protocol version
    if version != Reader.WIRE_VERSION:
      raise ReaderException('Invalid wire format version. Stream has version {0} but I can read {1}'.format(version, Reader.WIRE_VERSION))

    # create the Doc instance and RTManager
    doc = self._doc = self._doc_schema.defn()
    doc._dr_rt = RTManager()

    # read headers
    self._read_klasses()
    self._read_stores()
    self._backfill_pointer_fields()

  def _read_klasses(self):
    # read <klasses> ::= [ <klass> ]
    #        <klass> ::= ( <klass_name>, <fields> )
    rt = self._doc._dr_rt
    read = self._unpacker.unpack()
    for k, (klass_name, fields) in enumerate(read):
      # construct the RTAnn instance for the class
      ann_schema = self._doc_schema.klass_by_serial(klass_name)
      if klass_name == '__meta__':
        rtschema = RTAnn(k, klass_name, self._doc_schema)
        rt.doc = rtschema
      else:
        rtschema = RTAnn(k, klass_name, ann_schema)
      rt.klasses.append(rtschema)

      # for each <fields> ::= [ <field> ]
      for f, field in enumerate(fields):
        field_name = points_to = None
        is_pointer = is_self_pointer = is_slice = False

        # process fields map <field> ::= { <field_type> : <field_val> }
        for key, val in field.iteritems():
          if key == FIELD_TYPE_NAME:
            field_name = val
          elif key == FIELD_TYPE_POINTER_TO:
            points_to = val
            is_pointer = True
          elif key == FIELD_TYPE_IS_SLICE:
            if val != None:
              raise ReaderException('Expected NIL value for IS_SLICE key, got {0!r} instead'.format(val))
            is_slice = True
          elif key == FIELD_TYPE_IS_SELF_POINTER:
            if val != None:
              raise ReaderException('Expected NIL value for IS_SELF_POINTER key, got {0!r} instead'.format(val))
            is_self_pointer = True
          else:
            raise ReaderException('Unknown key {0!r} in <field> map'.format(key))

        # sanity check values
        if field_name is None:
          raise ReaderException('Field number {0} did not contain a NAME key'.format(f + 1))

        # see if the read in field exists on the registered class's schema
        if rtschema.is_lazy():
          rtfield = RTField(f, field_name, points_to, is_slice, is_self_pointer)
        else:
          # try and find the field on the registered class
          defn = None
          for fs in rtschema.defn.fields():
            if fs.serial == field_name:
              defn = fs
              break
          rtfield = RTField(f, field_name, points_to, is_slice, is_self_pointer, defn)

          # perform some sanity checks that the type of data on the stream is what we're expecting
          if defn is not None:
            if is_pointer != defn.is_pointer:
              raise ReaderException("Field {0!r} of class {1!r} has IS_POINTER as {2} on the stream, but {3} on the class's field".format(field_name, klass_name, is_pointer, defn.is_pointer))
            if is_slice != defn.is_slice:
              raise ReaderException("Field {0!r} of class {1!r} has IS_SLICE as {2} on the stream, but {3} on the class's field".format(field_name, klass_name, is_slice, defn.is_slice))
            if is_self_pointer != defn.is_self_pointer:
              raise ReaderException("Field {0!r} of class {1!r} has IS_SELF_POINTER as {2} on the stream, but {3} on the class's field".format(field_name, klass_name, is_self_pointer, defn.is_self_pointer))

        # add the field to the schema
        rtschema.fields.append(rtfield)

    # ensure we found a document class
    if rt.doc is None:
      raise ReaderException('Did not read in a __meta__ class')

  def _read_stores(self):
    # read <stores> ::= [ <store> ]
    #       <store> ::= ( <store_name>, <klass_id>, <store_nelem> )
    rt = self._doc._dr_rt
    read = self._unpacker.unpack()
    for s, (store_name, klass_id, nelem) in enumerate(read):
      # sanity check on the value of the klass_id
      if klass_id >= len(rt.klasses):
        raise ReaderException('klass_id value {0} >= number of klasses ({1})'.format(klass_id, len(rt.klasses)))

      # lookup the store on the Doc class
      defn = None
      for ss in self._doc_schema.stores():
        if ss.serial == store_name:
          defn = ss
          break

      # construct and keep track of RTStore
      if defn is None:
        rtstore = RTStore(s, store_name, rt.klasses[klass_id], lazy=nelem)
      else:
        rtstore = RTStore(s, store_name, rt.klasses[klass_id], defn=defn)
      rt.doc.stores.append(rtstore)

      # ensure that the stream store and the static store agree on the klass they're storing
      if not rtstore.is_lazy():
        store_stored_type = defn.stored_type
        if rt.klasses[klass_id].is_lazy():
          raise ReaderException('Store {0!r} points to {1} but the store on the stream points to a lazy type.'.format(store_name, store_stored_type))
        stored_klass_type = rt.klasses[klass_id].defn
        if store_stored_type != stored_klass_type:
          raise ReaderException('Store {0!r} points to {1} but the stream says it points to {2}.'.format(store_name, store_stored_type, stored_klass_type))

  def _backfill_pointer_fields(self):
    rt = self._doc._dr_rt
    for klass in rt.klasses:
      for field in klass.fields:
        if field.is_pointer:
          # sanity check on the value of store_id
          store_id = field.points_to
          if store_id >= len(rt.doc.stores):
            raise ReaderException('store_id value {0} >= number of stores ({1})'.format(store_id, len(rt.doc.stores)))
          rtstore = rt.doc.stores[store_id]

          # ensure the field points to a store of the same type as what the store actually is
          if not field.is_lazy():
            field_type = field.defn.points_to
            store_type = rtstore.defn.stored_type
            if field_type != store_type:
              raise ReaderException('field points at {0} but store contains {1}'.format(field_type, store_type))

          # backfill
          field.points_to = rtstore


# =============================================================================
# =============================================================================
def serialised_instance_to_dict(obj, wire_type):
  """
  Converts a serialised instance obj to a dictionary which can be
  used as the kwargs for the constructor of the class represented
  by wire_type.
  """
  instance = {}  # { serial : val }
  for f in wire_type.fields:
    val = obj.get(f.number)
    if val is not None:
      if f.is_range:
        assert len(val) == 2
        val = slice(val[0], val[1])
      if f.is_pointer and isinstance(val, (list, tuple)):
        f.set_collection()
      instance[f.name] = val
  return instance


def instantiate_instance(instance, klass):
  """
  Converts a dictionary returned by serialised_instance_to_dict into an actual
  Python object of type klass
  """
  s2p = klass._dr_s2p
  vals = dict((s2p[k], v) for k, v in instance.iteritems())
  return klass.from_wire(**vals)


class WireStore(object):
  __slots__ = ('name', 'nelem', 'wire_type', 'is_collection', '_instances', 'store')

  def __init__(self, name, nelem, wire_type):
    self.name = name
    self.nelem = nelem
    self.wire_type = wire_type
    self.is_collection = True
    self._instances = []
    self.store = None

  def add_instance(self, obj):
    instance = serialised_instance_to_dict(obj, self.wire_type)
    self._instances.append(instance)

  def instantiate_instances(self):
    klass = self.wire_type.klass()
    for i in self._instances:
      yield instantiate_instance(i, klass)


class WireField(object):
  __slots__ = ('number', 'name', 'pointer_to', 'is_range', 'is_collection', '_dr_field')

  def __init__(self, number, field):
    self.number = number
    self.name = field[FIELD_TYPE_NAME]
    self.pointer_to = field.get(FIELD_TYPE_POINTER_TO)
    self.is_range = FIELD_TYPE_IS_SLICE in field
    self.is_collection = False
    self._dr_field = None

  def __repr__(self):
    return 'WireField({0!r})'.format(self.name)

  def __str__(self):
    return self.name

  @property
  def is_pointer(self):
    return self.pointer_to is not None

  def set_collection(self, val=True):
    self.is_collection = val
    if self._dr_field is not None:
      self._dr_field.is_collection = val

  def dr_field(self):
    if self._dr_field is None:
      if self.is_range:
        if self.is_pointer:
          store = self.pointer_to.name
          klass = self.pointer_to.wire_type.name
          self._dr_field = Slice(klass, store=store, serial=self.name)
        else:
          self._dr_field = Slice(serial=self.name)
      elif self.is_pointer:
        store = self.pointer_to.name
        klass = self.pointer_to.wire_type.name
        if self.is_collection:
          self._dr_field = Pointers(klass, store=store, serial=self.name)
        else:
          self._dr_field = Pointer(klass, store=store, serial=self.name)
      else:
        self._dr_field = Field(serial=self.name)
    return self._dr_field


class WireType(object):
  __slots__ = ('number', 'name', 'fields', 'pointer_fields', 'is_meta', 'module', '_klass')

  by_number = {}

  def __init__(self, number, name, klass_fields, module=None):
    self.number = number
    self.name = name
    self.fields = [WireField(i, f) for i, f in enumerate(klass_fields)]
    self.pointer_fields = [f for f in self.fields if f.is_pointer and not f.is_range]
    self.is_meta = name == '__meta__'
    self.module = module
    self._klass = None
    WireType.by_number[number] = self

  def __repr__(self):
    return 'WireType({0!r})'.format(self.name)

  def __str__(self):
    return self.name

  def create_klass(self, doc_klass=None):
    if self._klass is not None:
      return

    if self.is_meta:
      if doc_klass is None:
        klass_name = 'Document'
        klass = AnnotationMeta.cached(klass_name, self.module)
      else:
        klass = doc_klass
    else:
      klass_name = self.name
      klass = AnnotationMeta.cached(klass_name, self.module)

    dr_fields = dict((f.name, f.dr_field()) for f in self.fields)
    if klass is None:
      dr_fields['__module__'] = self.module
      if self.is_meta:
        klass = type(klass_name, (Document, ), dr_fields)
      else:
        klass = type(klass_name, (Annotation, ), dr_fields)
    else:
      klass.update_attrs(dr_fields)
    self._klass = klass
    return self._klass

  def klass(self):
    return self._klass


#class Reader(object):
  #__slots__ = ('_doc_klass', '_meta_module', '_unpacker', '_doc')

  #def __init__(self, doc_klass=None):
    #self._doc_klass = doc_klass
    #if doc_klass and not issubclass(doc_klass, Document):
      #raise ValueError('"doc_klass" must be a subclass of Document')
    #self._meta_module = AnnotationMeta.generate_module()
    #if doc_klass:
      ## Register aliases for known types
      #AnnotationMeta.register(doc_klass, self._meta_module)
      #for name, store in doc_klass._dr_stores.iteritems():
        #if store._klass:
          #AnnotationMeta.register(store._klass, self._meta_module)

  #def __iter__(self):
    #return self

  #def next(self):
    #self._read_doc()
    #if self._doc is None:
      #raise StopIteration()
    #return self._doc

  #def stream(self, istream):
    #self._unpacker = msgpack.Unpacker(istream)
    #return self

  #def _unpack(self):
    #try:
        #obj = self._unpacker.unpack()
    #except StopIteration:
        #return None
    #return obj

  #def _update_pointers(self, objs, pointer_fields):
    #for obj in objs:
      #for field in pointer_fields:
        #old = getattr(obj, field.name)
        #if old is None:
          #continue
        #store = getattr(self._doc, field.pointer_to.name)
        #if field.is_collection:
          #new = [store[i] for i in old]
        #else:
          #new = store[old]
        #setattr(obj, field.name, new)

  #def _read_doc(self):
    ## attempt to read the header
    #header = self._unpack()  # [ ( name, [ { field_key : field_val } ] ) ]
    #if header is None:
      #self._doc = None
      #return

    ## decode the klasses header
    #wire_types, wire_meta = [], None
    #for i, (klass_name, klass_fields) in enumerate(header):
      #t = WireType(i, klass_name, klass_fields, self._meta_module)
      #wire_types.append(t)
      #if t.is_meta:
        #wire_meta = t
    #assert wire_meta is not None

    ## decode the stores header
    #header = self._unpack()  # [ ( store_name, klass_id, store_nelem ) ]
    #wire_stores = []
    #for name, klass_id, nelem in header:
      #wire_type = WireType.by_number[klass_id]
      #wire_stores.append(WireStore(name, nelem, wire_type))

    ## update the POINTER_TO values in the WireFields to point to their corresponding WireStore objects
    #for t in wire_types:
      #for f in t.fields:
        #if f.is_pointer:
          #f.pointer_to = wire_stores[f.pointer_to]

    ## instantiate / create each of the required classes
    #for t in wire_types:
      #if not t.is_meta:
        #t.create_klass()

    ## decode the document instance
    #self._unpack()  # nbytes (unused in the Python API)
    #doc_blob = self._unpack()
    #assert isinstance(doc_blob, dict)

    ## decode each of the instances groups
    #for s in wire_stores:
      #self._unpack()  # nbytes (unused in the Python API)
      #blob = self._unpack()

      #if isinstance(blob, dict):
        #s.is_collection = False
        #s.add_instance(blob)
      #else:
        #assert isinstance(blob, (list, tuple))
        #for obj in blob:
          #s.add_instance(obj)

    ## instantiate each of the Stores
    #stores = {}
    #for s in wire_stores:
      #klass = s.wire_type.klass()
      #storage = Store if s.is_collection else Singleton
      #stores[s.name] = s.store = storage(klass)

    ## create and update the Document type
    #self._doc_klass = wire_meta.create_klass(self._doc_klass)
    #self._doc_klass.update_attrs(stores)

    ## instantiate the Document
    #doc_vals = serialised_instance_to_dict(doc_blob, wire_meta)
    #self._doc = instantiate_instance(doc_vals, self._doc_klass)

    ## instantiate all of the instances
    #for s in wire_stores:
      #if s.is_collection:
        #s.name = self._doc._dr_s2p[s.name]
        #store = getattr(self._doc, s.name)
        #store.clear()
        #for obj in s.instantiate_instances():
          #store.append(obj)
      #else:
        #objs = tuple(s.instantiate_instances())
        #assert len(objs) == 1
        #setattr(self._doc, s.name, objs[0])

    ## update the pointers on the document
    #pointer_fields = wire_meta.pointer_fields
    #if pointer_fields:
      #self._update_pointers((self._doc, ), pointer_fields)

    ## update the pointers on the instances
    #for s in wire_stores:
      #pointer_fields = s.wire_type.pointer_fields
      #if pointer_fields:
        #objs = getattr(self._doc, s.name)
        #if not s.is_collection:
          #objs = (objs, )
        #self._update_pointers(objs, pointer_fields)

    ## call post-reading hook.
    #self._doc.ready()
