# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
"""
Utilities for managing document decoration by marking the document with the set of decorations that have been applied to it.
"""
from __future__ import absolute_import, print_function, unicode_literals
import collections
import functools

import six

__all__ = ['Decorator', 'decorator', 'method_requires_decoration', 'requires_decoration']


def decorator(key=None):
  """
  Wraps a docrep decorator, ensuring it is only executed once per document.
  Duplication is checked using the given key or the function object.
  """
  def dec(fn):
    @functools.wraps(fn)
    def wrapper(doc, check=True, mark=True):
      if not hasattr(doc, '_dr_decorated_by'):
        doc._dr_decorated_by = {}
      if check and key in doc._dr_decorated_by:
        return
      if mark:
        doc._dr_decorated_by[key] = wrapper
      fn(doc)
    wrapper.reapply = functools.partial(wrapper, check=False)
    return wrapper
  if callable(key):
    return dec(key)
  return dec


class Decorator(object):
  """
  An abstract document decorator, which wraps its decorate method to ensure it is only executed once per document.
  """

  def __init__(self, key):
    # NOTE: wrapping __call__ like this didn't seem to work
    self.decorate = decorator(key)(self.decorate)
    self._key = key

  @classmethod
  def _build_key(cls, *args):
    return '{0}-{1}'.format(cls.__name__, '-'.join(repr(arg) for arg in args))

  def _set_affected_fields(self, *args):
    """
    Stores a list of fields affected (i.e. set) for this decorator, aiding in reflexion and undo operations.

    Elements of args should be (store, field) pairs, or just an attr string for attributes of the document set by the decorator.

    Where store, field or attr are not strings or None for any of the args, affected fields will not be stored.
    """
    field_map = collections.defaultdict(set)
    for field in args:
      if isinstance(field, (six.binary_type, six.text_type)):
        field_map[None].add(field)
      elif field is None:
        pass
      else:
        try:
          store, field = field
        except TypeError:
          return
        if isinstance(store, (six.binary_type, six.text_type)) and isinstance(field, (six.binary_type, six.text_type)):
          field_map[store].add(field)
        elif store is not None and field is not None:
          # Not strings or None.
          return
    self._affected_fields = dict(field_map)

  def __call__(self, doc):
    self.decorate(doc)

  def reapply(self, doc):
    """Apply the decorator without checking if it has been previously applied to this document."""
    return self.decorate.reapply(doc)

  @staticmethod
  def _clear_fields(obj, fields):
    for field in fields:
      try:
        delattr(obj, field)
      except AttributeError:
        pass

  def undo(self, doc, unmark=True):
    """Where possible, unset the fields set by this decorator (and any other values in those fields), and allow it to be decorated again."""
    try:
      field_map = self._affected_fields
    except AttributeError:
      raise NotImplementedError('The affected fields are unknown for decorator %r' % self)

    for store, fields in six.iteritems(field_map):
      if store is None:
        self._clear_fields(doc, fields)
      else:
        for obj in getattr(doc, store, ()):
          self._clear_fields(obj, fields)

    if unmark:
      try:
        del doc._dr_decorated_by[self._key]
      except KeyError:
        pass

  def decorate(self, doc):
    raise NotImplementedError()

  def __str__(self):
    return self._key


def _flatten(seq):
  res = []
  for el in seq:
    if hasattr(el, '__iter__'):
      res.extend(_flatten(el))
    else:
      res.append(el)
  return res


def requires_decoration(*decorators, **kwargs):
  """
  Marks the document decoration dependencies for a function, where the
  document is found in the doc_arg positional argument (default 0) or
  doc_kwarg keyword argument (default 'doc').
  """
  doc_arg = kwargs.pop('doc_arg', 0)
  doc_kwarg = kwargs.pop('doc_kwarg', 'doc')
  if kwargs:
    raise ValueError("Got unexpected keyword arguments: {}".format(kwargs.keys()))

  decorators = list(_flatten(decorators))

  def dec(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
      try:
        doc = args[doc_arg]
      except IndexError:
        doc = kwargs[doc_kwarg]

      for decorate in decorators:
        decorate(doc)
      return fn(*args, **kwargs)
    return wrapper
  return dec


method_requires_decoration = functools.partial(requires_decoration, doc_arg=1)
