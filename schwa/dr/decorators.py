# vim: set ts=2 et:
from collections import defaultdict
from functools import partial
from operator import attrgetter
import itertools
from types import StringTypes, TupleType

from .decoration import Decorator

__all__ = ['add_prev_next', 'build_index', 'build_multi_index', 'materialise_slices', 'reverse_slices', 'find_contained_slices', 'convert_slices', 'reverse_pointers']


def _attrsetter(attr):
  if attr is None:
    fn = lambda obj, val: None
  else:
    fn = lambda obj, val: setattr(obj, attr, val)

  # Set a default value like any other value
  fn.default = fn
  return fn


def _attrappender(attr):
  if attr is None:
    fn = lambda obj, val: None
    fn.default = fn
    return fn

  def fn(obj, val):
    try:
      getattr(obj, attr).append(val)
    except AttributeError:
      setattr(obj, attr, [val])

  # Do not set a default value, just initialise the list
  def default_fn(obj, val):
    setattr(obj, attr, [])
  fn.default = default_fn
  return fn


def _attrgetter(attr):
  if callable(attr):
    return attr
  return attrgetter(attr)


def _storegetter(store):
  """
  Allows decorator arguments referring to a store of objects either to be a
  named attribute of a document, or a function which returns a list of objects
  given a document.
  """
  if callable(store):
    return store
  else:
    return attrgetter(store)


class add_prev_next(Decorator):
  """
  Adds prev and next pointers or None where N/A. Also may add index.
  """
  def __init__(self, store, prev_attr='prev', next_attr='next', index_attr=None):
    super(add_prev_next, self).__init__(self._build_key(store, prev_attr, next_attr, index_attr))
    self.get_store = _storegetter(store)
    self.set_prev = _attrsetter(prev_attr)
    self.set_next = _attrsetter(next_attr)
    self.set_index = _attrsetter(index_attr)
    self._set_affected_fields((store, prev_attr), (store, next_attr), (store, index_attr))

  def decorate(self, doc):
    prev = None
    for i, item in enumerate(self.get_store(doc)):
      self.set_prev(item, prev)
      self.set_index(item, i)
      if prev:
        self.set_next(prev, item)
      prev = item
    if prev:
      self.set_next(prev, None)


class build_index(Decorator):
  """
  Constructs an index over a selected field (key_attr) from a given object
  store, and stores it on the document at index_attr. By default the index
  maps from a keys to single object. If the extracted key is iterable and
  is not a string or tuple, multiple keys will be mapped for the object.

  Setting by_index=True will map to the object's offset in the given store
  instead of the object itself. The construct and add_entry arguments may define
  an arbitrary indexing structure.
  """
  def __init__(self, store, key_attr, index_attr, construct=dict, add_entry='__setitem__', by_index=False):
    super(build_index, self).__init__(self._build_key(index_attr, key_attr, store, construct, add_entry, by_index))
    self.get_objects = _storegetter(store)
    self.set_index = _attrsetter(index_attr)
    self.get_key = _attrgetter(key_attr)
    self.construct_index = construct
    self.get_add_entry = _attrgetter(add_entry)
    self.by_index = by_index
    self._set_affected_fields(index_attr)

  def decorate(self, doc):
    res = self.construct_index()
    self.set_index(doc, res)
    add_entry = self.get_add_entry(res)

    for i, obj in enumerate(self.get_objects(doc)):
      val = i if self.by_index else obj
      try:
        keys = self.get_key(obj)
      except AttributeError:
        # Is this correct behaviour?
        # Or should users ensure all objects in the store have the appropriate attribute?
        # WARNING: This behaviour may hide true AttributeErrors
        continue
      if isinstance(keys, (StringTypes, TupleType)) or not hasattr(keys, '__iter__'):
        keys = (keys,)
      for key in keys:
        add_entry(key, val)


