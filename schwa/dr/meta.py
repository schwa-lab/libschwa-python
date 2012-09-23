# vim: set ts=2 et:
import StringIO

from .fields import BaseField, BaseStore

__all__ = ['Ann', 'Doc']


class DocrepMeta(type):
  def __new__(mklass, klass_name, bases, attrs):
    # construct the class
    klass = super(DocrepMeta, mklass).__new__(mklass, klass_name, bases, attrs)

    # discover the BaseField and BaseStore instances
    stores, fields = {}, {}
    for base in bases:
      stores.update(getattr(base, '_dr_stores', {}))
      fields.update(getattr(base, '_dr_fields', {}))
    for name, attr in attrs.iteritems():
      if isinstance(attr, BaseStore):
        stores[name] = attr
      elif isinstance(attr, BaseField):
        fields[name] = attr

    # adds the Field and Store information appropriately
    klass._dr_fields = fields  # { attr : Field }
    klass._dr_stores = stores  # { attr : Store }

    # add the name
    meta = attrs.get('Meta', None)
    if hasattr(meta, 'serial'):
      klass._dr_serial = meta.serial
    else:
      klass._dr_serial = klass_name

    # construct the docstring for the class
    DocrepMeta.add_docstring(klass)

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


class Base(object):
  __metaclass__ = DocrepMeta

  def __init__(self, **kwargs):
    for name, field in self._dr_fields.iteritems():
      setattr(self, name, field.default())
    for name, store in self._dr_stores.iteritems():
      setattr(self, name, store.default())

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
