# vim: set ts=2 et:
"""
Tests ensuring that what is written out is identical to what is read in.
"""
from unittest import TestCase

from schwa import dr

from utils import write_read


class Annot(dr.Ann):
  pass


class DocWithoutFields(dr.Doc):
  pass


class DocWithField(dr.Doc):
  field = dr.Field()


class DocWithAnnotsAndPointer(dr.Doc):
  annots = dr.Store(Annot)
  special_annot = dr.Pointer(Annot)


class SameModelTests(TestCase):
  def test_pointer(self):
    doc = DocWithAnnotsAndPointer()
    doc.annots.create()
    self.assertEquals(len(doc.annots), 1)
    doc.special_annot = doc.annots[0]
    doc = write_read(doc, DocWithAnnotsAndPointer)
    self.assertIs(doc.special_annot, doc.annots[0])

  def test_null_pointer(self):
    doc = DocWithAnnotsAndPointer()
    doc.annots.create()
    doc.special_annot = None
    doc = write_read(doc, DocWithAnnotsAndPointer)
    self.assertIsNone(doc.special_annot)


class DifferentModelTests(TestCase):
  """
  Tests casting from one model to another via (de)serialisation
  """
  def test_various(self):
    doc = DocWithField()
    doc = write_read(doc, DocWithField)
    doc.field = 'foo'
    doc = write_read(doc, DocWithField, DocWithoutFields)
    doc = write_read(doc, DocWithoutFields, DocWithAnnotsAndPointer)
    doc.annots.create()
    doc.special_annot = doc.annots[-1]
    doc = write_read(doc, DocWithAnnotsAndPointer, DocWithoutFields)
    doc = write_read(doc, DocWithoutFields, DocWithField)
    self.assertEquals(doc.field, 'foo')
    doc = write_read(doc, DocWithField, DocWithoutFields)
    doc = write_read(doc, DocWithoutFields, DocWithAnnotsAndPointer)
    self.assertEquals(len(doc.annots), 1)
    self.assertEquals(doc.special_annot, doc.annots[0])
