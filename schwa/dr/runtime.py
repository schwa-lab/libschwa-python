# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

__all__ = ['RTField', 'RTStore', 'RTAnn', 'RTManager', 'build_rt', 'merge_rt']


class RTField(object):
  __slots__ = ('defn', 'points_to', 'serial', 'field_id', 'is_slice', 'is_self_pointer', 'is_collection')

  def __init__(self, field_id, serial, points_to, is_slice, is_self_pointer, is_collection, defn=None):
    self.defn = defn  # FieldSchema
    self.points_to = points_to  # RTStore
    self.serial = serial
    self.field_id = field_id
    self.is_slice = is_slice
    self.is_self_pointer = is_self_pointer
    self.is_collection = is_collection

  def __repr__(self):
    return str(self)

  def __str__(self):
    return 'RTField(field_id={}, serial={!r})'.format(self.field_id, self.serial)

  def is_lazy(self):
    return self.defn is None

  @property
  def is_pointer(self):
    return self.points_to is not None


class RTStore(object):
  __slots__ = ('klass', 'serial', 'store_id', 'defn', 'lazy', 'nelem')

  def __init__(self, store_id, serial, klass, defn=None, lazy=None, nelem=None):
    self.klass = klass  # RTAnn
    self.serial = serial
    self.store_id = store_id
    self.nelem = nelem
    self.defn = defn  # StoreSchema
    self.lazy = lazy

  def __repr__(self):
    return str(self)

  def __str__(self):
    return 'RTStore(store_id={}, serial={!r}, klass={})'.format(self.store_id, self.serial, self.klass)

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

  def build_kwargs(self, res={}):
    return res

  def copy_to_schema(self):
    if not self.defn:
      return
    for rt in self.fields:
      if rt.defn:
        self.defn.add_field(rt.serial, rt.defn)
    for rt in self.stores:
      if rt.defn:
        self.defn.add_store(rt.serial, rt.defn)

  def is_lazy(self):
    return self.defn is None


class AutomagicRTAnn(RTAnn):
  __slots__ = ('_init_kwargs',)

  def __init__(self, *args, **kwargs):
    super(AutomagicRTAnn, self).__init__(*args, **kwargs)
    self._init_kwargs = {}

  def build_kwargs(self):
    return {k: v() for k, v in self._init_kwargs.items()}

  def add_kwarg(self, name, default_fn):
    self._init_kwargs[name] = default_fn


class RTManager(object):
  __slots__ = ('doc', 'klasses')
  Field = RTField
  Ann = RTAnn
  Store = RTStore

  def __init__(self):
    self.doc = None  # RTAnn
    self.klasses = []  # [ RTAnn ]

  def copy_to_schema(self):
    for klass in self.klasses:
      klass.copy_to_schema()
    return self.doc.defn


class AutomagicRTManager(RTManager):
  __slots__ = ()
  Ann = AutomagicRTAnn


## =============================================================================
## =============================================================================
def _find_max_and_known(collection, id_attr):
  max_id = 0
  known = {}  # { str : RT* }
  if collection:
    for rt_obj in collection:
      if not rt_obj.is_lazy():
        known[rt_obj.defn.name] = rt_obj
      max_id = max(getattr(rt_obj, id_attr), max_id)
    max_id += 1
  return max_id, known


def _merge_rtschema_fields(rtschema, ann_schema, rtstore_map):
  # Discover max known field_id.
  field_id, known_fields = _find_max_and_known(rtschema.fields, 'field_id')

  # Construct the RTFields.
  for field_schema in ann_schema.fields():
    rtfield = known_fields.get(field_schema.name)
    if rtfield is None:
      points_to = None
      if field_schema.is_pointer:
        points_to = rtstore_map[field_schema.points_to]
      rtfield = RTField(field_id, field_schema.serial, points_to, field_schema.is_slice, field_schema.is_self_pointer, field_schema.is_collection, defn=field_schema)
      rtschema.fields.append(rtfield)
      field_id += 1
    else:
      rtfield.defn = field_schema
  if rtschema.fields:
    rtschema.fields.sort(key=lambda f: f.field_id)
    assert rtschema.fields[-1].field_id + 1 == len(rtschema.fields)


def merge_rt(rt, doc_schema):
  """
  Merges an existing RTManager instance with the provided DocSchema instance
  @param rt the existing RTManager instance
  @param doc_schema a DocSchema object from which to merge with the given RTManager instance
  @return the merged RTManager object
  """
  # Discover known klasses and stores.
  klass_id, known_klasses = _find_max_and_known(rt.klasses, 'klass_id')
  store_id, known_stores = _find_max_and_known(rt.doc.stores, 'store_id')

  # Construct the RTStores.
  rtstore_map = {}  # { StoreSchema : RTStore }
  for store_schema in doc_schema.stores():
    rtstore = known_stores.get(store_schema.name)
    if rtstore is None:
      rtstore = RTStore(store_id, store_schema.serial, None, store_schema)
      rt.doc.stores.append(rtstore)
      known_stores[store_schema.name] = rtstore
      store_id += 1
    else:
      rtstore.defn = store_schema
    rtstore_map[store_schema] = rtstore
  if rt.doc.stores:
    rt.doc.stores.sort(key=lambda s: s.store_id)
    assert rt.doc.stores[-1].store_id + 1 == len(rt.doc.stores)

  # Construct the documents RTFields.
  _merge_rtschema_fields(rt.doc, doc_schema, rtstore_map)

  # Construct the RTAnns.
  rtann_map = {}  # { AnnSchema : RTAnn }
  for ann_schema in doc_schema.klasses():
    rtschema = known_klasses.get(ann_schema.name)
    if rtschema is None:
      rtschema = RTAnn(klass_id, ann_schema.serial, ann_schema)
      rt.klasses.append(rtschema)
      klass_id += 1
    else:
      rtschema.defn = ann_schema
    _merge_rtschema_fields(rtschema, ann_schema, rtstore_map)
    rtann_map[ann_schema] = rtschema

  # Back-fill the RTStores' RTSchema pointers now that they exist.
  for store_schema in doc_schema.stores():
    rtstore = rtstore_map[store_schema]
    if rtstore.klass is None:
      rtstore.klass = rtann_map[store_schema.stored_type]

  return rt


def build_rt(doc_schema):
  """
  Constructs a RTManager instance from a DocSchema instance
  @param doc_schema a DocSchema object from which to construct a RTManager instance
  @return the newly created RTManager object
  """
  rt_doc = RTAnn(0, '__meta__', doc_schema)
  rt = RTManager()
  rt.doc = rt_doc
  rt.klasses.append(rt_doc)
  return merge_rt(rt, doc_schema)
