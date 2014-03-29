# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
"""
Unit test for #1542
http://schwa.org/issues/1542

Empty pointer lists should not be serialized.
"""
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr
import six


class X(dr.Ann):
  a = dr.Pointers('X')
  b = dr.SelfPointers()

  class Meta:
    name = 'X'


class Doc(dr.Doc):
  xs = dr.Store(X)


def serialize(doc, schema):
  out = six.BytesIO()
  writer = dr.Writer(out, schema)
  writer.write(doc)
  return out.getvalue()


class TestCase(unittest.TestCase):
  def test_empty(self):
    doc = Doc()
    doc.xs.create()

    actual = serialize(doc, Doc)

    correct = six.BytesIO()
    correct.write(b'\x02')  # <wire_version>
    correct.write(b'\x92')  # <klasses>: 2-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write(b'\x90')  # <fields>: 0-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa1X')  # <klass_name>: utf-8 encoded "X"
    correct.write(b'\x92')  # <fields>: 2-element array
    correct.write(b'\x83')  # <field>: 3-element map
    correct.write(b'\x00')  # 0: NAME
    correct.write(b'\xa1a')  # utf-8 encoded "a"
    correct.write(b'\x01')  # 1: IS_POINTER
    correct.write(b'\x00')  # <store_id>
    correct.write(b'\x04')  # 4: IS_COLLECTION
    correct.write(b'\xc0')  # NIL
    correct.write(b'\x83')  # <field>: 3-element map
    correct.write(b'\x00')  # 0: NAME
    correct.write(b'\xa1b')  # utf-8 encoded "b"
    correct.write(b'\x03')  # 3: IS_SELF_POINTER
    correct.write(b'\xc0')  # NIL
    correct.write(b'\x04')  # 4: IS_COLLECTION
    correct.write(b'\xc0')  # NIL

    correct.write(b'\x91')  # <stores>: 1-element array
    correct.write(b'\x93')  # <store>: 3-element array
    correct.write(b'\xa2xs')  # <store_name>: utf-8 encoded "xs"
    correct.write(b'\x01')  # <klass_id>: 1
    correct.write(b'\x01')  # <store_nelem>: 1

    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this for the document
    correct.write(b'\x80')  # <instance>: 0-element map

    correct.write(b'\x02')  # <instance_nbytes>: 1 byte after this for the "as" store
    correct.write(b'\x91')  # <instances>: 1-element array
    correct.write(b'\x80')  # <instance>: 0-element map

    self.assertEqual(actual, correct.getvalue())
