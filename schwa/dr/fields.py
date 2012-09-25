# vim: set ts=2 et:
from .collections import StoreList
from .exceptions import DependencyException

__all__ = ['BaseAttr', 'BaseField', 'Field', 'Pointer', 'Pointers', 'SelfPointer', 'SelfPointers', 'Slice', 'Store']


def from_wire_pointer(val, store):
  if val is None:
    return None
  return store[val]


def to_wire_pointer(obj, store):
  if obj is None:
    return None
  if not hasattr(obj, '_dr_index'):
    raise ValueError('Cannot serialize a pointer which is not in a store ({0}).'.format(obj))
  assert store[obj._dr_index] is obj
  return obj._dr_index


def from_wire_pointers(vals, store):
  if not vals:
    return None
  return [store[i] for i in vals]


def to_wire_pointers(objs, store):
  if not objs:
    return None
  indices = []
  for obj in objs:
    if not hasattr(obj, '_dr_index'):
      raise ValueError('Cannot serialize a pointer which is not in a store ({0}).'.format(obj))
    assert store[obj._dr_index] is obj
    indices.append(obj._dr_index)
  return indices


# =============================================================================
# =============================================================================
class BaseAttr(object):
  __slots__ = ('serial', 'help')

  def __init__(self, serial=None, help=None):
    self.serial = serial
    self.help = help

  def default(self):
    """
    Returns the default value for this type when it is instantiated.
    """
    raise NotImplementedError

  def resolve_klasses(self):
    if self._klass is None and self._klass_name is not None:
      from .meta import Meta
      if self._klass_name not in Meta.registered:
        raise DependencyException('klass_name {0!r} is not a registered Ann subclass name'.format(self._klass_name))
      self._klass = Meta.registered[self._klass_name]


# =============================================================================
# =============================================================================
class BaseField(BaseAttr):
  def from_wire(self, val, rtfield, cur_store, doc):
    """
    Deserialization hook for converting msgpack values into Python values
    specific to this field type.
    @param val the value return from msgpack unpacking
    @param rtfield the RTField instance for the current field
    @param cur_store the Store instance that the value is from
    @param doc the current Doc instance
    """
    raise NotImplementedError

  def to_wire(self, obj, rtfield, cur_store, doc):
    """
    Serialization hook for converting Python values into msgpack values
    specific to this field type.
    @param val the value return from msgpack unpacking
    @param rtfield the RTField instance for the current field
    @param cur_store the Store instance that the value is from
    @param doc the current Doc instance
    """
    raise NotImplementedError


class Field(BaseField):
  def default(self):
    return None

  def from_wire(self, val, rtfield, cur_store, doc):
    return val

  def to_wire(self, obj, rtfield, cur_store, doc):
    if isinstance(obj, unicode):
      obj = obj.encode('utf-8')
    return obj

  def resolve_klasses(self):
    pass


class Pointer(BaseField):
  __slots__ = ('_klass', '_klass_name', 'is_collection', 'store')

  def __init__(self, klass, store=None, serial=None, help=None):
    from .meta import Ann
    super(Pointer, self).__init__(serial=serial, help=help)
    if isinstance(klass, (str, unicode)):
      self._klass_name = klass
      self._klass = None
    elif issubclass(klass, Ann):
      self._klass_name = None
      self._klass = klass
    else:
      raise ValueError('Unknown first argument {0!r}.'.format(klass))
    self.store = store
    self.is_collection = False

  def __repr__(self):
    return '{0}({1}, store={2}, is_collection={3})'.format(self.__class__.__name__, self._klass or self._klass_name, self.store, self.is_collection)

  def default(self):
    return None

  def from_wire(self, val, rtfield, cur_store, doc):
    return from_wire_pointer(val, getattr(doc, rtfield.points_to.defn.name))

  def to_wire(self, obj, rtfield, cur_store, doc):
    return to_wire_pointer(obj, getattr(doc, rtfield.points_to.defn.name))


class Pointers(Pointer):
  def __init__(self, klass, store=None, serial=None, help=None):
    super(Pointers, self).__init__(klass, store=store, serial=serial, help=help)
    self.is_collection = True

  def default(self):
    return []

  def from_wire(self, vals, rtfield, cur_store, doc):
    return from_wire_pointers(vals, getattr(doc, rtfield.points_to.defn.name))

  def to_wire(self, objs, rtfield, cur_store, doc):
    return to_wire_pointers(objs, getattr(doc, rtfield.points_to.defn.name))


class SelfPointer(BaseField):
  __slots__ = ('is_collection',)

  def __init__(self, serial=None, help=None):
    super(SelfPointer, self).__init__(serial=serial, help=help)
    self.is_collection = False

  def default(self):
    return None

  def resolve_klasses(self):
    pass

  def from_wire(self, val, rtfield, cur_store, doc):
    return from_wire_pointer(val, cur_store)

  def to_wire(self, obj, rtfield, cur_store, doc):
    return to_wire_pointer(obj, cur_store)


class SelfPointers(SelfPointer):
  def __init__(self, serial=None, help=None):
    super(SelfPointers, self).__init__(serial=serial, help=help)
    self.is_collection = True

  def default(self):
    return []

  def from_wire(self, vals, rtfield, cur_store, doc):
    return from_wire_pointers(vals, cur_store)

  def to_wire(self, objs, rtfield, cur_store, doc):
    return to_wire_pointers(objs, cur_store)


class Slice(BaseField):
  __slots__ = ('_klass', '_klass_name', 'store')

  def __init__(self, klass=None, store=None, serial=None, help=None):
    from .meta import Ann
    super(Slice, self).__init__(serial=serial, help=help)
    if klass is None:
      self._klass_name = None
      self._klass = None
    elif isinstance(klass, (str, unicode)):
      self._klass_name = klass
      self._klass = None
    elif issubclass(klass, Ann):
      self._klass_name = None
      self._klass = klass
    else:
      raise ValueError('Unknown first argument {0!r}.'.format(klass))
    self.store = store

  def default(self):
    return None

  def is_byteslice(self):
    return self._klass is None and self._klass_name is None

  def resolve_klasses(self):
    if not self.is_byteslice():
      super(Slice, self).resolve_klasses()

  def from_wire(self, val, rtfield, cur_store, doc):
    if val is None:
      return None
    return slice(val[0], val[1])

  def to_wire(self, obj, rtfield, cur_store, doc):
    if obj is None:
      return None
    return (obj.start, obj.stop)


# =============================================================================
# =============================================================================
class Store(BaseAttr):
  """
  A Store houses Annotation instances. For an Annotation to be serialised, it needs
  to be placed into a Store.
  """
  __slots__ = ('_klass', '_klass_name')

  def __init__(self, klass, serial=None, help=None):
    from .meta import Ann
    super(Store, self).__init__(serial=serial, help=help)
    if isinstance(klass, (str, unicode)):
      self._klass_name = klass
      self._klass = None
    elif issubclass(klass, Ann):
      self._klass_name = None
      self._klass = klass
    else:
      raise ValueError('Unknown first argument {0!r}.'.format(klass))

  def default(self):
    assert self._klass is not None
    return StoreList(self._klass)
