
from unittest import TestCase

from schwa import dr

class Document(dr.Document):
  annots = dr.Store('MyAnnot')
  slices = dr.Store('SliceAnnot')
  super_slices = dr.Store('SuperSliceAnnot')
  favourites = dr.Pointers('MyAnnot')

class MyAnnot(dr.Annotation):
  field = dr.Field()
  children = dr.Pointers('MyAnnot')
  child = dr.Pointer('MyAnnot')

  def __repr__(self):
    return '{}(field={}, children={}, child={})'.format(self.__class__.__name__, self.field, self.children, self.child)

class SliceAnnot(dr.Annotation):
  span = dr.Slice('MyAnnot')
  name = dr.Field()

  def __repr__(self):
    return '{}(span={}, name={})'.format(self.__class__.__name__, self.span, self.name)

class SuperSliceAnnot(dr.Annotation):
  slice_span = dr.Slice('SliceAnnot')


class SliceDecoratorsTest(TestCase):
  def setUp(self):
    self.doc = Document()
    for val in '0123456':
      self.doc.annots.create(field=val)
    self.doc.slices.create(span=slice(1, 4), name='Long slice')
    self.doc.slices.create(span=slice(5, 6), name='Unit slice')

  def test_materialise_slices(self):
    decorate = dr.decorators.materialise_slices('slices', 'annots', 'span', 'annots')
    for sl in self.doc.slices:
      self.assertFalse(hasattr(sl, 'annots'))

    decorate(self.doc)

    self.assertEqual('123', ''.join(a.field for a in self.doc.slices[0].annots))
    self.assertEqual('5', ''.join(a.field for a in self.doc.slices[1].annots))

  def test_reverse_mutually_exclusive_slices(self, mark_outside=False):
    decorate = dr.decorators.reverse_slices('slices', 'annots', 'span', pointer_attr='slice_pointer', offset_attr='slice_offset', roffset_attr='slice_roffset', all_attr='slice_all', mutex=True, mark_outside=mark_outside)
    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'slice_pointer'))
      self.assertFalse(hasattr(a, 'slice_offset'))
      self.assertFalse(hasattr(a, 'slice_roffset'))
      self.assertFalse(hasattr(a, 'slice_all'))

    decorate(self.doc)
    annots = self.doc.annots
    slices = self.doc.slices

    EXPECTED = {
      1: (slices[0], 0, 2),
      2: (slices[0], 1, 1),
      3: (slices[0], 2, 0),
      5: (slices[1], 0, 0),
    }
    EXPECTED_OUTSIDE = (None, None, None)

    for i, a in enumerate(annots):
      if i in EXPECTED:
        self.assertEqual((a.slice_pointer, a.slice_offset, a.slice_roffset), EXPECTED[i])
        self.assertEqual(a.slice_all, EXPECTED[i])
      elif mark_outside:
        self.assertEqual((a.slice_pointer, a.slice_offset, a.slice_roffset), EXPECTED_OUTSIDE)
        self.assertEqual(a.slice_all, EXPECTED_OUTSIDE)
      else:
        self.assertFalse(hasattr(a, 'slice_pointer'))
        self.assertFalse(hasattr(a, 'slice_offset'))
        self.assertFalse(hasattr(a, 'slice_roffset'))
        self.assertFalse(hasattr(a, 'slice_all'))

  def test_reverse_mutually_exclusive_slices_with_o(self):
    self.test_reverse_mutually_exclusive_slices(mark_outside=True)

  def test_reverse_slices_no_attrs(self):
    # When no attributes are specified, nothing should not be set
    decorate = dr.decorators.reverse_slices('slices', 'annots', 'span')
    decorate(self.doc)
    # Nothing exploded? Great!

  def test_reverse_overlapping_slices(self, mark_outside=False):
    self.doc.slices.create(span=slice(0, 4), name='Overlapping')
    decorate = dr.decorators.reverse_slices('slices', 'annots', 'span', 'slice_pointer', 'slice_offset', 'slice_roffset', 'slice_all', mutex=False, mark_outside=mark_outside)

    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'slice_pointer'))
      self.assertFalse(hasattr(a, 'slice_offset'))
      self.assertFalse(hasattr(a, 'slice_roffset'))
      self.assertFalse(hasattr(a, 'slice_all'))

    decorate(self.doc)
    annots = self.doc.annots
    slices = self.doc.slices
    EXPECTED = {
      0: [(slices[2], 0, 3)],
      1: [(slices[2], 1, 2), (slices[0], 0, 2)],
      2: [(slices[2], 2, 1), (slices[0], 1, 1)],
      3: [(slices[2], 3, 0), (slices[0], 2, 0)],
      5: [(slices[1], 0, 0)],
    }

    for i, a in enumerate(annots):
      if i in EXPECTED:
        self.assertEqual(set(a.slice_pointer), set(p for p, o, b in EXPECTED[i]))
        self.assertEqual(set(a.slice_offset), set(o for p, o, b in EXPECTED[i]))
        self.assertEqual(set(a.slice_roffset), set(b for p, o, b in EXPECTED[i]))
        self.assertEqual(set(a.slice_all), set(EXPECTED[i]))
      elif mark_outside:
        self.assertEqual(len(a.slice_pointer), 0)
        self.assertEqual(len(a.slice_offset), 0)
        self.assertEqual(len(a.slice_roffset), 0)
        self.assertEqual(len(a.slice_all), 0)
      else:
        self.assertFalse(hasattr(a, 'slice_pointer'))
        self.assertFalse(hasattr(a, 'slice_offset'))
        self.assertFalse(hasattr(a, 'slice_roffset'))
        self.assertFalse(hasattr(a, 'slice_all'))

  def test_reverse_overlapping_slices_with_o(self):
    self.test_reverse_overlapping_slices(mark_outside=True)

  def test_convert_slices(self):
    self.doc.super_slices.create(slice_span=slice(0, 1))
    self.doc.super_slices.create(slice_span=slice(1, 2))
    self.doc.super_slices.create(slice_span=slice(0, 2))
    self.doc.super_slices.create()

    decorate = dr.decorators.convert_slices('super_slices', 'slices', 'slice_span', 'span', 'myannot_span')

    for ss in self.doc.super_slices:
      self.assertFalse(hasattr(ss, 'myannot_span'))
    
    decorate(self.doc)

    EXPECTED = [
      slice(self.doc.slices[0].span.start, self.doc.slices[0].span.stop),
      slice(self.doc.slices[1].span.start, self.doc.slices[1].span.stop),
      slice(self.doc.slices[0].span.start, self.doc.slices[1].span.stop),
      None
    ]

    for i, ss in enumerate(self.doc.super_slices):
      print 'SuperSlice', i
      self.assertEqual(ss.myannot_span, EXPECTED[i])
    self.assertEqual(i, 3)

  def test_find_contained_slices(self):
    self.doc.slices.create(span=slice(1, 3), name='1-3')
    self.doc.slices.create(span=slice(2, 3), name='2-3a')
    self.doc.slices.create(span=slice(2, 3), name='2-3b')
    self.doc.slices.create(span=slice(3, 4), name='3-4')
    decorate = dr.decorators.find_contained_slices('slices', 'span', collection_attr='contained')
    
    for sl in self.doc.slices:
      self.assertFalse(hasattr(sl, 'contained'))
    
    decorate(self.doc)

    EXPECTED = {
        'Unit slice': [],
        'Long slice': ['1-3', '2-3a', '2-3b', '3-4'],
        '1-3': ['2-3a', '2-3b'],
        '2-3a': ['2-3b'],
        '2-3b': ['2-3a'],
        '3-4': [],
    }

    for sl in self.doc.slices:
      self.assertListEqual(EXPECTED[sl.name], [subsl.name for subsl in sl.contained])


