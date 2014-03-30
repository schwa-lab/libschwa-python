# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import inspect
import io

import msgpack
import six
from six.moves import xrange

from .constants import FieldType
from .exceptions import ReaderException
from .fields_core import Field, Pointer, Pointers, SelfPointer, SelfPointers, Slice, Store
from .meta import Doc
from .rtklasses import get_or_create_klass
from .runtime import RTManager, AutomagicRTManager
from .schema import AnnSchema, DocSchema, FieldSchema, StoreSchema

__all__ = ['Reader']


class RTReader(object):
  __slots__ = ('_doc_schema',)
  Manager = RTManager

  WIRE_VERSION = 2  # Version of the wire protocol the reader knows how to process.

  def __init__(self, schema):
    self._doc_schema = schema

  def __call__(self, unpacker):
    try:
      version = unpacker.unpack()
    except msgpack.OutOfData:
      return None
    # Validate wire protocol version.
    if version != self.WIRE_VERSION:
      raise ReaderException('Invalid wire format version. Stream has version {0} but I can read {1}. Ensure the input is not plain text.'.format(version, self.WIRE_VERSION))

    rt = self.Manager()
    self._read_klasses(rt, unpacker.unpack())
    self._read_stores(rt, unpacker.unpack())
    self._backfill_pointer_fields(rt)
    return rt

  def _read_klasses(self, rt, read):
    # read <klasses> ::= [ <klass> ]
    #        <klass> ::= ( <klass_name>, <fields> )
    for k, (klass_name, fields) in enumerate(read):
      klass_name = klass_name.decode('utf-8')
      # Construct the RTAnn instance for the class.
      if klass_name == '__meta__':
        rtschema = rt.Ann(k, klass_name, self._doc_schema)
        rt.doc = rtschema
      else:
        ann_schema = self._doc_schema.klass_by_serial(klass_name)
        rtschema = rt.Ann(k, klass_name, ann_schema)
      rt.klasses.append(rtschema)

      # For each <fields> ::= [ <field> ].
      for f, field in enumerate(fields):
        field_name = points_to = None
        is_pointer = is_self_pointer = is_slice = is_collection = False

        # Process fields map <field> ::= { <field_type> : <field_val> }.
        for key, val in six.iteritems(field):
          if key == FieldType.NAME:
            field_name = val.decode('utf-8')
          elif key == FieldType.POINTER_TO:
            points_to = val
            is_pointer = True
          elif key == FieldType.IS_SLICE:
            if val is not None:
              raise ReaderException('Expected NIL value for IS_SLICE key, got {0!r} instead'.format(val))
            is_slice = True
          elif key == FieldType.IS_SELF_POINTER:
            if val is not None:
              raise ReaderException('Expected NIL value for IS_SELF_POINTER key, got {0!r} instead'.format(val))
            is_self_pointer = True
          elif key == FieldType.IS_COLLECTION:
            if val is not None:
              raise ReaderException('Expected NIL value for IS_COLLECTION key, got {0!r} instead'.format(val))
            is_collection = True
          else:
            raise ReaderException('Unknown key {0!r} in <field> map'.format(key))

        # Sanity check values.
        if field_name is None:
          raise ReaderException('Field number {0} did not contain a NAME key'.format(f + 1))

        # See if the read in field exists on the registered class's schema.
        if rtschema.is_lazy():
          rtfield = rt.Field(f, field_name, points_to, is_slice, is_self_pointer, is_collection)
        else:
          # Try and find the field on the registered class.
          defn = None
          for fs in rtschema.defn.fields():
            if fs.serial == field_name:
              defn = fs
              break
          rtfield = rt.Field(f, field_name, points_to, is_slice, is_self_pointer, is_collection, defn=defn)

          # perform some sanity checks that the type of data on the stream is what we're expecting
          if defn is not None:
            if is_pointer != defn.is_pointer:
              raise ReaderException("Field {0!r} of class {1!r} has IS_POINTER as {2} on the stream, but {3} on the class's field".format(field_name, klass_name, is_pointer, defn.is_pointer))
            if is_slice != defn.is_slice:
              raise ReaderException("Field {0!r} of class {1!r} has IS_SLICE as {2} on the stream, but {3} on the class's field".format(field_name, klass_name, is_slice, defn.is_slice))
            if is_self_pointer != defn.is_self_pointer:
              raise ReaderException("Field {0!r} of class {1!r} has IS_SELF_POINTER as {2} on the stream, but {3} on the class's field".format(field_name, klass_name, is_self_pointer, defn.is_self_pointer))
            if is_collection != defn.is_collection:
              raise ReaderException("Field {0!r} of class {1!r} has IS_COLLECTION as {2} on the stream, but {3} on the class's field".format(field_name, klass_name, is_collection, defn.is_collection))

        # Add the field to the schema.
        rtschema.fields.append(rtfield)

    # Ensure we found a document class.
    if rt.doc is None:
      raise ReaderException('Did not read in a __meta__ class')

  def _read_stores(self, rt, read):
    # read <stores> ::= [ <store> ]
    #       <store> ::= ( <store_name>, <klass_id>, <store_nelem> )
    for s, (store_name, klass_id, nelem) in enumerate(read):
      store_name = store_name.decode('utf-8')
      # Sanity check on the value of the klass_id.
      if klass_id >= len(rt.klasses):
        raise ReaderException('klass_id value {0} >= number of klasses ({1})'.format(klass_id, len(rt.klasses)))

      # Lookup the store on the Doc class.
      defn = None
      for ss in self._doc_schema.stores():
        if ss.serial == store_name:
          defn = ss
          break

      # Construct and keep track of RTStore.
      if defn is None:
        rtstore = rt.Store(s, store_name, rt.klasses[klass_id], nelem=nelem)
      else:
        rtstore = rt.Store(s, store_name, rt.klasses[klass_id], nelem=nelem, defn=defn)
      rt.doc.stores.append(rtstore)

      # Ensure that the stream store and the static store agree on the klass they're storing.
      if not rtstore.is_lazy():
        store_stored_type = defn.stored_type
        if rt.klasses[klass_id].is_lazy():
          raise ReaderException('Store {0!r} points to {1} but the store on the stream points to a lazy type.'.format(store_name, store_stored_type))
        stored_klass_type = rt.klasses[klass_id].defn
        if store_stored_type != stored_klass_type:
          raise ReaderException('Store {0!r} points to {1} but the stream says it points to {2}.'.format(store_name, store_stored_type, stored_klass_type))

  def _backfill_pointer_fields(self, rt):
    for klass in rt.klasses:
      for field in klass.fields:
        if field.is_pointer:
          # Sanity check on the value of store_id.
          store_id = field.points_to
          if store_id >= len(rt.doc.stores):
            raise ReaderException('store_id value {0} >= number of stores ({1})'.format(store_id, len(rt.doc.stores)))
          rtstore = rt.doc.stores[store_id]

          # Ensure the field points to a store of the same type as what the store actually is.
          if not field.is_lazy():
            field_type = field.defn.points_to.stored_type
            store_type = rtstore.defn.stored_type
            if field_type != store_type:
              raise ReaderException('field points at {0} but store contains {1}'.format(field_type, store_type))

          # Backfill.
          field.points_to = rtstore


