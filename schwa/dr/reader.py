# vim: set ts=2 et:
import inspect

import msgpack

from .constants import FIELD_TYPE_NAME, FIELD_TYPE_POINTER_TO, FIELD_TYPE_IS_SLICE, FIELD_TYPE_IS_SELF_POINTER
from .exceptions import ReaderException
from .runtime import RTField, RTStore, RTAnn, RTManager
from .meta import Doc
from .schema import DocSchema

__all__ = ['Reader']


class Reader(object):
  __slots__ = ('_doc', '_doc_schema', '_unpacker')

  WIRE_VERSION = 2  # version of the wire protocol the reader knows how to process

  def __init__(self, istream, arg):
    if isinstance(arg, DocSchema):
      self._doc_schema = arg
    elif inspect.isclass(arg) and issubclass(arg, Doc):
      self._doc_schema = arg.schema()
    else:
      raise TypeError('Invalid value for arg. Must be either a DocSchema instance or a Doc subclass')
    self._doc = None
    self._unpacker = msgpack.Unpacker(istream)

  def __iter__(self):
    return self

  def next(self):
    self._read_doc()
    if self._doc is None:
      raise StopIteration()
    return self._doc

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

    # read instances
    self._read_doc_instance()
    self._read_instances()

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
        store = getattr(self._doc, defn.name)
        store.create_n(nelem)
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
            field_type = field.defn.points_to.stored_type
            store_type = rtstore.defn.stored_type
            if field_type != store_type:
              raise ReaderException('field points at {0} but store contains {1}'.format(field_type, store_type))

          # backfill
          field.points_to = rtstore

  def _process_instance(self, rtschema, instance, obj, store):
    # <instance> ::= { <field_id> : <obj_val> }
    for key, val in instance.iteritems():
      rtfield = rtschema.fields[key]
      if rtfield.is_lazy():
        if obj._dr_lazy is None:
          obj._dr_lazy = {}
        obj._dr_lazy[key] = val
      else:
        field = rtfield.defn.defn
        val = field.from_wire(val, rtfield, store, self._doc)
        setattr(obj, rtfield.defn.name, val)

  def _read_doc_instance(self):
    # read the document instance <doc_instance> ::= <instances_nbytes> <instance>
    self._unpacker.unpack()  # nbytes
    instance = self._unpacker.unpack()
    self._process_instance(self._doc._dr_rt.doc, instance, self._doc, None)

  def _read_instances(self):
    # <instances_groups> ::= <instances_group>*
    for rtstore in self._doc._dr_rt.doc.stores:
      # <instances_group>  ::= <instances_nbytes> <instances>
      self._unpacker.unpack()  # nbytes
      instances = self._unpacker.unpack()

      if rtstore.is_lazy():
        rtstore.lazy = instances
      else:
        rtschema = rtstore.klass
        store = getattr(self._doc, rtstore.defn.name)
        for i, instance in enumerate(instances):
          obj = store[i]
          self._process_instance(rtschema, instance, obj, store)