class PointerDecoratorTest(TestCase):
  def setUp(self):
    self.doc = Document()
    self.doc.annots.create(field='0')
    self.doc.annots.create(field='1', child=self.doc.annots[0])
    self.doc.annots.create(field='2', children=[self.doc.annots[0], self.doc.annots[1]])

  def test_reverse_mutually_exclusive_pointer(self, mark_outside=False):
    """One child, one parent"""
    decorate = dr.decorators.reverse_pointers('annots', 'annots', 'child', 'parent', mutex=True, mark_outside=mark_outside)

    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'parent'))

    decorate(self.doc)

    EXPECTED = {
      0: self.doc.annots[1],
    }
    for i, a in enumerate(self.doc.annots):
      if i in EXPECTED:
        self.assertEqual(a.parent, EXPECTED[i])
      elif mark_outside:
        self.assertIsNone(a.parent)
      else:
        self.assertFalse(hasattr(a, 'parent'))

  def test_reverse_mutually_exclusive_pointer_with_o(self):
    self.test_reverse_mutually_exclusive_pointer(True)

  def test_reverse_mutually_exclusive_pointers(self, mark_outside=False):
    """Multiple children, one parent"""
    decorate = dr.decorators.reverse_pointers('annots', 'annots', 'children', 'parent', mutex=True, mark_outside=mark_outside)

    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'parent'))

    decorate(self.doc)

    EXPECTED = {
      0: self.doc.annots[2],
      1: self.doc.annots[2],
    }
    for i, a in enumerate(self.doc.annots):
      if i in EXPECTED:
        self.assertEqual(a.parent, EXPECTED[i])
      elif mark_outside:
        self.assertIsNone(a.parent)
      else:
        self.assertFalse(hasattr(a, 'parent'))

  def test_reverse_mutually_exclusive_pointers_with_o(self):
    self.test_reverse_mutually_exclusive_pointers(True)

  def test_reverse_overlapping_pointer(self, mark_outside=False):
    """One child, multiple parents"""
    self.doc.annots[0].child = self.doc.annots[0]
    decorate = dr.decorators.reverse_pointers('annots', 'annots', 'child', 'parents', mutex=False, mark_outside=mark_outside)

    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'parents'))

    decorate(self.doc)

    EXPECTED = {
      0: [self.doc.annots[0], self.doc.annots[1]],
    }
    for i, a in enumerate(self.doc.annots):
      if i in EXPECTED:
        self.assertEqual(set(a.parents), set(EXPECTED[i]))
      elif mark_outside:
        self.assertEqual(len(a.parents), 0)
      else:
        self.assertFalse(hasattr(a, 'parents'))

  def test_reverse_overlapping_pointer_with_o(self):
    self.test_reverse_overlapping_pointer(True)

  def test_reverse_overlapping_pointers(self, mark_outside=False):
    """Multiple children, multiple parents"""
    self.doc.annots[0].children = [self.doc.annots[0]]
    decorate = dr.decorators.reverse_pointers('annots', 'annots', 'children', 'parents', mutex=False, mark_outside=mark_outside)

    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'parents'))

    decorate(self.doc)

    EXPECTED = {
      0: [self.doc.annots[0], self.doc.annots[2]],
      1: [self.doc.annots[2]],
    }
    for i, a in enumerate(self.doc.annots):
      if i in EXPECTED:
        self.assertEqual(set(a.parents), set(EXPECTED[i]))
      elif mark_outside:
        self.assertEqual(len(a.parents), 0)
      else:
        self.assertFalse(hasattr(a, 'parents'))

  def test_reverse_overlapping_pointers_with_o(self):
    self.test_reverse_overlapping_pointers(True)


