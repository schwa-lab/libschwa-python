# vim: set ts=2 et:
import inspect

import msgpack

from .constants import FIELD_TYPE_NAME, FIELD_TYPE_POINTER_TO, FIELD_TYPE_IS_SLICE, FIELD_TYPE_IS_SELF_POINTER
from .exceptions import WriterException
from .runtime import build_rt, merge_rt
from .meta import Doc
from .schema import DocSchema

__all__ = ['Writer']


class Writer(object):
  __slots__ = ('_ostream', '_packer', '_doc_schema')

  WIRE_VERSION = 2  # version of the wire protocol the reader knows how to process

  def __init__(self, ostream, arg):
    if not hasattr(ostream, 'write'):
      raise TypeError('ostream must have a write attr')
    self._ostream = ostream
    if isinstance(arg, DocSchema):
      self._doc_schema = arg
    elif inspect.isclass(arg) and issubclass(arg, Doc):
      self._doc_schema = arg.schema()
    else:
      raise TypeError('Invalid value for arg. Must be either a DocSchema instance or a Doc subclass')
    self._packer = msgpack.Packer()

  def write(self, doc):
    if not isinstance(doc, Doc):
      raise ValueError('You can only stream instances of Doc')

    # get or construct the RTManager for the document
    if doc._dr_rt is None:
      rt = doc._dr_rt = build_rt(self._doc_schema)
    else:
      rt = doc._dr_rt = merge_rt(doc._dr_rt, self._doc_schema)

    # update the _dr_index values
    self._index_stores(doc, rt)

    # write wire version
    self._pack(Writer.WIRE_VERSION)

    # write headers
    self._pack(self._build_klasses(doc, rt))
    self._pack(self._build_stores(doc, rt))

    # write instances
    self._write_doc_instance(doc, rt)
    self._write_instances(doc, rt)

  def _pack(self, value):
    packed = self._packer.pack(value)
    self._ostream.write(packed)

  def _pack_prefixed(self, value):
    packed = self._packer.pack(value)
    self._pack(len(packed))
    self._ostream.write(packed)

  def _index_stores(self, doc, rt):
    """Set _dr_index on each of the objects in the stores."""
    for s in rt.doc.stores:
      if not s.is_lazy():
        store = getattr(doc, s.defn.name)
        for i, obj in enumerate(store):
          if obj is None:
            raise WriterException('Index {0} on store {1} is None'.format(i, s.defn))
          obj._dr_index = i

  def _build_klasses(self, doc, rt):
    # <klasses> ::= [ <klass> ]
    klasses = []

    for klass in rt.klasses:
      # <fields> ::= [ <field> ]
      fields = []
      for f in klass.fields:
        # <field> ::= { <field_type> : <field_val> }
        field = {}
        fields.append(field)
        # <field_type> ::= 0 # NAME => the name of the field
        field[FIELD_TYPE_NAME] = f.serial if f.is_lazy() else f.defn.serial
        # <field_type> ::= 1 # POINTER_TO => the <store_id> that this field points into
        if f.is_pointer:
          field[FIELD_TYPE_POINTER_TO] = f.points_to.store_id
        # <field_type> ::= 2 # IS_SLICE => whether or not this field is a "Slice" field
        if f.is_slice:
          field[FIELD_TYPE_IS_SLICE] = None
        # <field_type>  ::= 3 # IS_SELF_POINTER => whether or not this field is a self-pointer
        if f.is_self_pointer:
          field[FIELD_TYPE_IS_SELF_POINTER] = None

      # work out the serial name for the class
      if klass is rt.doc:
        klass_name = '__meta__'
      elif klass.is_lazy():
        klass_name = klass.serial
      else:
        klass_name = klass.defn.serial

      # <klass> ::= ( <klass_name>, <fields> )
      klass = (klass_name, fields)
      klasses.append(klass)

    return klasses

  def _build_stores(self, doc, rt):
    # <stores> ::= [ <store> ]
    stores = []

    for s in rt.doc.stores:
      # // <store> ::= ( <store_name>, <type_id>, <store_nelem> )
      store_name = s.serial if s.is_lazy() else s.defn.serial
      klass_id = s.klass.klass_id
      nelem = len(s.lazy) if s.is_lazy() else len(getattr(doc, s.defn.name))
      store = (store_name, klass_id, nelem)
      stores.append(store)

    return stores

  def _build_instance(self, obj, store, doc, rtschema):
    instance = {}
    if obj._dr_lazy is not None:
      instance.update(obj._dr_lazy)
    for f in rtschema.fields:
      if f.is_lazy():
        continue
      field = f.defn.defn
      val = getattr(obj, f.defn.name)
      val = field.to_wire(val, f, store, doc)
      if val is None:
        continue
      instance[f.field_id] = val
    return instance

  def _write_doc_instance(self, doc, rt):
    self._pack_prefixed(self._build_instance(doc, None, doc, rt.doc))

  def _write_instances(self, doc, rt):
    for rtstore in rt.doc.stores:
      if rtstore.is_lazy():
        self._pack_prefixed(rtstore.lazy)
      else:
        rtschema = rtstore.klass
        store = getattr(doc, rtstore.defn.name)
        instances = [self._build_instance(obj, store, doc, rtschema) for obj in store]
        self._pack_prefixed(instances)
