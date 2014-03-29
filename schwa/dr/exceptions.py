# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

__all__ = ['DependencyException', 'ReaderException', 'WriterException']


class DependencyException(Exception):
  pass


class ReaderException(Exception):
  pass


class WriterException(Exception):
  pass