class PrevNextIndexTest(TestCase):
  def setUp(self):
    self.doc = Document()
    for val in '012':
      self.doc.annots.create(field=val)
    self.doc.slices.create(span=slice(0, 1), name='Unit slice')

  def test_prev_next(self):
    decorate = dr.decorators.add_prev_next('annots', 'prev', 'next')

    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'prev'))
      self.assertFalse(hasattr(a, 'next'))

    decorate(self.doc)

    annots = self.doc.annots
    self.assertEqual(annots[0].next, annots[1])
    self.assertEqual(annots[1].next, annots[2])
    self.assertIsNone(annots[2].next)

    self.assertIsNone(annots[0].prev)
    self.assertEqual(annots[1].prev, annots[0])
    self.assertEqual(annots[2].prev, annots[1])

    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'index'))

  def test_prev_next_single_item(self):
    decorate = dr.decorators.add_prev_next('slices', 'prev', 'next')

    for s in self.doc.slices:
      self.assertFalse(hasattr(s, 'prev'))
      self.assertFalse(hasattr(s, 'next'))

    decorate(self.doc)

    self.assertIsNone(self.doc.slices[0].prev)
    self.assertIsNone(self.doc.slices[0].next)

  def test_index(self):
    decorate = dr.decorators.add_prev_next('annots', index_attr='index')
    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'index'))

    decorate(self.doc)
    for i, a in enumerate(self.doc.annots):
      self.assertEqual(i, a.index)


