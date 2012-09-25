# vim: set ts=2 et:
from unittest import TestCase

from schwa import dr

from utils import write_read


class DocWithoutFields(dr.Doc):
  pass


class FieldWithDefault(dr.Field):
  DEFAULT_VALUE = 'some default value'

  def default(self):
    return FieldWithDefault.DEFAULT_VALUE


class DocWithDefaultField(dr.Doc):
  field = FieldWithDefault()


class FieldTests(TestCase):
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
    doc.field = 'value'
    doc = write_read(doc, DocWithDefaultField)
    self.assertEquals(doc.field, 'value')