class build_multi_index(build_index):
  def __init__(self, *args, **kwargs):
    kwargs['construct'] = partial(defaultdict, set)
    kwargs['add_entry'] = lambda index: lambda key, val: index[key].add(val)
    super(build_multi_index, self).__init__(*args, **kwargs)


class materialise_slices(Decorator):
  """
  Decorates entries in the source_store with deref_attr, the list of elements
  in target_store corresponding to the slice_attr value.
  """
  def __init__(self, source_store, target_store, slice_attr, deref_attr):
    super(materialise_slices, self).__init__(self._build_key(source_store, target_store, slice_attr, deref_attr))
    self.get_source_store = _storegetter(source_store)
    self.get_target_store = _storegetter(target_store)
    self.slice_attr = slice_attr
    self.deref_attr = deref_attr
    self._set_affected_fields((source_store, deref_attr))

  def decorate(self, doc):
    store = self.get_target_store(doc)
    for obj in self.get_source_store(doc):
      span = getattr(obj, self.slice_attr)
      if span is not None:
        setattr(obj, self.deref_attr, store[span])


class reverse_slices(Decorator):
  """api/python/tests/test_decorators.py
  Where objects in source_store point (through slice_attr) to slices over
  objects in target_store, this decorates the target_store objects with any or
  all of: a pointer to a target_store object, its offset within the slice
  range (counting from left and/or right), a tuple of all the above.

  If slices are not mutually exclusive, each attribute will be a list whose
  items correspond to source annotations.
  """

  def __init__(self, source_store, target_store, slice_attr, pointer_attr=None, offset_attr=None, roffset_attr=None, all_attr=None, mutex=True, mark_outside=False):
    super(reverse_slices, self).__init__(self._build_key(source_store, target_store, slice_attr, pointer_attr, offset_attr, roffset_attr, all_attr, mutex, mark_outside))
    self.get_source_store = _storegetter(source_store)
    self.get_target_store = _storegetter(target_store)
    self.slice_attr = slice_attr
    if mutex:
      setter = _attrsetter
    else:
      setter = _attrappender
    self.set_pointer = setter(pointer_attr)
    self.set_offset = setter(offset_attr)
    self.set_roffset = setter(roffset_attr)
    self.set_all = setter(all_attr)
    self.mark_outside = mark_outside
    self._set_affected_fields((target_store, pointer_attr), (target_store, offset_attr), (target_store, roffset_attr), (target_store, all_attr))

  def decorate(self, doc):
    target_items = self.get_target_store(doc)

    if self.mark_outside:
      for target in target_items:
        self.set_pointer.default(target, None)
        self.set_offset.default(target, None)
        self.set_roffset.default(target, None)
        self.set_all.default(target, (None, None, None))

    for source in self.get_source_store(doc):
      span = getattr(source, self.slice_attr)
      if not span:
        continue
      n = span.stop - span.start
      for i, target in enumerate(target_items[span]):
        self.set_pointer(target, source)
        self.set_offset(target, i)
        roffset = n - i - 1
        self.set_roffset(target, roffset)
        self.set_all(target, (source, i, roffset))


