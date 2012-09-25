# vim: set ts=2 et:
__all__ = ['RTField', 'RTStore', 'RTAnn', 'RTManager', 'build_rt', 'merge_rt']


class RTField(object):
  __slots__ = ('defn', 'points_to', 'serial', 'field_id', 'is_slice', 'is_self_pointer')

  def __init__(self, field_id, serial, points_to, is_slice, is_self_pointer, defn=None):
    self.defn = defn  # FieldSchema
    self.points_to = points_to  # RTStore
    self.serial = serial
    self.field_id = field_id
    self.is_slice = is_slice
    self.is_self_pointer = is_self_pointer

  def is_lazy(self):
    return self.defn is None

  @property
  def is_pointer(self):
    return self.points_to is not None


class RTStore(object):
  __slots__ = ('klass', 'serial', 'store_id', 'defn', 'lazy')

  def __init__(self, store_id, serial, klass, defn=None, lazy=None):
    self.klass = klass  # RTAnn
    self.serial = serial
    self.store_id = store_id
    self.defn = defn  # StoreSchema
    self.lazy = lazy

  def is_lazy(self):
    return self.defn is None


class RTAnn(object):
  __slots__ = ('serial', 'klass_id', 'fields', 'stores', 'defn')

  def __init__(self, klass_id, serial, defn=None):
    self.serial = serial
    self.klass_id = klass_id
    self.fields = []
    self.stores = []
    self.defn = defn  # AnnSchema

  def is_lazy(self):
    return self.defn is None


class RTManager(object):
  __slots__ = ('doc', 'klasses')

  def __init__(self, doc=None):
    self.doc = doc  # RTAnn
    self.klasses = []  # [ RTAnn ]


def build_rt(dschema):
  pass


def merge_rt(rt, dschema):
  pass
