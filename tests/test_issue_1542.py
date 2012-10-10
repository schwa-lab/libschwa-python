# vim: set ts=2 et:
"""
Unit test for #1542
http://schwa.org/issues/1542

Empty pointer lists should not be serialized.
"""
import cStringIO
import unittest

from schwa import dr


class X(dr.Ann):
  a = dr.Pointers('X')
  b = dr.SelfPointers()

  class Meta:
    name = 'X'


class Doc(dr.Doc):
  xs = dr.Store(X)


def serialize(doc, schema):
  out = cStringIO.StringIO()
  writer = dr.Writer(out, schema)
  writer.write(doc)
  return out.getvalue()


class TestCase(unittest.TestCase):
  def test_empty(self):
    doc = Doc()
    doc.xs.create()

    actual = serialize(doc, Doc)

    correct = cStringIO.StringIO()
    correct.write('\x02')  # <wire_version>
    correct.write('\x92')  # <klasses>: 2-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write('\x90')  # <fields>: 0-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa1X')  # <klass_name>: utf-8 encoded "X"
    correct.write('\x92')  # <fields>: 2-element array
    correct.write('\x83')  # <field>: 3-element map
    correct.write('\x00')  # 0: NAME
    correct.write('\xa1a')  # utf-8 encoded "a"
    correct.write('\x01')  # 1: IS_POINTER
    correct.write('\x00')  # <store_id>
    correct.write('\x04')  # 4: IS_COLLECTION
    correct.write('\xc0')  # NIL
    correct.write('\x83')  # <field>: 3-element map
    correct.write('\x00')  # 0: NAME
    correct.write('\xa1b')  # utf-8 encoded "b"
    correct.write('\x03')  # 3: IS_SELF_POINTER
    correct.write('\xc0')  # NIL
    correct.write('\x04')  # 4: IS_COLLECTION
    correct.write('\xc0')  # NIL

    correct.write('\x91')  # <stores>: 1-element array
    correct.write('\x93')  # <store>: 3-element array
    correct.write('\xa2xs')  # <store_name>: utf-8 encoded "xs"
    correct.write('\x01')  # <klass_id>: 1
    correct.write('\x01')  # <store_nelem>: 1

    correct.write('\x01')  # <instance_nbytes>: 1 byte after this for the document
    correct.write('\x80')  # <instance>: 0-element map

    correct.write('\x02')  # <instance_nbytes>: 1 byte after this for the "as" store
    correct.write('\x91')  # <instances>: 1-element array
    correct.write('\x80')  # <instance>: 0-element map

    self.assertEqual(actual, correct.getvalue())
