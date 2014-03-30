# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

__all__ = ['FieldType']


class FieldType(object):
  __slots__ = ()

  NAME = 0
  POINTER_TO = 1
  IS_SLICE = 2
  IS_SELF_POINTER = 3
  IS_COLLECTION = 4
