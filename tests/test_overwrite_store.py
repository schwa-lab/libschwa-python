# vim: set ts=2 et:
import unittest

from schwa import dr


class Node(dr.Ann):
  label = dr.Field()


class Doc(dr.Doc):
  store = dr.Store(Node)


class Test(unittest.TestCase):
  def _test_example(self, doc):
    doc.store = None

  def test_example(self):
    R = 'Cannot overwrite a store (.*)'

    d = Doc()
    d.store.create()
    self.assertRaisesRegexp(ValueError, R, lambda: self._test_example(d))
