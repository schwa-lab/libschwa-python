# vim: set ts=2 et:
import dateutil.parser

from .fields import Field

__all__ = ['DateTime', 'Text']


class DateTime(Field):
  def from_wire(self, val, rtfield, cur_store, doc):
    if val is None:
      return None
    return dateutil.parser.parse(val)

  def to_wire(self, obj, rtfield, cur_store, doc):
    if obj is None:
      return None
    return obj.isoformat()


class Text(Field):
  __slots__ = ('encoding', )

  def __init__(self, encoding='utf-8', **kwargs):
    super(Text, self).__init__(**kwargs)
    self.encoding = encoding

  def from_wire(self, val, rtfield, cur_store, doc):
    if val is None:
      return None
    return val.decode(self.encoding)

  def to_wire(self, obj, rtfield, cur_store, doc):
    if obj is None:
      return None
    return obj.encode(self.encoding)
