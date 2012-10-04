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

  def create(self, **kwargs):
    obj = self._klass(**kwargs)
    self.append(obj)
    return obj

  def create_n(self, n, **kwargs):
    for i in xrange(n):
      obj = self._klass(**kwargs)
      self.append(obj)
