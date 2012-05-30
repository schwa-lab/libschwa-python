# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 et:

from abc import ABCMeta, abstractmethod

class AbstractWriter(object):
  __metaclass__ = ABCMeta
  @abstractmethod
  def write(self, doc):
    raise NotImplementedError
