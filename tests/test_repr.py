# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr


class MyAnn(dr.Ann):
  foo = dr.Field()
  others = dr.SelfPointers()
  prev = dr.SelfPointer()


class SpecialisedReprAnn(dr.Ann):
  def __repr__(self):
    return 'Yo!'


class MyDoc(dr.Doc):
  b = dr.Field()
  a = dr.Field()
  _c = dr.Field(serial='c')
  sl = dr.Slice()
  anns = dr.Store(MyAnn)
  more_anns = dr.Store(MyAnn)
  specialised_repr_anns = dr.Store(SpecialisedReprAnn)


class TestCase(unittest.TestCase):
  def test_hides_defaults(self):
    d = MyDoc()
    self.assertEqual(repr(d), 'MyDoc()')
    d.anns.create()
    self.assertEqual(repr(d), 'MyDoc(anns=[MyAnn()])')

  def test_list(self):
    d = MyDoc()
    d.anns.create_n(3)
    s = repr(d)
    self.assertEqual(repr(d), 'MyDoc(anns=[MyAnn(), MyAnn(), MyAnn()])')

  def test_list_ellipsis(self):
    d = MyDoc()
    d.anns.create_n(4000)
    s = repr(d)
    self.assertTrue(len(s) < 1000)
    self.assertTrue('...]' in s)

  def test_sorting(self):
    # Fields in alphabetical order, stores in alphabetical order
    d = MyDoc(b=5, a=6)
    d.anns.create()
    d.more_anns.create()
    self.assertEqual(repr(d), 'MyDoc(a=6, b=5, anns=[MyAnn()], more_anns=[MyAnn()])')

  def test_serial(self):
    d = MyDoc(_c=10)
    self.assertEqual(repr(d), 'MyDoc(_c=10)')

  def test_slice(self):
    # Slices should have step hidden
    d = MyDoc(sl=slice(5, 6))
    self.assertEqual(repr(d), 'MyDoc(sl=slice(5, 6))')

  def test_limited_nesting(self):
    d = MyDoc()
    d.anns.create_n(3)
    for i, a in enumerate(d.anns):
      a.foo = i
      a.prev = d.anns[i - 1]
    self.assertEqual(repr(d), 'MyDoc(anns=[MyAnn(foo=0, prev=MyAnn(...)), MyAnn(foo=1, prev=MyAnn(...)), MyAnn(foo=2, prev=MyAnn(...))])')
    self.assertEqual(repr(d.anns[0]), 'MyAnn(foo=0, prev=MyAnn(foo=2, prev=MyAnn(...)))')

  def test_pointer_lists(self):
    d = MyDoc()
    d.anns.create_n(3)
    for i, a in enumerate(d.anns):
      a.foo = i
    d.anns[0].others = d.anns[1:]
    self.assertEqual(repr(d.anns[0]), 'MyAnn(foo=0, others=[MyAnn(foo=1), MyAnn(foo=2)])')

  def test_overwritten_repr(self):
    d = MyDoc()
    d.specialised_repr_anns.create()
    self.assertEqual(repr(d), 'MyDoc(specialised_repr_anns=[Yo!])')