class BuildIndexTest(TestCase):
  def setUp(self):
    self.doc = Document()
    self.doc.annots.create(field=['dog', 'cat'])
    self.doc.annots.create(field=['mouse'])
    self.doc.slices.create(span=slice(0, 2))
    self.doc.slices.create(span=slice(1, 2))

  def test_single_key(self):
    decorate = dr.decorators.build_index('slices', 'span.start', 'test_index')

    self.assertFalse(hasattr(self.doc, 'test_index'))

    decorate(self.doc)

    EXPECTED = {
        0: self.doc.slices[0],
        1: self.doc.slices[1],
    }
    self.assertEqual(self.doc.test_index, EXPECTED)

  def test_multi_key(self):
    decorate = dr.decorators.build_index('annots', 'field', 'test_index')

    self.assertFalse(hasattr(self.doc, 'test_index'))

    decorate(self.doc)

    EXPECTED = {
        'dog': self.doc.annots[0],
        'cat': self.doc.annots[0],
        'mouse': self.doc.annots[1],
    }
    self.assertEqual(self.doc.test_index, EXPECTED)

  def test_by_index(self):
    decorate = dr.decorators.build_index('annots', 'field', 'test_index', by_index=True)

    self.assertFalse(hasattr(self.doc, 'test_index'))

    decorate(self.doc)

    EXPECTED = {
        'dog': 0,
        'cat': 0,
        'mouse': 1,
    }
    self.assertEqual(self.doc.test_index, EXPECTED)

  def test_multi_value(self):
    decorate = dr.decorators.build_multi_index('slices', 'span.stop', 'test_index')

    self.assertFalse(hasattr(self.doc, 'test_index'))

    decorate(self.doc)

    EXPECTED = {
        2: set((self.doc.slices[0], self.doc.slices[1]))
    }
    self.assertEqual(self.doc.test_index, EXPECTED)

  def test_missing_key(self):
    self.doc.slices.create(span=None)
    decorate = dr.decorators.build_index('slices', 'span.start', 'test_index')

    self.assertFalse(hasattr(self.doc, 'test_index'))

    decorate(self.doc)

    EXPECTED = {
        0: self.doc.slices[0],
        1: self.doc.slices[1],
    }
    self.assertEqual(self.doc.test_index, EXPECTED)


class StoreSubsetTest(TestCase):
  """Tests using a function instead of an attribute as a store reference"""

  def setUp(self):
    self.doc = Document()
    for val in '0123456':
      self.doc.annots.create(field=val)
    self.doc.favourites = [self.doc.annots[i] for i in (1,3,5)]

  def add_prev_next_favourites_test(self):
    decorate = dr.decorators.add_prev_next(lambda doc: doc.favourites, 'prev', 'next', 'index')

    for a in self.doc.annots:
      self.assertFalse(hasattr(a, 'prev'))
      self.assertFalse(hasattr(a, 'next'))
      self.assertFalse(hasattr(a, 'index'))

    decorate(self.doc)

    EXPECTED = {
      1: (None, self.doc.annots[3], 0),
      3: (self.doc.annots[1], self.doc.annots[5], 1),
      5: (self.doc.annots[3], None, 2),
    }
    for i, a in enumerate(self.doc.annots):
      if i in EXPECTED:
        self.assertEqual((a.prev, a.next, a.index), EXPECTED[i])
      else:
        self.assertFalse(hasattr(a, 'prev'))
        self.assertFalse(hasattr(a, 'next'))
        self.assertFalse(hasattr(a, 'index'))


