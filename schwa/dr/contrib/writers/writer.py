# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import abc

import six

__all__ = ['AbstractWriter']


@six.add_metaclass(abc.ABCMeta)
class AbstractWriter(object):
  @abc.abstractmethod
  def write(self, doc):
    raise NotImplementedError
