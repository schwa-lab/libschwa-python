# vim: set ts=2 et:
import unittest

from schwa import dr
from schwa.dr.exceptions import WriterException

from utils import write_read


class Foo(dr.Ann):
  label = dr.Field()
  other = dr.Pointer('Foo')

  class Meta:
    name = 'Foo'


class Doc(dr.Doc):
  foos = dr.Store(Foo)


class TestDoc(unittest.TestCase):
  def test_sorting(self):
    d = Doc()

    f1 = d.foos.create(label='1')
    f2 = d.foos.create(label='2')
    f3 = d.foos.create(label='3')
    f4 = d.foos.create(label='4')
    d.foos.sort(key=lambda f: f.label, reverse=True)
    f1.other = f3
    f2.other = f1
    f3.other = f2
    f4.other = f4

    d = write_read(d, Doc)

    self.assertEqual(len(d.foos), 4)
    f1, f2, f3, f4 = d.foos
    self.assertEqual(f1.label, '4')
    self.assertEqual(f2.label, '3')
    self.assertEqual(f3.label, '2')
    self.assertEqual(f4.label, '1')
    self.assertIs(f1.other, f1)
    self.assertIs(f2.other, f3)
    self.assertIs(f3.other, f4)
    self.assertIs(f4.other, f2)

  def test_deletion(self):
    d = Doc()

    d.foos.create(label='1')
    d.foos.create(label='2')
    d.foos.create(label='3')
    d.foos.create(label='4')
    del d.foos[2:4]

    d = write_read(d, Doc)

    self.assertEqual(len(d.foos), 2)
    f1, f2 = d.foos
    self.assertEqual(f1.label, '1')
    self.assertEqual(f2.label, '2')

  def test_deletion_bad(self):
    d = Doc()

    f1 = d.foos.create(label='1')
    f2 = d.foos.create(label='2')
    f3 = d.foos.create(label='3')
    f4 = d.foos.create(label='4')
    f1.other = f4
    f2.other = f4
    f3.other = f4
    del d.foos[3]

    R = 'Cannot serialize pointer to .* as it is not not in any store'
    self.assertRaisesRegexp(WriterException, R, lambda: write_read(d, Doc))