class ApplicationsTest(TestCase):
  def real_world_applications_test(self):
    class Doc(dr.Document):
      tokens = dr.Store('Token')
      entities = dr.Store('Entity')

    class Token(dr.Token):
      def __repr__(self):
        return 'Token(norm={0!r}, span={1}:{2})'.format(self.norm, self.span.start, self.span.stop)

    class Entity(dr.Annotation):
      token_span = dr.Slice('Token')
      type = dr.Field()
      def __repr__(self):
        return 'Entity(type={0!r}, token_span={1}:{2})'.format(self.type, self.token_span.start, self.token_span.stop)

    #       0         1         2         3         4         5         6         7         8
    #       0123456789012345678901234567890123456789012345678901234567890123456789012345678901
    text = "Tony Abbott's address to party as Gillard polls as preferred prime minister again."

    doc = Doc()
    doc.tokens.create(norm="Tony", span=slice(0, 4))        # 0
    doc.tokens.create(norm="Abbott", span=slice(5, 11))     # 1
    doc.tokens.create(norm="'s", span=slice(11, 13))        # 2
    doc.tokens.create(norm="address", span=slice(14, 21))   # 3
    doc.tokens.create(norm="to", span=slice(22, 24))        # 4
    doc.tokens.create(norm="party", span=slice(25, 30))     # 5
    doc.tokens.create(norm="as", span=slice(31, 33))        # 6
    doc.tokens.create(norm="Gillard", span=slice(34, 41))   # 7
    doc.tokens.create(norm="polls", span=slice(42, 47))     # 8
    doc.tokens.create(norm="as", span=slice(48, 50))        # 9
    doc.tokens.create(norm="preferred", span=slice(51, 60)) # 10
    doc.tokens.create(norm="prime", span=slice(61, 66))     # 11
    doc.tokens.create(norm="minister", span=slice(67, 74))  # 12
    doc.tokens.create(norm="again", span=slice(76, 81))     # 13
    doc.tokens.create(norm=".", span=slice(81, 82))         # 14
    doc.entities.create(type='PER', token_span=slice(0, 2)) # 0
    doc.entities.create(type='PER', token_span=slice(7, 8)) # 1

    # convert from character spans to token spans
    dr.decorators.build_index('tokens', 'span.start', 'token_index_by_start', by_index=True)(doc)
    dr.decorators.build_index('tokens', 'span.stop', 'token_index_by_stop', by_index=True)(doc)
    prime_minister_span = slice(doc.token_index_by_start[61], doc.token_index_by_stop[74])
    self.assertEqual(slice(11, 12), prime_minister_span)
    doc.entities.create(type='PER_DESC', token_span=prime_minister_span)

    # look up all mentions of a type
    dr.decorators.build_multi_index('entities', 'type', 'entities_by_type')(doc)
    self.assertEqual(set([doc.entities[0], doc.entities[1]]), doc.entities_by_type['PER'])

    # convert from token spans to character spans
    dr.decorators.convert_slices('entities', 'tokens', 'token_span', 'span', 'char_span')(doc)
    self.assertSetEqual(set(repr(x) for x in (slice(0, 11), slice(34, 41))), set(repr(ent.char_span) for ent in doc.entities_by_type['PER']))

    # traverse tokens in context around entity
    dr.decorators.materialise_slices('entities', 'tokens', 'token_span', 'tokens')(doc)
    dr.decorators.add_prev_next('tokens', 'prev', 'next')(doc)
    self.assertEqual([('preferred', 'minister')], [(entity.tokens[0].prev.norm, entity.tokens[-1].next.norm) for entity in doc.entities_by_type['PER_DESC']])

    # label tokens according to their presence in an entity
    dr.decorators.reverse_slices('entities', 'tokens', 'token_span', pointer_attr='entity', offset_attr='entity_offset', mark_outside=True)(doc)
    self.assertEqual('BIOOOOOBOOOBOOO', ''.join('O' if not tok.entity else ('I' if tok.entity_offset else 'B') for tok in doc.tokens))