class AutomagicRTReader(RTReader):
  Manager = AutomagicRTManager
  _automagic_count = 0

  def __call__(self, unpacker):
    rt = super(AutomagicRTReader, self).__call__(unpacker)
    if rt is not None:
      self._do_automagic(rt)
      self._automagic_count += 1
    return rt

  def _do_automagic(self, rt):
    for klass in rt.klasses:
      if klass.is_lazy():
        self._automagic_klass(klass)
    for klass in rt.klasses:
      for store in klass.stores:
        if store.is_lazy():
          self._automagic_store(store, rt.doc)
      for field in klass.fields:
        if field.is_lazy():
          self._automagic_field(field, klass, rt)

  def _automagic_klass(self, rtklass):
    klass = get_or_create_klass(self._automagic_count, rtklass.serial)
    ann_schema = AnnSchema.from_klass(klass)
    rtklass.defn = ann_schema
    self._doc_schema.add_klass(ann_schema)

  def _automagic_store(self, rtstore, rtdoc):
    ann_schema = rtstore.klass.defn
    store = Store(ann_schema.defn)
    defn = StoreSchema(rtstore.serial, store.help, store.serial, store, ann_schema)
    rtstore.defn = defn
    rtdoc.add_kwarg(rtstore.serial, store.default)

  def _automagic_field(self, rtfield, rtklass, rt):
    points_to = None
    if rtfield.is_self_pointer:
      if rtfield.is_collection:
        field = SelfPointers()
      else:
        field = SelfPointer()
    elif rtfield.is_slice:
      if rtfield.is_pointer:
        points_to = rtfield.points_to.defn
        field = Slice(points_to.stored_type.defn, store=points_to.serial)
      else:
        field = Slice()
    elif rtfield.is_pointer:
      points_to = rtfield.points_to.defn
      if rtfield.is_collection:
        field = Pointers(points_to.stored_type.defn, store=points_to.serial)
      else:
        field = Pointer(points_to.stored_type.defn, store=points_to.serial)
    else:
      field = Field()
    defn = FieldSchema(rtfield.serial, field.help, field.serial, field, rtfield.is_pointer, rtfield.is_self_pointer, rtfield.is_slice, rtfield.is_collection, points_to=points_to)
    rtfield.defn = defn
    rtklass.add_kwarg(rtfield.serial, field.default)


