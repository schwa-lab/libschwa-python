# vim: set ts=2 et:
__all__ = ['FieldType']


class FieldType(object):
  __slots__ = ('NAME', 'POINTER_TO', 'IS_SLICE', 'IS_SELF_POINTER', 'IS_COLLECTION')

  NAME = 0
  POINTER_TO = 1
  IS_SLICE = 2
  IS_SELF_POINTER = 3
  IS_COLLECTION = 4
