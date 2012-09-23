# vim: set ts=2 et:
from .collections import StoreList

__all__ = ['BaseAttr', 'BaseField', 'Field', 'Pointer', 'Pointers', 'SelfPointer', 'SelfPointers', 'Slice', 'Store']


class BaseAttr(object):
  __slots__ = ('serial', 'help')

  def __init__(self, serial=None, help=None):
    self.serial = serial
    self.help = help

  def default(self):
    """Returns the default value for this type when it is instantiated."""
    raise NotImplementedError


# =============================================================================
# =============================================================================
class BaseField(BaseAttr):
  pass


class Field(BaseField):
  def default(self):
    return None


class Pointer(BaseField):
  __slots__ = ('_klass', '_klass_name', 'is_collection', 'is_self_pointer', 'store')

  def __init__(self, klass, store=None, serial=None, help=None):
    super(Pointer, self).__init__(serial=serial, help=help)
    if isinstance(klass, (str, unicode)):
      self._klass_name = klass.encode('utf-8')
      self._klass = None
    elif issubclass(klass, Ann):
      self._klass_name = None
      self._klass = klass
    else:
      raise ValueError('Unknown first argument {0!r}.'.format(klass))
    self.store = store
    self.is_collection = False
    self.is_self_pointer = False

  def default(self):
    return None

  def __repr__(self):
    return '{0}({1}, store={2}, is_collection={3}, is_self_pointer={4})'.format(self.__class__.__name__, self._klass or self._klass_name, self.store, self.is_collection, self.is_self_pointer)


class Pointers(Pointer):
  def __init__(self, klass, store=None, serial=None, help=None):
    super(Pointers, self).__init__(klass, store=store, serial=serial, help=help)
    self.is_collection = True

  def default(self):
    return []


class SelfPointer(Pointer):
  def __init__(self, klass, serial=None, help=None):
    super(SelfPointer, self).__init__(klass, serial=serial, help=help)
    self.is_self_pointer = True


class SelfPointers(Pointer):
  def __init__(self, klass, serial=None, help=None):
    super(SelfPointers, self).__init__(klass, serial=serial, help=help)
    self.is_collection = True

  def default(self):
    return []


class Slice(BaseField):
  __slots__ = ('_klass', '_klass_name', 'store')

  def __init__(self, klass=None, store=None, serial=None, help=None):
    super(Slice, self).__init__(serial=serial, help=help)
    if klass is None:
      self._klass_name = None
      self._klass = None
    elif isinstance(klass, (str, unicode)):
      self._klass_name = klass.encode('utf-8')
      self._klass = None
    elif issubclass(klass, Ann):
      self._klass_name = None
      self._klass = klass
    else:
      raise ValueError('Unknown first argument {0!r}.'.format(klass))
    self.store = store

  def default(self):
    return None


# =============================================================================
# =============================================================================
class Store(BaseAttr):
  """
  A Store houses Annotation instances. For an Annotation to be serialised, it needs
  to be placed into a Store.
  """
  __slots__ = ('_klass', '_klass_name')

  def __init__(self, klass, serial=None, help=None):
    super(Store, self).__init__(serial=serial, help=help)
    if isinstance(klass, (str, unicode)):
      self._klass_name = klass.encode('utf-8')
      self._klass = None
    elif issubclass(klass, Ann):
      self._klass_name = None
      self._klass = klass
    else:
      raise ValueError('Unknown first argument {0!r}.'.format(klass))

  def default(self):
    assert self._klass is not None
    return StoreList(self._klass)