class Reader(object):
  __slots__ = ('_doc_schema', '_unpacker', '_read_headers', '_automagic')

  def __init__(self, istream, doc_schema_or_doc=None, automagic=False):
    """
    @param istream A file-like object to read from
    @param doc_schema_or_doc A DocSchema instance or a Doc subclass. If a Doc subclass is provided, the .schema() method is called to create the DocSchema instance.
    @param automagic Whether or not to instantiate unknown classes at runtime. False by default.
    """
    self._unpacker = msgpack.Unpacker(istream, use_list=True)
    self._automagic = automagic
    if doc_schema_or_doc is None:
      if not automagic:
        raise ValueError('doc_schema_or_doc can only be None if automagic is True')
      self._doc_schema = None
    elif isinstance(doc_schema_or_doc, DocSchema):
      self._doc_schema = doc_schema_or_doc
    elif inspect.isclass(doc_schema_or_doc) and issubclass(doc_schema_or_doc, Doc):
      self._doc_schema = doc_schema_or_doc.schema()
    else:
      raise TypeError('Invalid value for doc_schema_or_doc. Must be either a DocSchema instance or a Doc subclass')
    if automagic:
      self._read_headers = AutomagicRTReader(self._doc_schema)
    else:
      self._read_headers = RTReader(self._doc_schema)

  @property
  def doc_schema(self):
    """Returns the DocSchema instance used/created during the reading process."""
    return self._doc_schema

  def __iter__(self):
    return self

  def __next__(self):
    if self._automagic:
      doc_klass = get_or_create_klass(self._read_headers._automagic_count, 'Doc', is_doc=True)
      self._doc_schema = doc_klass.schema()
      self._read_headers._doc_schema = self.doc_schema
    doc = self.read()
    if doc is None:
      raise StopIteration()
    self._doc_schema = doc._dr_rt.copy_to_schema()
    return doc

  def next(self):
    return self.__next__()

  def read(self):
    rt = self._read_headers(self._unpacker)
    if rt is None:
      return
    return self._instantiate(rt)

  def _instantiate(self, rt):
    # Create the Doc instance and RTManager.
    doc = self._doc_schema.defn(**rt.doc.build_kwargs())
    self._create_stores(rt, doc)

    # Read instances.
    self._read_doc_instance(rt, doc)
    self._read_instances(rt, doc)
    doc._dr_rt = rt
    return doc

  def _create_stores(self, rt, doc):
    for rtstore in rt.doc.stores:
      if rtstore.is_lazy():
        continue
      attr = rtstore.defn.name
      store = getattr(doc, attr)
      for i in xrange(rtstore.nelem):
        store.create(**rtstore.klass.build_kwargs())

  def _read_packed(self):
    tmp = io.BytesIO()
    self._unpacker.skip(tmp.write)
    return tmp.getvalue()

  def _process_instance(self, rtschema, doc, instance, obj, store):
    # <instance> ::= { <field_id> : <obj_val> }
    for key, val in six.iteritems(instance):
      rtfield = rtschema.fields[key]
      if rtfield.is_lazy():
        if obj._dr_lazy is None:
          obj._dr_lazy = {}
        obj._dr_lazy[key] = val
      else:
        field = rtfield.defn.defn
        val = field.from_wire(val, rtfield, store, doc)
        setattr(obj, rtfield.defn.name, val)

  def _read_doc_instance(self, rt, doc):
    # read the document instance <doc_instance> ::= <instances_nbytes> <instance>
    self._unpacker.unpack()  # nbytes
    instance = self._unpacker.unpack()
    self._process_instance(rt.doc, doc, instance, doc, None)

  def _read_instances(self, rt, doc):
    # <instances_groups> ::= <instances_group>*
    for rtstore in rt.doc.stores:
      # <instances_group>  ::= <instances_nbytes> <instances>
      nbytes = self._unpacker.unpack()

      if rtstore.is_lazy():
        rtstore.lazy = self._unpacker.read_bytes(nbytes)
      else:
        rtschema = rtstore.klass
        store = getattr(doc, rtstore.defn.name)
        for i, instance in enumerate(self._unpacker.unpack()):
          obj = store[i]
          self._process_instance(rtschema, doc, instance, obj, store)
