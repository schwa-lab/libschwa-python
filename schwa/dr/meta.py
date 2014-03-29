# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import collections

import six

from .containers import StoreList
from .exceptions import DependencyException
from .fields_core import BaseField, Store

__all__ = ['Ann', 'Doc', 'MetaBase', 'make_ann']


class MetaBase(type):
  _registered = {}  # { _dr_name : klass }

  def __new__(mklass, klass_name, bases, attrs):
    # Sanity check the base classes.
    is_here = has_ann_base = has_doc_base = False
    for base in bases:
      if attrs.get('__module__') == MetaBase.__module__:
        is_here = True
      else:
        if issubclass(base, Ann):
          has_ann_base = True
        elif issubclass(base, Doc):
          has_doc_base = True
    if not is_here:
      if has_ann_base and has_doc_base:
        raise ValueError('Class {0!r} cannot have both Ann and Doc as a base class'.format(klass_name))
      elif not (has_ann_base or has_doc_base):
        raise ValueError('Class {0!r} must have either Ann or Doc as a base class'.format(klass_name))

    # Discover the Field and Store instances.
    fields, stores = {}, {}
    for base in bases:
      fields.update(getattr(base, '_dr_fields', {}))
      stores.update(getattr(base, '_dr_stores', {}))
    for name, attr in six.iteritems(attrs):
      if isinstance(name, six.binary_type):
        name = name.decode('utf-8')
      if isinstance(attr, Store):
        # die if a Store is placed on an Ann
        if has_ann_base:
          raise ValueError('Class {0!r} cannot house a Store ({1!r}) as it is not a Doc subclass'.format(klass_name, name))
        stores[name] = attr
      elif isinstance(attr, BaseField):
        fields[name] = attr

    # Construct __slots__.
    if not is_here:
      if '__slots__' in attrs:
        slots = list(attrs['__slots__']) + list(fields) + list(stores)
        attrs['__slots__'] = tuple(slots)

      # Remove the Store and BaseField objects from the set of class attributes so that they can be overwritten by instances of the class.
      for key in fields:
        if key in attrs:
          del attrs[key]
      for key in stores:
        if key in attrs:
          del attrs[key]

    # Construct the class.
    klass = super(MetaBase, mklass).__new__(mklass, klass_name, bases, attrs)

    # Adds the Field and Store information appropriately.
    klass._dr_fields = collections.OrderedDict()  # { attr : Field }
    for key in sorted(fields):
      klass._dr_fields[key] = fields[key]
    klass._dr_stores = collections.OrderedDict()  # { attr : Store }
    for key in sorted(stores):
      klass._dr_stores[key] = stores[key]

    # Add the name.
    meta = attrs.get('Meta', None)
    if hasattr(meta, 'name'):
      klass._dr_name = meta.name
    else:
      module = ''
      if '.' not in klass_name and klass.__module__ != '__main__':
        module = klass.__module__ + '.'
      klass._dr_name = module + klass_name
    if hasattr(meta, 'serial'):
      klass._dr_serial = meta.serial
    else:
      klass._dr_serial = klass_name
    if hasattr(meta, 'help'):
      klass._dr_help = meta.help
    else:
      klass._dr_help = ''

    # _dr_name and _dr_serial are stored as Unicode.
    if isinstance(klass._dr_name, six.binary_type):
      klass._dr_name = klass._dr_name.decode('utf-8')
    if isinstance(klass._dr_serial, six.binary_type):
      klass._dr_serial = klass._dr_serial.decode('utf-8')

    # Ensure _dr_name's are unique.
    if klass._dr_name in MetaBase._registered:
      raise ValueError('The name {0!r} has already been registered by another class ({1})'.format(klass._dr_name, MetaBase._registered[klass._dr_name]))
    MetaBase._registered[klass._dr_name] = klass

    # Construct the docstring for the class.
    MetaBase.add_docstring(klass)

    return klass

  @staticmethod
  def add_docstring(klass):
    doc = six.StringIO()
    write_doc = False
    if klass.__doc__:
      doc.write(klass.__doc__ + '\n')
      write_doc = True
    doc.write('docrep members for this class:\n')
    for name, field in sorted(klass._dr_fields.items()):
      doc.write('* ')
      doc.write(name)
      if field.help:
        doc.write(': ')
        doc.write(field.help)
        write_doc = True
      doc.write('\n')
    if write_doc:
      klass.__doc__ = doc.getvalue()

  @staticmethod
  def find_klass(klass_name):
    if klass_name not in MetaBase._registered:
      suggestions = []
      for name in MetaBase._registered:
        if name.endswith('.' + klass_name):
          suggestions.append(name)
      suggestion = ''
      if len(suggestions) == 1:
        suggestion = ' Perhaps you meant {0!r} instead?'.format(suggestions[0])
      raise DependencyException('klass_name {0!r} is not a registered Ann subclass name.{1}'.format(klass_name, suggestion))
    return MetaBase._registered[klass_name]


@six.add_metaclass(MetaBase)
class Base(object):
  __slots__ = ('_dr_lazy', )

  def __init__(self, **kwargs):
    for name, field in six.iteritems(self._dr_fields):
      setattr(self, name, field.default())
    for name, store in six.iteritems(self._dr_stores):
      setattr(self, name, store.default())
    self._dr_lazy = None

    for k, v in six.iteritems(kwargs):
      setattr(self, k, v)

  @classmethod
  def from_wire(klass, **kwargs):
    for k, v in six.iteritems(kwargs):
      f = klass._dr_fields.get(k, None)
      if hasattr(f, 'from_wire'):
        kwargs[k] = f.from_wire(v)
    return klass(**kwargs)


class Ann(Base):
  __slots__ = ('_dr_index', )

  def __init__(self, **kwargs):
    super(Ann, self).__init__(**kwargs)
    self._dr_index = None

  def __lt__(self, other):
    if self._dr_index is None:
      return -1
    else:
      return self._dr_index < other._dr_index


class Doc(Base):
  __slots__ = ('_dr_rt', '_dr_decorated_by', )

  def __init__(self, **kwargs):
    super(Doc, self).__init__(**kwargs)
    self._dr_rt = None

  def __setattr__(self, attr, value):
    if attr in self._dr_stores and not isinstance(value, StoreList):
      raise ValueError('Cannot overwrite a store ({0}) with a value that is not a StoreList'.format(attr))
    super(Doc, self).__setattr__(attr, value)

  @classmethod
  def schema(klass):
    from .schema import create_schema
    return create_schema(klass)


def safe_klass_or_field_name(name):
  # In py2, class names must be non-Unicode. In py3, class names must be Unicode.
  if six.PY2:
    if not isinstance(name, six.binary_type):
      name = name.encode('utf-8')
  else:
    if not isinstance(name, six.text_type):
      name = name.decode('utf-8')
  return name


def make_ann(name, *named_fields, **defined_fields):
  """
  A collections.namedtuple sister function for creating Ann subclasses.
  @param name The name of the Ann subclass
  @param named_fields The string names of the Field's to add to the class
  @oaran defined_fields Name, field object pairs for fields you want to add to the class that are not of type Field
  @return The created class object
  """
  from .fields_core import Field
  attrs = {}
  for k, v in six.iteritems(defined_fields):
    attrs[safe_klass_or_field_name(k)] = v
  for field in named_fields:
    attrs[safe_klass_or_field_name(field)] = Field()
  return MetaBase(safe_klass_or_field_name(name), (Ann, ), attrs)
