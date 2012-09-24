# vim: set ts=2 et:
import inspect

from .exceptions import DependencyException
from .fields import Field, Pointer, Pointers, SelfPointer, SelfPointers, Slice
from .meta import Ann, Doc


__all__ = ['AnnSchema', 'DocSchema', 'FieldSchema', 'StoreSchema', 'create']


class BaseSchema(object):
  __slots__ = ('_name', '_help', 'serial')

  def __init__(self, name, help, serial):
    self._name = name
    self._help = '' if help is None else help
    self.serial = name if serial is None else serial

  @property
  def help(self):
    return self._help

  @property
  def name(self):
    return self._name


class AnnSchema(BaseSchema):
  __slots__ = ('_fields',)

  def __init__(self, name, help, serial):
    super(AnnSchema, self).__init__(name, help, serial)
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

  def __init__(self, name, help, serial):
    super(DocSchema, self).__init__(name, help, serial)
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
      self._stores_by_klass[store.stored_type].append(store)
    else:
      self._stores_by_klass[store.stored_type] = [store]

  def store_by_name(self, name):
    return self._stores[name]

  def store_by_type(self, klass):
    return self._stores_by_klass[klass]


class FieldSchema(BaseSchema):
  __slots__ = ('_is_pointer', '_is_self_pointer', '_is_slice', '_points_to')

  def __init__(self, name, help, serial, is_pointer, is_self_pointer, is_slice, points_to=None):
    super(FieldSchema, self).__init__(name, help, serial)
    self._is_pointer = is_pointer
    self._is_self_pointer = is_self_pointer
    self._is_slice = is_slice
    self._points_to = points_to  # AnnSchema

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

  def __init__(self, name, help, serial, stored_type):
    super(StoreSchema, self).__init__(name, help, serial)
    self._stored_type = stored_type  # AnnSchema

  @property
  def stored_type(self):
    return self._stored_type


def _create_fields(ann_klass, s_ann, stored_klasses):
  print ann_klass
  #print s_ann
  #print stored_klasses
  for attr, field in ann_klass._dr_fields.iteritems():
    print field
    field.resolve_klasses()
    if isinstance(field, Field):
      s_field = FieldSchema(attr, field.help, field.serial, False, False, False)
    elif isinstance(field, (Pointer, Pointers)):
      print field
      print field._klass
      if field._klass not in stored_klasses:
        raise DependencyException('Invalid document structure: The class {0} is referenced to by {1} ({2}) but are not stored.'.format(field._klass, attr, field))
      s_field = FieldSchema(attr, field.help, field.serial, True, False, False)
    elif isinstance(field, (SelfPointer, SelfPointers)):
      s_field = FieldSchema(attr, field.help, field.serial, False, True, False)
    elif isinstance(field, Slice):
      if not field.is_byteslice():
        if field._klass not in stored_klasses:
          raise DependencyException('Invalid document structure: The class {0} is referenced to by {1} ({2}) but are not stored.'.format(field._klass, attr, field))
        s_field = FieldSchema(attr, field.help, field.serial, True, False, True)
      else:
        s_field = FieldSchema(attr, field.help, field.serial, False, False, True)
    else:
      raise TypeError('Unknown type of field {0}'.format(field))

    s_ann.add_field(attr, s_field)


def create(doc_klass):
  """
  Creates a schema structure for a given Doc subclass.
  """
  if not inspect.isclass(doc_klass):
    raise TypeError('doc_klass should be a class')
  elif not issubclass(doc_klass, Doc):
    raise TypeError('doc_klass should be a Doc subclass')

  stored_klasses = set()

  s_doc = DocSchema(doc_klass._dr_name, doc_klass._dr_help, doc_klass._dr_serial)

  # construct each of the stores
  for attr, store in doc_klass._dr_stores.iteritems():
    store.resolve_klasses()
    stored_klasses.add(store._klass)
    s_store = StoreSchema(attr, store.help, store.serial, store._klass)
    s_doc.add_store(attr, s_store)

  # construct each of the fields on the document
  _create_fields(doc_klass, s_doc, stored_klasses)

  # construct each of the stored classes
  for klass in stored_klasses:
    s_klass = AnnSchema(klass._dr_name, klass._dr_help, klass._dr_serial)
    s_doc.klasses.append(s_klass)
    _create_fields(klass, s_klass, stored_klasses)

  return s_doc
