# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import argparse
import collections
import inspect

import six

from .exceptions import DependencyException
from .fields_core import Field, Pointer, Pointers, SelfPointer, SelfPointers, Slice
from .meta import Ann, Doc


__all__ = ['AnnSchema', 'DocSchema', 'FieldSchema', 'StoreSchema', 'create_schema']


class ArgparseAction(argparse.Action):
  __slots__ = ('schema',)

  def __init__(self, schema, *args, **kwargs):
    argparse.Action.__init__(self, *args, **kwargs)
    self.schema = schema

  def __call__(self, parser, namespace, values, option_string=None):
    self.schema.serial = values


def argparse_action(self):
  def fn(*args, **kwargs):
    return ArgparseAction(self, *args, **kwargs)
  return fn


class BaseSchema(object):
  __slots__ = ('_name', '_help', '_defn', 'serial')

  def __init__(self, name, help, serial, defn):
    self._name = name
    self._help = '' if help is None else help
    self.serial = name if serial is None else serial
    self._defn = defn

  @property
  def defn(self):
    return self._defn

  @property
  def help(self):
    return self._help

  @property
  def name(self):
    return self._name

  def add_to_argparse(self, parser, prefix):
    arg = prefix + '-' + self.name + '-serial'
    parser.add_argument(arg, action=argparse_action(self), default=self.serial, help=self.help, metavar=self.serial)


class AnnSchema(BaseSchema):
  __slots__ = ('_fields',)

  def __init__(self, name, help, serial, defn):
    super(AnnSchema, self).__init__(name, help, serial, defn)
    self._fields = collections.OrderedDict()

  def __contains__(self, name):
    if not isinstance(name, (six.binary_type, six.text_type)):
      raise TypeError('__contains__ needs a text-like field name')
    return name in self._fields

  def __getitem__(self, name):
    if not isinstance(name, (six.binary_type, six.text_type)):
      raise TypeError('__getitem__ needs a text-like field name')
    return self._fields[name]

  def add_field(self, name, field):
    if not isinstance(field, FieldSchema):
      raise TypeError('argument must be a FieldSchema instance')
    self._fields[name] = field

  def fields(self):
    return six.itervalues(self._fields)

  def add_to_argparse(self, parser, prefix='-'):
    pre = prefix + '-' + self.name
    group = parser.add_argument_group(self.name, self.help)
    group.add_argument(pre + '-serial', action=argparse_action(self), default=self.serial, metavar=self.serial)
    for field in self.fields():
      field.add_to_argparse(group, pre)

  @staticmethod
  def from_klass(klass):
    return AnnSchema(klass._dr_name, klass._dr_help, klass._dr_serial, klass)


class DocSchema(BaseSchema):
  __slots__ = ('_fields', '_klasses', '_stores', '_stores_by_klass')

  def __init__(self, name, help, serial, defn):
    super(DocSchema, self).__init__(name, help, serial, defn)
    self._fields = collections.OrderedDict()
    self._klasses = []
    self._stores = collections.OrderedDict()
    self._stores_by_klass = {}

  def __contains__(self, arg):
    if inspect.isclass(arg) and issubclass(arg, Ann):
      for klass in self._klasses:
        if klass.defn == arg:
          return True
      return False
    elif isinstance(arg, (six.binary_type, six.text_type)):
      return arg in self._fields or arg in self._stores
    else:
      raise TypeError('__contains__ needs a text-like field name or an Ann subclass')

  def __getitem__(self, arg):
    if inspect.isclass(arg) and issubclass(arg, Ann):
      for klass in self._klasses:
        if klass.defn == arg:
          return klass
      raise ValueError('Class {0} was not found'.format(arg))
    elif isinstance(arg, (six.binary_type, six.text_type)):
      if arg in self.fields:
        return self._fields[arg]
      else:
        return self._stores[arg]
    else:
      raise TypeError('__getitem__ needs a text-like field name or an Ann subclass')

  def add_field(self, name, field):
    if not isinstance(field, FieldSchema):
      raise TypeError('argument must be a FieldSchema instance')
    self._fields[name] = field

  def add_klass(self, klass):
    if not isinstance(klass, AnnSchema):
      raise TypeError('argument must be an AnnSchema instance')
    self._klasses.append(klass)

  def add_store(self, name, store):
    if not isinstance(store, StoreSchema):
      raise TypeError('argument must be a StoreSchema instance')
    self._stores[name] = store
    if store.stored_type.defn in self._stores_by_klass:
      self._stores_by_klass[store.stored_type.defn].append(store)
    else:
      self._stores_by_klass[store.stored_type.defn] = [store]

  def has_klass_by_serial(self, serial):
    for klass in self._klasses:
      if klass.serial == serial:
        return True
    return False

  def has_store_by_name(self, name):
    return name in self._stores

  def klass_by_serial(self, serial):
    for klass in self._klasses:
      if klass.serial == serial:
        return klass

  def store_count_by_type(self, klass):
    klasses = self._stores_by_klass.get(klass, [])
    return len(klasses)

  def store_by_name(self, name):
    return self._stores[name]

  def store_by_type(self, klass):
    return self._stores_by_klass[klass][0]

  def fields(self):
    return six.itervalues(self._fields)

  def klasses(self):
    return self._klasses

  def stores(self):
    return six.itervalues(self._stores)

  def add_to_argparse(self, parser, prefix='-'):
    pre = prefix + '-' + self.name
    group = parser.add_argument_group(self.name, self.help)
    group.add_argument(pre + '-serial', action=argparse_action(self), default=self.serial, metavar=self.serial)
    for field in self.fields():
      field.add_to_argparse(group, pre)
    for store in self.stores():
      store.add_to_argparse(group, pre)

    for schema in self._klasses:
      schema.add_to_argparse(parser, prefix)

  @staticmethod
  def from_klass(klass):
    return DocSchema(klass._dr_name, klass._dr_help, klass._dr_serial, klass)


