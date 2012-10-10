# vim: set ts=2 et:
import unittest

from schwa import dr

from utils import write_read


class Doc1(dr.Doc):
  foo = dr.Field()


class Doc2(Doc1):
  bar = dr.Field()


class TestCase(unittest.TestCase):
  def test(self):
    d = Doc2()
    d.foo = 1
    d.bar = 2

    d = write_read(d, Doc2)

    self.assertEqual(d.foo, 1)
    self.assertEqual(d.bar, 2)
