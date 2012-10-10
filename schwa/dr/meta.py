# vim: set ts=2 et:
import StringIO

from .containers import StoreList
from .exceptions import DependencyException
from .fields_core import BaseField, Store

__all__ = ['Ann', 'Doc', 'MetaBase', 'make_ann']


class MetaBase(type):
  _registered = {}  # { _dr_name : klass }

  def __new__(mklass, klass_name, bases, attrs):
    # sanity check the base classes
    is_here = has_ann_base = has_doc_base = False
    for base in bases:
      if attrs.get('__module__') == MetaBase.__module__:
        is_here = True
      else:
        #from . import Ann, Doc
        if issubclass(base, Ann):
          has_ann_base = True
        elif issubclass(base, Doc):
          has_doc_base = True
    if not is_here:
      if has_ann_base and has_doc_base:
        raise ValueError('Class {0!r} cannot have both Ann and Doc as a base class'.format(klass_name))
      elif not (has_ann_base or has_doc_base):
        raise ValueError('Class {0!r} must have either Ann or Doc as a base class'.format(klass_name))

    # discover the Field and Store instances
    fields, stores = {}, {}
    for base in bases:
      fields.update(getattr(base, '_dr_fields', {}))
      stores.update(getattr(base, '_dr_stores', {}))
    for name, attr in attrs.iteritems():
      if isinstance(attr, Store):
        # die if a Store is placed on an Ann
        if has_ann_base:
          raise ValueError('Class {0!r} cannot house a Store ({1!r}) as it is not a Doc subclass'.format(klass_name, name))
        stores[name] = attr
      elif isinstance(attr, BaseField):
        fields[name] = attr

    # construct __slots__
    if not is_here:
      if '__slots__' in attrs:
        slots = list(attrs['__slots__']) + list(fields) + list(stores)
        attrs['__slots__'] = tuple(slots)

      # remove the Store and BaseField objects from the set of class attributes so that they can be overwritten by instances of the class
      for key in fields:
        if key in attrs:
          del attrs[key]
      for key in stores:
        if key in attrs:
          del attrs[key]

    # construct the class
    klass = super(MetaBase, mklass).__new__(mklass, klass_name, bases, attrs)

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
  __slots__ = ('_dr_decorated_by', '_dr_lazy')

  def __init__(self, **kwargs):
    for name, field in self._dr_fields.iteritems():
      setattr(self, name, field.default())
    for name, store in self._dr_stores.iteritems():
      setattr(self, name, store.default())
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
  __slots__ = ('_dr_index', )

  def __init__(self, **kwargs):
    super(Ann, self).__init__(**kwargs)
    self._dr_index = None


class Doc(Base):
  __slots__ = ('_dr_rt', )

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


def make_ann(name, *named_fields, **defined_fields):
  """
  A collections.namedtuple sister function for creating Ann subclasses.
  @param name The name of the Ann subclass
  @param named_fields The string names of the Field's to add to the class
  @oaran defined_fields Name, field object pairs for fields you want to add to the class that are not of type Field
  @return The created class object
  """
  from .fields_core import Field
  attrs = dict(defined_fields)
  for field in named_fields:
    attrs[field] = Field()
  return MetaBase(name, (Ann, ), attrs)
