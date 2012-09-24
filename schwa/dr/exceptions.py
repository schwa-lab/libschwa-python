# vim: set ts=2 et:
__all__ = ['DependencyException', 'ReaderException', 'StoreException']


class DependencyException(Exception):
  pass


class ReaderException(Exception):
  pass


class StoreException(Exception):
  pass
