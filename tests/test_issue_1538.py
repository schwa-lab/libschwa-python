# vim: set ts=2 et:
"""
Unit test for #
http://schwa.org/issues/1538

Writing a pointer to an object from the incorrect store should raise an exception.
"""
import unittest

from schwa import dr

from utils import write_read


class Foo(dr.Ann):
  val = dr.Field()


class Bar(dr.Ann):
  val = dr.Field()


class Doc(dr.Doc):
  foos = dr.Store(Foo)
  wrong_foos = dr.Store(Foo)
  bars = dr.Store(Bar)
  favourite = dr.Pointer(Foo, store='foos')


class Issue1538Test(unittest.TestCase):
  WRONG_STORE_MSG = r'Cannot serialize pointer to .* not in store .*'

  def setUp(self):
    self.doc = Doc()
    for val in range(5):
      self.doc.foos.create(val=val)
      self.doc.wrong_foos.create(val=val)
      self.doc.bars.create(val=val)

  def test_different_type(self):
    self.doc.favourite = self.doc.bars[2]
    with self.assertRaisesRegexp(ValueError, self.WRONG_STORE_MSG):
      write_read(self.doc, Doc)

  def test_same_type(self):
    self.doc.favourite = self.doc.wrong_foos[2]
    with self.assertRaisesRegexp(ValueError, self.WRONG_STORE_MSG):
      write_read(self.doc, Doc)
