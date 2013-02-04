# vim: set ts=2 et:
import unittest

from schwa import dr

from utils import write_read

def write_read_other(doc, in_schema):
  return write_read(doc, doc.schema(), in_schema)


class DocWithField(dr.Doc):
  field = dr.Field()


class EmptyDoc(dr.Doc):
  pass


class MyAnn(dr.Ann):
  pass


class DocWithStore(dr.Doc):
  store = dr.Store(MyAnn)


class TestCase(unittest.TestCase):
  def test_required_field(self):
    read_schema = DocWithField.schema()
    self._set_schema_flag(read_schema.fields(), 'field', 'read_required')

    with self.assertRaises(dr.ReaderException):
      write_read_other(EmptyDoc(), read_schema)
    write_read_other(DocWithField(), read_schema)

  def test_prohibited_field(self):
    read_schema = DocWithField.schema()
    self._set_schema_flag(read_schema.fields(), 'field', 'read_prohibited')

    write_read_other(EmptyDoc(), read_schema)
    with self.assertRaises(dr.ReaderException):
      write_read_other(DocWithField(), read_schema)

  def test_required_store(self):
    read_schema = DocWithStore.schema()
    self._set_schema_flag(read_schema.stores(), 'store', 'read_required')

    with self.assertRaises(dr.ReaderException):
      write_read_other(EmptyDoc(), read_schema)
    write_read_other(DocWithStore(), read_schema)

  def test_prohibited_store(self):
    read_schema = DocWithStore.schema()
    self._set_schema_flag(read_schema.stores(), 'store', 'read_prohibited')

    write_read_other(EmptyDoc(), read_schema)
    with self.assertRaises(dr.ReaderException):
      write_read_other(DocWithStore(), read_schema)

  @staticmethod
  def _set_schema_flag(iter, name, attr):
    for subschema in iter:
      if subschema.name == name:
        getattr(subschema, 'set_' + attr)()
        break
    else:
      raise Exception('Expected to find field named `field`')
