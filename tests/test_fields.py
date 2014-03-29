# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr

from testutils import write_read


class DocWithoutFields(dr.Doc):
  pass


class FieldWithDefault(dr.Field):
  DEFAULT_VALUE = 'some default value'

  def default(self):
    return FieldWithDefault.DEFAULT_VALUE


class DocWithDefaultField(dr.Doc):
  field = FieldWithDefault()


class FieldTests(unittest.TestCase):
  def test_default_field(self):
    doc = DocWithDefaultField()
    self.assertEquals(doc.field, FieldWithDefault.DEFAULT_VALUE)

  def test_default_field_from_wire(self):
    doc = DocWithoutFields()
    doc = write_read(doc, DocWithoutFields, DocWithDefaultField)
    self.assertEquals(doc.field, FieldWithDefault.DEFAULT_VALUE)

  def test_set_default_field_from_wire(self):
    doc = DocWithoutFields()
    doc = write_read(doc, DocWithoutFields, DocWithDefaultField)
    self.assertEquals(doc.field, FieldWithDefault.DEFAULT_VALUE)
    doc.field = b'value'
    doc = write_read(doc, DocWithDefaultField)
    self.assertEquals(doc.field, b'value')
