# vim: set ts=2 et:
__all__ = ['StoreList']


class StoreList(list):
  __slots__ = ('_klass', )

  def __init__(self, klass, *args, **kwargs):
    super(StoreList, self).__init__(*args, **kwargs)
    self._klass = klass

  def __repr__(self):
    r = super(StoreList, self).__repr__()
    return 'StoreList({0})'.format(r)

  def clear(self):
    del self[:]

  def create(self, **kwargs):
    """Instantiate, append and return an object of this store's klass"""
    obj = self._klass(**kwargs)
    self.append(obj)
    return obj

  def create_n(self, n, **kwargs):
    """Instantiate and append n objects of this store's klass, returning the corresponding slice"""
    for i in xrange(n):
      obj = self._klass(**kwargs)
      self.append(obj)
    return slice(len(self) - n, len(self))
