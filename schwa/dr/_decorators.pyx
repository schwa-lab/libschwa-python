#cython: wraparound=False
#cython: checkbounds=True

from cpython cimport PyList_GetSlice

cdef inline append_to_attr(obj, attr, val):
  x = getattr(obj, attr, None)
  if x is None:
    setattr(obj, attr, [val])
  else:
    x.append(val)


def materialize_slices(slice_attr, deref_attr,
                       source_store, target_store):
  cdef list sources = <list> source_store 
  cdef list targets = <list> target_store
  cdef slice span

  for source in sources:
    span = getattr(source, slice_attr)
    if span is not None:
      # TODO: use PyList_GetSlice
      setattr(source, deref_attr, PyList_GetSlice(targets, span.start, span.stop))


def reverse_slices(slice_attr, pointer_attr, offset_attr, roffset_attr,
                   all_attr, bint mutex, bint mark_outside,
                   source_store, target_store):
  cdef list sources = <list> source_store 
  cdef list targets = <list> target_store

  cdef bint want_pointer = bool(pointer_attr)
  cdef bint want_offset = bool(offset_attr)
  cdef bint want_roffset = bool(roffset_attr)
  cdef bint want_all = bool(all_attr)

  cdef slice span
  cdef int i
  cdef int start
  cdef int stop

  if mutex:
    if mark_outside:
      for target in targets:
        if want_pointer:
          setattr(target, pointer_attr, None)
        if want_offset:
          setattr(target, offset_attr, None)
        if want_roffset:
          setattr(target, roffset_attr, None)
        if want_all:
          setattr(target, all_attr, (None, None, None))
      
    for source in sources:
      span_ = getattr(source, slice_attr)
      if span_ is None:
          continue
      span = <slice> span_
      i = start = span.start
      stop = span.stop
      while i < stop:
        target = targets[i]
        if want_pointer:
          setattr(target, pointer_attr, source)
        if want_offset:
          setattr(target, offset_attr, i - start)
        if want_roffset:
          setattr(target, roffset_attr, stop - i - 1)
        if want_all:
          setattr(target, all_attr, (source, i - start, stop - i - 1))
        i += 1

  else:  # not mutually exclusvie
    if mark_outside:
      for target in targets:
        if want_pointer:
          setattr(target, pointer_attr, [])
        if want_offset:
          setattr(target, offset_attr, [])
        if want_roffset:
          setattr(target, roffset_attr, [])
        if want_all:
          setattr(target, all_attr, [])
      
    for source in sources:
      span_ = getattr(source, slice_attr)
      if span_ is None:
          continue
      span = <slice> span_
      i = start = span.start
      stop = span.stop
      while i < stop:
        target = targets[i]
        if want_pointer:
          append_to_attr(target, pointer_attr, source)
        if want_offset:
          append_to_attr(target, offset_attr, i - start)
        if want_roffset:
          append_to_attr(target, roffset_attr, stop - i - 1)
        if want_all:
          append_to_attr(target, all_attr, (source, i - start, stop - i - 1))
        i += 1


def reverse_pointers(pointer_attr, rev_attr,
                     bint mutex, bint mark_outside,
                     source_store, target_store):

  if mutex:
    if mark_outside:
      for target in <list> target_store:
        setattr(target, rev_attr, None)
      
    for source in <list> source_store:
      target = getattr(source, pointer_attr)
      if target is None:
        continue
      elif isinstance(target, list):
        for t in <list> target:
          setattr(t, rev_attr, source)
      else:
        setattr(target, rev_attr, source)

  else:  # not mutually exclusvie
    if mark_outside:
      for target in <list> target_store:
        setattr(target, rev_attr, [])
      
    for source in <list> source_store:
      target = getattr(source, pointer_attr)
      if target is None:
        continue
      elif isinstance(target, list):
        for t in <list> target:
          append_to_attr(t, rev_attr, source)
      else:
        append_to_attr(target, rev_attr, source)


def add_prev_next(prev_attr, next_attr, index_attr, store):
  cdef list items = <list> store
  cdef bint want_prev = bool(prev_attr)
  cdef bint want_next = bool(prev_attr)
  cdef bint want_index = bool(index_attr)
  cdef int i
  
  prev = None
  for i, item in enumerate(store):
    if want_prev:
      setattr(item, prev_attr, prev)
    if want_next and prev is not None:
      setattr(prev, next_attr, item)
    if want_index:
      setattr(item, index_attr, i)
    prev = item

  if want_next and prev is not None:
    setattr(prev, next_attr, None)