class find_contained_slices(Decorator):
  """
  Adds collection_attr to each containing_store object O, being a list of the
  objects in contained_store with a contained_slice that is a sub-span of O's
  containing_slice value.

  If contained_store (or contained_slice) is None, the value is copied from
  containing_store (containing_slice). In this case, each O will not be
  included in its contained objects collection.
  """
  def __init__(self, containing_store, containing_slice, contained_store=None, contained_slice=None, collection_attr=None):
    if not collection_attr:
      raise ValueError('collection_attr must be a non-empty string')
    super(find_contained_slices, self).__init__(self._build_key(containing_store, containing_slice, contained_store, contained_slice, collection_attr))
    self.get_containing_store = _storegetter(containing_store)
    self.get_containing_slice = attrgetter(containing_slice)
    self.get_contained_store = _storegetter(contained_store or containing_store)
    self.get_contained_slice = attrgetter(contained_slice or containing_slice)
    self.set_collection = _attrsetter(collection_attr)
    self.get_collection = attrgetter(collection_attr)
    self._set_affected_fields((containing_store, collection_attr))

  def _gen_tuples(self, store, get_slice, group):
    for obj in store:
      sl = get_slice(obj)
      if not sl:
        continue
      yield sl.start, -sl.stop, group, obj

  def decorate(self, doc, CONTAINING_GROUP=0, CONTAINED_GROUP=1):
    containing_tuples = self._gen_tuples(self.get_containing_store(doc), self.get_containing_slice, CONTAINING_GROUP)
    contained_tuples = self._gen_tuples(self.get_contained_store(doc), self.get_contained_slice, CONTAINED_GROUP)
    open_containers = []
    for tup in sorted(itertools.chain(containing_tuples, contained_tuples)):
      start, stop, group, obj = tup
      while open_containers and start >= open_containers[-1][1]:
        open_containers.pop()

      if group == CONTAINING_GROUP:
        collection = []
        self.set_collection(obj, collection)
        open_containers.append((start, -stop, obj, collection))
      else:
        for cstart, cstop, container, collection in open_containers:
          if container != obj:
            collection.append(obj)


class convert_slices(Decorator):
  """
  Augments source_store objects with new_slice_attr, whose value corresponds to
  source_slice_attr over the finer granularity indicated by target_slice_attr.

  For example, if Sentence.span is a Slice over Token objects, and Token.span
  indicates a Slice over raw text, this decorator could be used to augment
  Sentence objects with Slice attributes over raw text.
  """
  def __init__(self, source_store, target_store, source_slice_attr, target_slice_attr, new_slice_attr):
    super(convert_slices, self).__init__(self._build_key(source_store, target_store, source_slice_attr, target_slice_attr, new_slice_attr))
    self.get_source_store = _storegetter(source_store)
    self.get_target_store = _storegetter(target_store)
    self.get_source_slice = attrgetter(source_slice_attr)
    self.get_target_slice = attrgetter(target_slice_attr)
    self.set_new_slice = _attrsetter(new_slice_attr)
    self._set_affected_fields((source_store, new_slice_attr))

  def decorate(self, doc):
    targets = self.get_target_store(doc)
    for source in self.get_source_store(doc):
      source_slice = self.get_source_slice(source)
      try:
        start = source_slice.start
        stop = source_slice.stop
      except AttributeError:
        self.set_new_slice(source, None)
        continue

      start = self.get_target_slice(targets[start])
      stop = self.get_target_slice(targets[stop - 1])
      try:
        self.set_new_slice(source, slice(start.start, stop.stop))
      except AttributeError:
        self.set_new_slice(source, None)


class reverse_pointers(Decorator):
  """
  Where objects in source_store point (through pointer_attr) to objects in
  target_store, this decorates the target objects with a rev_attr attribute
  pointing back to the source object.
  """

  def __init__(self, source_store, target_store, pointer_attr, rev_attr, mutex=True, mark_outside=False):
    super(reverse_pointers, self).__init__(self._build_key(source_store, target_store, pointer_attr, rev_attr, mutex, mark_outside))
    self.get_source_store = _storegetter(source_store)
    self.get_target_store = _storegetter(target_store)
    self.pointer_attr = pointer_attr
    if mutex:
      setter = _attrsetter
    else:
      setter = _attrappender
    self.set_rev = setter(rev_attr)
    self.mark_outside = mark_outside
    self._set_affected_fields((target_store, rev_attr))

  def decorate(self, doc):
    if self.mark_outside:
      for target in self.get_target_store(doc):
        self.set_rev.default(target, None)

    for source in self.get_source_store(doc):
      target = getattr(source, self.pointer_attr)
      if not target:
        continue
      if isinstance(target, list):
        for target_item in target:
          self.set_rev(target_item, source)
      else:
        self.set_rev(target, source)
