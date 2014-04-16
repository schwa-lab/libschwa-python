# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import inspect

import msgpack

from .constants import FieldType
from .exceptions import WriterException
from .runtime import build_rt, merge_rt
from .meta import Doc
from .schema import DocSchema

__all__ = ['Writer']


class Writer(object):
  __slots__ = ('_ostream', '_packer', '_doc_schema')

  WIRE_VERSION = 2  # Version of the wire protocol the reader knows how to process.

  def __init__(self, ostream, doc_schema_or_doc):
    """
    @param ostream A file-like object to write to
    @param doc_schema_or_doc A DocSchema instance or a Doc subclass. If a Doc subclass is provided, the .schema() method is called to create the DocSchema instance.
    """
    if not hasattr(ostream, 'write'):
      raise TypeError('ostream must have a write attr')
    self._ostream = ostream
    if isinstance(doc_schema_or_doc, DocSchema):
      self._doc_schema = doc_schema_or_doc
    elif inspect.isclass(doc_schema_or_doc) and issubclass(doc_schema_or_doc, Doc):
      self._doc_schema = doc_schema_or_doc.schema()
    else:
      raise TypeError('Invalid value for doc_schema_or_doc. Must be either a DocSchema instance or a Doc subclass')
    self._packer = msgpack.Packer()

  @property
  def doc_schema(self):
    """Returns the DocSchema instance used/created during the writing process."""
    return self._doc_schema

  def write(self, doc):
    """
    Writes a Doc instance to the stream.
    @param doc the Doc instance to write to the stream.
    """
    if not isinstance(doc, Doc):
      raise ValueError('You can only stream instances of Doc')

    # Get or construct the RTManager for the document.
    if doc._dr_rt is None:
      rt = doc._dr_rt = build_rt(self._doc_schema)
    else:
      rt = doc._dr_rt = merge_rt(doc._dr_rt, self._doc_schema)

    # Update the _dr_index values.
    self._index_stores(doc, rt)

    # Write wire version.
    self._pack(Writer.WIRE_VERSION)

    # Write headers.
    self._pack(self._build_klasses(doc, rt))
    self._pack(self._build_stores(doc, rt))

    # Write instances.
    self._write_doc_instance(doc, rt)
    self._write_instances(doc, rt)

  def _pack(self, value):
    packed = self._packer.pack(value)
    self._ostream.write(packed)

  def _write_prefixed(self, packed):
    self._pack(len(packed))
    self._ostream.write(packed)

  def _pack_prefixed(self, value):
     self._write_prefixed(self._packer.pack(value))

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
        field[FieldType.NAME] = f.serial if f.is_lazy() else f.defn.serial
        # <field_type> ::= 1 # POINTER_TO => the <store_id> that this field points into
        if f.is_pointer:
          field[FieldType.POINTER_TO] = f.points_to.store_id
        # <field_type> ::= 2 # IS_SLICE => whether or not this field is a "Slice" field
        if f.is_slice:
          field[FieldType.IS_SLICE] = None
        # <field_type>  ::= 3 # IS_SELF_POINTER => whether or not this field is a self-pointer
        if f.is_self_pointer:
          field[FieldType.IS_SELF_POINTER] = None
        # <field_type>  ::= 4 # IS_COLLECTION => whether or not this field is a collection
        if f.is_collection:
          field[FieldType.IS_COLLECTION] = None

      # Work out the serial name for the class.
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
      # <store> ::= ( <store_name>, <type_id>, <store_nelem> )
      store_name = s.serial if s.is_lazy() else s.defn.serial
      klass_id = s.klass.klass_id
      nelem = s.nelem if s.is_lazy() else len(getattr(doc, s.defn.name))
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
      if field.should_write(val):
        try:
          wire_val = field.to_wire(val, f, store, doc)
        except Exception as e:
          raise WriterException('An exception occurred while writing field "{0}" of "{1}": {2}'.format(f.defn.name, rtschema.defn.name, e))
        instance[f.field_id] = wire_val
    return instance

  def _write_doc_instance(self, doc, rt):
    self._pack_prefixed(self._build_instance(doc, None, doc, rt.doc))

  def _write_instances(self, doc, rt):
    for rtstore in rt.doc.stores:
      if rtstore.is_lazy():
        self._write_prefixed(rtstore.lazy)
      else:
        rtschema = rtstore.klass
        store = getattr(doc, rtstore.defn.name)
        instances = [self._build_instance(obj, store, doc, rtschema) for obj in store]
        self._pack_prefixed(instances)
