# vim: set ts=2 et:
import dateutil.parser

from .fields_core import Field

__all__ = ['DateTime', 'Text']


class DateTime(Field):
  def from_wire(self, val, rtfield, cur_store, doc):
    if val is None:
      return None
    try:
      return dateutil.parser.parse(val)
    # Some parse errors manifest as Nones.
    except TypeError:
      return None

  def to_wire(self, obj, rtfield, cur_store, doc):
    if obj is None:
      return None
    return obj.isoformat()


class Text(Field):
  __slots__ = ('encoding', )

  def __init__(self, encoding='utf-8', store_empty=False, **kwargs):
    super(Text, self).__init__(**kwargs)
    self.encoding = encoding
    if not store_empty:
        self.should_write = lambda val: val

  def from_wire(self, val, rtfield, cur_store, doc):
    if val is None:
      return None
    return val.decode(self.encoding)

  def to_wire(self, obj, rtfield, cur_store, doc):
    if obj is None:
      return None
    return obj.encode(self.encoding)
