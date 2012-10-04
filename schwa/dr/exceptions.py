# vim: set ts=2 et:
__all__ = ['DependencyException', 'ReaderException', 'WriterException']


class DependencyException(Exception):
  pass


class ReaderException(Exception):
  pass


class WriterException(Exception):
  pass
