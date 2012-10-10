# vim: set ts=2 et:
import unittest

from schwa import dr

from utils import write_read


class Ann1(dr.Ann):
  foo = dr.Field()


class Ann2(Ann1):
  bar = dr.Field()


class Doc(dr.Doc):
  ann1s = dr.Store(Ann1)
  ann2s = dr.Store(Ann2)


class TestCase(unittest.TestCase):
  def test(self):
    d = Doc()
    d.ann1s.create(foo='a')
    d.ann2s.create(foo='z', bar=1)

    d = write_read(d, Doc)

    self.assertEqual(len(d.ann1s), 1)
    self.assertEqual(len(d.ann2s), 1)
    self.assertEqual(d.ann1s[0].foo, 'a')
    self.assertEqual(d.ann2s[0].foo, 'z')
    self.assertEqual(d.ann2s[0].bar, 1)
