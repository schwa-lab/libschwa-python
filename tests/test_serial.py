# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr

from testutils import write_read

# TODO: test pointers to renamed stores


class X(dr.Ann):
  foo = dr.Field(serial='chicken')
  bar = dr.Field()


class Doc1(dr.Doc):
  name = dr.Field(serial='filename')
  xs = dr.Store(X)


class Doc2(dr.Doc):
  filename = dr.Field()
  xs = dr.Store(X)


class Doc3(dr.Doc):
  exes = dr.Store(X, serial='xs')


class SerialTest(unittest.TestCase):
  def test_doc1_doc1(self):
    d1 = Doc1(name=b'test.txt')
    self.assertEqual(len(d1._dr_stores), 1)
    self.assertIn('xs', d1._dr_stores)

    self.assertTrue(hasattr(d1, 'name'))
    self.assertFalse(hasattr(d1, 'filename'))
    self.assertEqual(d1.name, b'test.txt')

    d1.xs.create(foo=1, bar=b'hello')
    d1.xs.create(foo=10, bar=b'world')
    d1.xs.create(foo=5)
    d1.xs.create(bar=b'bar')
    self.assertEqual(len(d1.xs), 4)
    self.assertEqual(len([x for x in d1.xs]), 4)

    for x in d1.xs:
      self.assertEqual(len(x._dr_fields), 2)
      self.assertEqual(len(x._dr_stores), 0)
      self.assertTrue(hasattr(x, 'foo'))
      self.assertTrue(hasattr(x, 'bar'))
      self.assertFalse(hasattr(x, 'chicken'))

    d2 = write_read(d1, Doc1)
    self.assertIsNot(d1, d2)
    self.assertIsInstance(d2, Doc1)

    self.assertTrue(hasattr(d2, 'name'))
    self.assertFalse(hasattr(d2, 'filename'))
    self.assertEqual(d2.name, b'test.txt')

    self.assertEqual(len(d2._dr_stores), 1)
    self.assertIn('xs', d2._dr_stores)
    self.assertEqual(len(d1.xs), len(d2.xs))

    for x in d2.xs:
      self.assertEqual(len(x._dr_fields), 2)
      self.assertEqual(len(x._dr_stores), 0)
      self.assertTrue(hasattr(x, 'foo'))
      self.assertTrue(hasattr(x, 'bar'))
      self.assertFalse(hasattr(x, 'chicken'))

  def test_different_doc(self):
    d1 = Doc1()
    d1.xs.create(foo=1, bar=b'hello')
    d1.xs.create(foo=10, bar=b'world')
    d1.xs.create(foo=5)
    d1.xs.create(bar=b'bar')

    d2 = write_read(d1, Doc1, Doc2)
    self.assertIsNot(d1, d2)
    self.assertIsInstance(d2, Doc2)

    self.assertEqual(len(d2._dr_stores), 1)
    self.assertIn('xs', d2._dr_stores)
    self.assertEqual(len(d1.xs), len(d2.xs))

    for x in d2.xs:
      self.assertEqual(len(x._dr_fields), 2)
      self.assertEqual(len(x._dr_stores), 0)
      self.assertTrue(hasattr(x, 'foo'))
      self.assertTrue(hasattr(x, 'bar'))
      self.assertFalse(hasattr(x, 'chicken'))

  def test_store_serial(self):
    d1 = Doc1()
    d1.xs.create(foo=1, bar=b'hello')
    d1.xs.create(foo=10, bar=b'world')
    d1.xs.create(foo=5)
    d1.xs.create(bar=b'bar')

    d3 = write_read(d1, Doc1, Doc3)
    self.assertFalse(hasattr(d3, 'xs'))
    self.assertEqual(len(d3.exes), len(d1.xs))
    for x, y in zip(d3.exes, d1.xs):
      self.assertEqual(x.foo, y.foo)
      self.assertEqual(x.bar, y.bar)

    d1 = write_read(d3, Doc3, Doc1)
    self.assertFalse(hasattr(d1, 'exes'))
