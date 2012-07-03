# vim: set ts=2 et:
import unittest

from schwa import dr

from utils import write_read, write_x_read_y

# TODO: test pointers to renamed stores


class X(dr.Annotation):
  foo = dr.Field(serial='chicken')
  bar = dr.Field()

  class Meta:
    name = 'test_serial.X'


class Doc1(dr.Document):
  name = dr.Field(serial='filename')
  xs = dr.Store(X)

  class Meta:
    name = 'test_serial.Doc1'


class Doc2(dr.Document):
  filename = dr.Field()
  xs = dr.Store(X)

  class Meta:
    name = 'test_serial.Doc2'


class Doc3(dr.Document):
  exes = dr.Store(X, serial='xs')

  class Meta:
    name = 'test_serial.Doc3'


class SerialTest(unittest.TestCase):
  def test_doc1_doc1(self):
    d1 = Doc1(name='test.txt')
    self.assertEqual(len(d1._dr_stores), 1)
    self.assertIn('xs', d1._dr_stores)

    self.assertTrue(hasattr(d1, 'name'))
    self.assertFalse(hasattr(d1, 'filename'))
    self.assertEqual(d1.name, 'test.txt')

    d1.xs.create(foo=1, bar='hello')
    d1.xs.create(foo=10, bar='world')
    d1.xs.create(foo=5)
    d1.xs.create(bar='bar')
    self.assertEqual(len(d1.xs), 4)
    self.assertEqual(len([x for x in d1.xs]), 4)

    for x in d1.xs:
      self.assertEqual(len(x._dr_fields), 2)
      self.assertEqual(len(x._dr_stores), 0)
      self.assertEqual(len(x._dr_s2p), 2)
      self.assertListEqual(sorted(x._dr_fields), ['bar', 'foo'])
      self.assertDictEqual(x._dr_s2p, {'chicken': 'foo', 'bar': 'bar'})
      self.assertTrue(hasattr(x, 'foo'))
      self.assertTrue(hasattr(x, 'bar'))
      self.assertFalse(hasattr(x, 'chicken'))

    d2 = write_read(d1)
    self.assertIsNot(d1, d2)
    self.assertIsInstance(d2, Doc1)

    self.assertTrue(hasattr(d2, 'name'))
    self.assertFalse(hasattr(d2, 'filename'))
    self.assertEqual(d2.name, 'test.txt')

    self.assertEqual(len(d2._dr_stores), 1)
    self.assertIn('xs', d2._dr_stores)
    self.assertEqual(len(d1.xs), len(d2.xs))

    for x in d2.xs:
      self.assertEqual(len(x._dr_fields), 2)
      self.assertEqual(len(x._dr_stores), 0)
      self.assertEqual(len(x._dr_s2p), 2)
      self.assertListEqual(sorted(x._dr_fields), ['bar', 'foo'])
      self.assertDictEqual(x._dr_s2p, {'chicken': 'foo', 'bar': 'bar'})
      self.assertTrue(hasattr(x, 'foo'))
      self.assertTrue(hasattr(x, 'bar'))
      self.assertFalse(hasattr(x, 'chicken'))

  def test_different_doc(self):
    d1 = Doc1()
    d1.xs.create(foo=1, bar='hello')
    d1.xs.create(foo=10, bar='world')
    d1.xs.create(foo=5)
    d1.xs.create(bar='bar')

    d2 = write_x_read_y(d1, Doc2)
    self.assertIsNot(d1, d2)
    self.assertIsInstance(d2, Doc2)

    self.assertEqual(len(d2._dr_stores), 1)
    self.assertIn('xs', d2._dr_stores)
    self.assertEqual(len(d1.xs), len(d2.xs))

    for x in d2.xs:
      self.assertEqual(len(x._dr_fields), 2)
      self.assertEqual(len(x._dr_stores), 0)
      self.assertEqual(len(x._dr_s2p), 2)
      self.assertListEqual(sorted(x._dr_fields), ['bar', 'foo'])
      self.assertDictEqual(x._dr_s2p, {'chicken': 'foo', 'bar': 'bar'})
      self.assertTrue(hasattr(x, 'foo'))
      self.assertTrue(hasattr(x, 'bar'))
      self.assertFalse(hasattr(x, 'chicken'))

  def test_store_serial(self):
    d1 = Doc1()
    d1.xs.create(foo=1, bar='hello')
    d1.xs.create(foo=10, bar='world')
    d1.xs.create(foo=5)
    d1.xs.create(bar='bar')

    d3 = write_x_read_y(d1, Doc3)
    self.assertFalse(hasattr(d3, 'xs'))
    self.assertEqual(len(d3.exes), len(d1.xs))
    for x, y in zip(d3.exes, d1.xs):
      self.assertEqual(x.foo, y.foo)
      self.assertEqual(x.bar, y.bar)

    d1 = write_x_read_y(d3, Doc1)

    self.assertFalse(hasattr(d1, 'exes'))
