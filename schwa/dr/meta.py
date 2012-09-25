# vim: set ts=2 et:
import StringIO

from .exceptions import DependencyException
from .fields import BaseField, Store

__all__ = ['Ann', 'Doc', 'MetaBase']


class MetaBase(type):
  _registered = {}  # { _dr_name : klass }

  def __new__(mklass, klass_name, bases, attrs):
    # construct the class
    klass = super(MetaBase, mklass).__new__(mklass, klass_name, bases, attrs)

    # discover the Field and Store instances
    stores, fields = {}, {}
    for base in bases:
      stores.update(getattr(base, '_dr_stores', {}))
      fields.update(getattr(base, '_dr_fields', {}))
    for name, attr in attrs.iteritems():
      if isinstance(attr, Store):
        stores[name] = attr
      elif isinstance(attr, BaseField):
        fields[name] = attr

    # adds the Field and Store information appropriately
    klass._dr_fields = fields  # { attr : Field }
    klass._dr_stores = stores  # { attr : Store }

    # add the name
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

    # ensure _dr_name's are unique
    if klass._dr_name in MetaBase._registered:
      raise ValueError('The name {0!r} has already been registered by another class ({1})'.format(klass._dr_name, MetaBase._registered[klass._dr_name]))
    MetaBase._registered[klass._dr_name] = klass

    # construct the docstring for the class
    MetaBase.add_docstring(klass)

    return klass

  @staticmethod
  def add_docstring(klass):
    doc = StringIO.StringIO()
    write_doc = False
    if klass.__doc__:
      doc.write(klass.__doc__ + '\n')
      write_doc = True
    doc.write('Docrep members for this class:\n')
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


class Base(object):
  __metaclass__ = MetaBase

  def __init__(self, **kwargs):
    for name, field in self._dr_fields.iteritems():
      self.__dict__[name] = field.default()
    for name, store in self._dr_stores.iteritems():
      self.__dict__[name] = store.default()
    self._dr_lazy = None

    for k, v in kwargs.iteritems():
      setattr(self, k, v)

  @classmethod
  def from_wire(klass, **kwargs):
    for k, v in kwargs.iteritems():
      f = klass._dr_fields.get(k, None)
      if hasattr(f, 'from_wire'):
        kwargs[k] = f.from_wire(v)
    return klass(**kwargs)


class Ann(Base):
  pass


class Doc(Base):
  def __init__(self, **kwargs):
    super(Doc, self).__init__(**kwargs)
    self._dr_rt = None

  def __setattr__(self, attr, value):
    if attr in self._dr_stores:
      raise ValueError('Cannot overwrite a store ({0})'.format(attr))
    super(Doc, self).__setattr__(attr, value)

  def ready(self):
    """Hook called after a Document and all its Stores are loaded."""
    pass

  @classmethod
  def schema(klass):
    from .schema import create_schema
    return create_schema(klass)
