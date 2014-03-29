# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr

from testutils import write_read


class SerialTest(unittest.TestCase):
  def test_define(self):
    Foo = dr.make_ann('Foo', 'a', 'b', 'c', 'd', e=dr.Slice(), __module__='SerialTest.test_define')
    self.assertEqual(len(Foo._dr_fields), 5)
    self.assertIn('a', Foo._dr_fields)
    self.assertIsInstance(Foo._dr_fields['a'], dr.Field)
    self.assertIn('b', Foo._dr_fields)
    self.assertIsInstance(Foo._dr_fields['b'], dr.Field)
    self.assertIn('c', Foo._dr_fields)
    self.assertIsInstance(Foo._dr_fields['c'], dr.Field)
    self.assertIn('d', Foo._dr_fields)
    self.assertIsInstance(Foo._dr_fields['d'], dr.Field)
    self.assertIn('e', Foo._dr_fields)
    self.assertIsInstance(Foo._dr_fields['e'], dr.Slice)

  def test_use(self):
    Foo = dr.make_ann('Foo', 'a', 'b', 'c', 'd', e=dr.Slice(), __module__='SerialTest.test_use')

    class Doc(dr.Doc):
      foos = dr.Store(Foo)

      class Meta:
        name = 'SerialTest.test_use.Doc'

    d = Doc()
    d.foos.create(a=1, b=2, c=3, d=4, e=None)
    d.foos.create(a=4, b=3, c=2, d=1, e=slice(10, 21))
    d.foos.create(x='y')

    self.assertEqual(len(d.foos), 3)

    d = write_read(d, Doc)

    self.assertEqual(len(d.foos), 3)
    f1, f2, f3 = d.foos

    self.assertEqual(f1.a, 1)
    self.assertEqual(f1.b, 2)
    self.assertEqual(f1.c, 3)
    self.assertEqual(f1.d, 4)
    self.assertIsNone(f1.e)

    self.assertEqual(f2.a, 4)
    self.assertEqual(f2.b, 3)
    self.assertEqual(f2.c, 2)
    self.assertEqual(f2.d, 1)
    self.assertEqual(f2.e, slice(10, 21))

    self.assertIsNone(f3.a)
    self.assertIsNone(f3.b)
    self.assertIsNone(f3.c)
    self.assertIsNone(f3.d)
    self.assertIsNone(f3.e)

  def test_pointer(self):
    A = dr.make_ann('A', 'x', 'y', z=dr.SelfPointer(), __module__='SerialTest.test_pointer')
    B = dr.make_ann('B', p=dr.Pointer(A), __module__='SerialTest.test_pointer')

    class Doc(dr.Doc):
      sa = dr.Store(A)
      sb = dr.Store(B)

      class Meta:
        name = 'SerialTest.test_pointer.Doc'

    d = Doc()
    a1 = d.sa.create(x=1, y=2, z=None)
    a2 = d.sa.create(x=11, y=21, z=a1)
    d.sb.create(p=None)
    d.sb.create(p=a2)

    d = write_read(d, Doc)

    self.assertEqual(len(d.sa), 2)
    self.assertEqual(len(d.sb), 2)
    a1, a2 = d.sa
    b1, b2 = d.sb

    self.assertEqual(a1.x, 1)
    self.assertEqual(a1.y, 2)
    self.assertIsNone(a1.z)

    self.assertEqual(a2.x, 11)
    self.assertEqual(a2.y, 21)
    self.assertIs(a2.z, a1)

    self.assertIsNone(b1.p)

    self.assertIs(b2.p, a2)
