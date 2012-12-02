# vim: set ts=2 et:
import cStringIO
import unittest

from schwa import dr


class Token(dr.Ann):
  span = dr.Slice()
  norm = dr.Field()
  empty = dr.Field()


class Sent(dr.Ann):
  span = dr.Slice(Token)


class Doc(dr.Doc):
  tokens = dr.Store(Token)
  sents = dr.Store(Sent)
  adjectives = dr.Pointers(Token)
  empty = dr.Field()


def write(out):
  doc1 = Doc()

  doc2 = Doc()
  doc2.tokens.create(span=slice(0, 3), norm='The')
  doc2.tokens.create(span=slice(4, 9), norm='quick')
  doc2.tokens.create(span=slice(11, 16), norm='brown')
  doc2.tokens.create(span=slice(17, 20), norm='fox')
  doc2.tokens.create(span=slice(20, 21), norm='.')
  doc2.sents.create(span=slice(0, 5))
  doc2.adjectives = doc2.tokens[1:3]

  writer = dr.Writer(out, Doc)
  writer.write(doc1)
  writer.write(doc2)


class TestCase(unittest.TestCase):
  def test(self):
    orig = cStringIO.StringIO()
    write(orig)
    orig.seek(0)

    reader = dr.Reader(orig, automagic=True)
    docs = list(reader)
    self.assertEqual(len(docs), 2)

    rewritten = cStringIO.StringIO()
    writer = dr.Writer(rewritten, reader.doc_schema)

    doc = docs[0]
    self.assertTrue(hasattr(doc, 'tokens'))
    self.assertTrue(hasattr(doc, 'sents'))
    self.assertEqual(len(doc.tokens), 0)
    self.assertEqual(len(doc.sents), 0)
    self.assertEqual(doc.adjectives, [])
    writer.write(doc)

    doc = docs[1]
    self.assertTrue(hasattr(doc, 'tokens'))
    self.assertTrue(hasattr(doc, 'sents'))
    self.assertEqual(len(doc.tokens), 5)
    self.assertEqual(len(doc.sents), 1)
    self.assertEqual(doc.tokens[0].norm, 'The')
    self.assertEqual(doc.tokens[0].span, slice(0, 3))
    self.assertEqual(doc.tokens[1].norm, 'quick')
    self.assertEqual(doc.tokens[1].span, slice(4, 9))
    self.assertEqual(doc.tokens[2].norm, 'brown')
    self.assertEqual(doc.tokens[2].span, slice(11, 16))
    self.assertEqual(doc.tokens[3].norm, 'fox')
    self.assertEqual(doc.tokens[3].span, slice(17, 20))
    self.assertEqual(doc.tokens[4].norm, '.')
    self.assertEqual(doc.tokens[4].span, slice(20, 21))
    self.assertEqual(doc.sents[0].span, slice(0, 5))
    self.assertListEqual(doc.adjectives, doc.tokens[1:3])
    writer.write(doc)

    orig.seek(0)
    rewritten.seek(0)
    orig = orig.getvalue()
    rewritten = rewritten.getvalue()
    self.assertEqual(orig, rewritten)

  def test_schema(self):
    orig = cStringIO.StringIO()
    write(orig)
    orig.seek(0)

    reader = dr.Reader(orig, automagic=True)
    docs = list(reader)

    # The following works if reader.doc_schema is replaced with docs[0]._dr_rt.copy_to_schema()
    self.assertSchemaEqual(Doc.schema(), reader.doc_schema)

  def assertSchemaEqual(self, s1, s2, sub_schemas=('klasses', 'stores', 'fields'), fields=('is_pointer', 'is_self_pointer', 'is_slice', 'is_collection', 'pointer_to')):
    fields1 = {}
    fields2 = {}
    for field in fields:
      if hasattr(s1, field):
        fields1[field] = getattr(s1, field)
      if hasattr(s2, field):
        fields2[field] = getattr(s2, field)
    self.assertDictEqual(fields1, fields2)

    for sub_attr in sub_schemas:
      has_sub = hasattr(s1, sub_attr)
      self.assertEqual(has_sub, hasattr(s2, sub_attr))
      if not has_sub:
        continue
      
      subs1 = self._schema_dict(getattr(s1, sub_attr))
      subs2 = self._schema_dict(getattr(s2, sub_attr))
      self.assertSetEqual(set(subs1.keys()), set(subs2.keys()))

      for serial, sub1 in subs1.items():
        self.assertSchemaEqual(sub1, subs2[serial])
  
  @staticmethod
  def _schema_dict(schemas):
    if callable(schemas):
      # handles the annoying discrepancy between schema.klasses and schema.stores()
      schemas = schemas()
    return {obj.serial: obj for obj in schemas}