class FieldSchema(BaseSchema):
  __slots__ = ('_is_pointer', '_is_self_pointer', '_is_slice', '_is_collection', '_points_to')

  def __init__(self, name, help, serial, defn, is_pointer, is_self_pointer, is_slice, is_collection, points_to=None):
    super(FieldSchema, self).__init__(name, help, serial, defn)
    self._is_pointer = is_pointer
    self._is_self_pointer = is_self_pointer
    self._is_slice = is_slice
    self._is_collection = is_collection
    self._points_to = points_to  # StoreSchema
    if is_pointer and points_to is None:
      raise ValueError('is_pointer requires points_to to point to an AnnSchema instance')

  def __str__(self):
    return 'FieldSchema(name={!r}, serial={!r})'.format(self._name, self.serial)

  @property
  def is_collection(self):
    return self._is_collection

  @property
  def is_pointer(self):
    return self._is_pointer

  @property
  def is_self_pointer(self):
    return self._is_self_pointer

  @property
  def is_slice(self):
    return self._is_slice

  @property
  def points_to(self):
    return self._points_to


class StoreSchema(BaseSchema):
  __slots__ = ('_stored_type',)

  def __init__(self, name, help, serial, defn, stored_type):
    super(StoreSchema, self).__init__(name, help, serial, defn)
    self._stored_type = stored_type  # AnnSchema

  @property
  def stored_type(self):
    return self._stored_type


def _get_points_to(attr, field, s_doc, stored_klasses):
  if field._klass not in stored_klasses:
    raise DependencyException('Invalid document structure: The class {0} is referenced to by {1} ({2}) but are not stored.'.format(field._klass, attr, field))
  if field.store is None:
    if s_doc.store_count_by_type(field._klass) != 1:
      raise DependencyException('The field {0!r} ({1}) points to class {2} without "store" being set. It is ambiguous not to specify which store.'.format(attr, field, field._klass))
    points_to = s_doc.store_by_type(field._klass)
  else:
    if not s_doc.has_store_by_name(field.store):
      raise DependencyException('The field {0!r} ({1}) has "store" set to {2!r} but this store is unknown.'.format(attr, field, field.store))
    points_to = s_doc.store_by_name(field.store)
    if points_to.stored_type.defn != field._klass:
      raise DependencyException('The field {0!r} ({1}) has "store" set to {2!r} but this store is of a different type.'.format(attr, field, field.store))
  return points_to


def _create_fields(ann_klass, s_ann, s_doc, stored_klasses):
  for attr, field in six.iteritems(ann_klass._dr_fields):
    field.resolve_klasses()
    if isinstance(field, Field):
      s_field = FieldSchema(attr, field.help, field.serial, field, False, False, False, False)
    elif isinstance(field, (Pointer, Pointers)):
      points_to = _get_points_to(attr, field, s_doc, stored_klasses)
      s_field = FieldSchema(attr, field.help, field.serial, field, True, False, False, isinstance(field, Pointers), points_to=points_to)
    elif isinstance(field, (SelfPointer, SelfPointers)):
      s_field = FieldSchema(attr, field.help, field.serial, field, False, True, False, isinstance(field, SelfPointers))
    elif isinstance(field, Slice):
      if not field.is_byteslice():
        points_to = _get_points_to(attr, field, s_doc, stored_klasses)
        s_field = FieldSchema(attr, field.help, field.serial, field, True, False, True, False, points_to=points_to)
      else:
        s_field = FieldSchema(attr, field.help, field.serial, field, False, False, True, False)
    else:
      raise TypeError('Unknown type of field {0}'.format(field))

    s_ann.add_field(attr, s_field)


def create_schema(doc_klass):
  """
  Creates a schema structure for a given Doc subclass.
  """
  if not inspect.isclass(doc_klass):
    raise TypeError('doc_klass should be a class')
  elif not issubclass(doc_klass, Doc):
    raise TypeError('doc_klass should be a Doc subclass')

  stored_klasses = {}  # { Ann : AnnSchema }

  s_doc = DocSchema.from_klass(doc_klass)

  # Construct each of the AnnSchemas.
  for attr, store in six.iteritems(doc_klass._dr_stores):
    store.resolve_klasses()
    klass = store._klass
    if klass not in stored_klasses:
      s_klass = AnnSchema.from_klass(klass)
      s_doc.add_klass(s_klass)
      stored_klasses[klass] = s_klass

  # Construct each of the stores.
  for attr, store in six.iteritems(doc_klass._dr_stores):
    s_store = StoreSchema(attr, store.help, store.serial, store, stored_klasses[store._klass])
    s_doc.add_store(attr, s_store)

  # Construct each of the fields on the document.
  _create_fields(doc_klass, s_doc, s_doc, stored_klasses)

  # Construct each of the stored classes.
  for klass in stored_klasses:
    s_klass = stored_klasses[klass]
    _create_fields(klass, s_klass, s_doc, stored_klasses)

  return s_doc
