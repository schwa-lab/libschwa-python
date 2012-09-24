# vim: set ts=2 et:
import inspect

from .exceptions import DependencyException
from .fields import Field, Pointer, Pointers, SelfPointer, SelfPointers, Slice
from .meta import Ann, Doc


__all__ = ['AnnSchema', 'DocSchema', 'FieldSchema', 'StoreSchema', 'create_schema']


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


class AnnSchema(BaseSchema):
  __slots__ = ('_fields',)

  def __init__(self, name, help, serial, defn):
    super(AnnSchema, self).__init__(name, help, serial, defn)
    self._fields = {}

  def __contains__(self, name):
    if not isinstance(name, (str, unicode)):
      raise TypeError('__contains__ needs a str or unicode field name')
    return name in self._fields

  def __getitem__(self, name):
    if not isinstance(name, (str, unicode)):
      raise TypeError('__getitem__ needs a str or unicode field name')
    return self._fields[name]

  def add_field(self, name, field):
    if not isinstance(field, FieldSchema):
      raise TypeError('argument must be a FieldSchema instance')
    self._fields[name] = field


class DocSchema(BaseSchema):
  __slots__ = ('_fields', '_stores', '_stores_by_klass', 'klasses')

  def __init__(self, name, help, serial, defn):
    super(DocSchema, self).__init__(name, help, serial, defn)
    self._fields = {}
    self._stores = {}
    self._stores_by_klass = {}
    self.klasses = []

  def __contains__(self, arg):
    if inspect.isclass(arg) and issubclass(arg, Ann):
      return arg in self._stores_by_klass
    elif isinstance(arg, (str, unicode)):
      return arg in self._fields or arg in self._stores
    else:
      raise TypeError('__contains__ needs a str or unicode field name or an Ann subclass')

  def __getitem__(self, arg):
    if inspect.isclass(arg) and issubclass(arg, Ann):
      klasses = self._stores_by_klass[arg]
      if len(klasses) == 1:
        return klasses[0]
      else:
        raise ValueError('{0} stores were found of this type'.format(len(klasses)))
    elif isinstance(arg, (str, unicode)):
      if arg in self.fields:
        return self._fields[arg]
      else:
        return self._stores[arg]
    else:
      raise TypeError('__getitem__ needs a str or unicode field name or an Ann subclass')

  def add_field(self, name, field):
    if not isinstance(field, FieldSchema):
      raise TypeError('argument must be a FieldSchema instance')
    self._fields[name] = field

  def add_store(self, name, store):
    if not isinstance(store, StoreSchema):
      raise TypeError('argument must be a StoreSchema instance')
    self._stores[name] = store
    if store.stored_type in self._stores_by_klass:
      self._stores_by_klass[store.stored_type.defn].append(store)
    else:
      self._stores_by_klass[store.stored_type.defn] = [store]

  def has_store_by_name(self, name):
    return name in self._stores

  def store_count_by_type(self, klass):
    klasses = self._stores_by_klass.get(klass, [])
    return len(klasses)

  def store_by_name(self, name):
    return self._stores[name]

  def store_by_type(self, klass):
    return self._stores_by_klass[klass][0]


class FieldSchema(BaseSchema):
  __slots__ = ('_is_pointer', '_is_self_pointer', '_is_slice', '_points_to')

  def __init__(self, name, help, serial, defn, is_pointer, is_self_pointer, is_slice, points_to=None):
    super(FieldSchema, self).__init__(name, help, serial, defn)
    self._is_pointer = is_pointer
    self._is_self_pointer = is_self_pointer
    self._is_slice = is_slice
    self._points_to = points_to  # AnnSchema
    if is_pointer and points_to is None:
      raise ValueError('is_pointer requires points_to to point to an AnnSchema instance')

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
    points_to = s_doc.store_by_type(field._klass).stored_type
  else:
    if not s_doc.has_store_by_name(field.store):
      raise DependencyException('The field {0!r} ({1}) has "store" set to {2!r} but this store is unknown.'.format(attr, field, field.store))
    points_to = s_doc.store_by_name(field.store).stored_type
    if points_to.defn != field._klass:
      raise DependencyException('The field {0!r} ({1}) has "store" set to {2!r} but this store is of a different type.'.format(attr, field, field.store))
  return points_to


def _create_fields(ann_klass, s_ann, s_doc, stored_klasses):
  for attr, field in ann_klass._dr_fields.iteritems():
    field.resolve_klasses()
    if isinstance(field, Field):
      s_field = FieldSchema(attr, field.help, field.serial, field, False, False, False)
    elif isinstance(field, (Pointer, Pointers)):
      points_to = _get_points_to(attr, field, s_doc, stored_klasses)
      s_field = FieldSchema(attr, field.help, field.serial, field, True, False, False, points_to)
    elif isinstance(field, (SelfPointer, SelfPointers)):
      s_field = FieldSchema(attr, field.help, field.serial, field, False, True, False)
    elif isinstance(field, Slice):
      if not field.is_byteslice():
        points_to = _get_points_to(attr, field, s_doc, stored_klasses)
        s_field = FieldSchema(attr, field.help, field.serial, field, True, False, True, points_to)
      else:
        s_field = FieldSchema(attr, field.help, field.serial, field, False, False, True)
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

  s_doc = DocSchema(doc_klass._dr_name, doc_klass._dr_help, doc_klass._dr_serial, doc_klass)

  # construct each of the AnnSchema's
  for attr, store in doc_klass._dr_stores.iteritems():
    store.resolve_klasses()
    klass = store._klass
    if klass not in stored_klasses:
      s_klass = AnnSchema(klass._dr_name, klass._dr_help, klass._dr_serial, klass)
      stored_klasses[klass] = s_klass
      s_doc.klasses.append(s_klass)

  # construct each of the stores
  for attr, store in doc_klass._dr_stores.iteritems():
    s_store = StoreSchema(attr, store.help, store.serial, store, stored_klasses[store._klass])
    s_doc.add_store(attr, s_store)

  # construct each of the fields on the document
  _create_fields(doc_klass, s_doc, s_doc, stored_klasses)

  # construct each of the stored classes
  for klass in stored_klasses:
    s_klass = stored_klasses[klass]
    _create_fields(klass, s_klass, s_doc, stored_klasses)

  return s_doc
