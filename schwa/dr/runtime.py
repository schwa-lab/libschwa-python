# vim: set ts=2 et:
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

  def __init__(self):
    self.doc = None  # RTAnn
    self.klasses = []  # [ RTAnn ]


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
  # discover max known field_id
  field_id, known_fields = _find_max_and_known(rtschema.fields, 'field_id')

  # construct the RTField's
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
  # discover known klasses and stores
  klass_id, known_klasses = _find_max_and_known(rt.klasses, 'klass_id')
  store_id, known_stores = _find_max_and_known(rt.doc.stores, 'store_id')

  # construct the RTStore's
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

  # construct the documents RTField's
  _merge_rtschema_fields(rt.doc, doc_schema, rtstore_map)

  # construct the RTAnn's
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

  # back-fill the RTStores' RTSchema pointers now that they exist
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
