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
