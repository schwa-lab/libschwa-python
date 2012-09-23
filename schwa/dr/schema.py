# vim: set ts=2 et:
import inspect

from .meta import Ann


class AnnSchema(object):
  __slots__ = ('name', 'help', 'serial', 'fields')

  def __init__(self, name, help, serial):
    self.name = name
    self.help = help
    self.serial = serial
    self.fields = {}

  def __contains__(self, name):
    if not isinstance(name, (str, unicode)):
      raise ValueError('__contains__ needs a str or unicode field name')
    name = name.encode('utf-8')
    return name in self.fields

  def __getitem__(self, name):
    if not isinstance(name, (str, unicode)):
      raise ValueError('__getitem__ needs a str or unicode field name')
    name = name.encode('utf-8')
    return self.fields[name]


class DocSchema(object):
  __slots__ = ('name', 'help', 'serial', 'fields', 'klasses')

  def __init__(self, name, help, serial):
    self.name = name
    self.help = help
    self.serial = serial
    self.fields = {}
    self.klasses = {}

  def __contains__(self, arg):
    if inspect.isclass(arg) and issubclass(arg, Ann):
      return arg in self.klasses
    elif isinstance(arg, (str, unicode)):
      name = arg.encode('utf-8')
      return name in self.fields
    else:
      raise ValueError('__contains__ needs a str or unicode field name or an Ann subclass')

  def __getitem__(self, arg):
    if inspect.isclass(arg) and issubclass(arg, Ann):
      return self.klasses[arg]
    elif isinstance(arg, (str, unicode)):
      name = arg.encode('utf-8')
      return self.fields[name]
    else:
      raise ValueError('__getitem__ needs a str or unicode field name or an Ann subclass')
