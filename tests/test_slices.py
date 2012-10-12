# vim: set ts=2 et:
import cStringIO
import unittest

from schwa import dr


class Token(dr.Ann):
  span = dr.Slice()
  raw = dr.Field()


class Sent(dr.Ann):
  span = dr.Slice(Token)
  number = dr.Field()


class Doc(dr.Doc):
  tokens = dr.Store(Token)
  sents = dr.Store(Sent)


class TestCase(unittest.TestCase):
  def test(self):
    doc = Doc()
    doc.tokens.create(span=slice(0, 3), raw='The')
    doc.tokens.create(span=slice(4, 9), raw='quick')
    doc.tokens.create(span=slice(11, 16), raw='brown')
    doc.tokens.create(span=slice(17, 20), raw='fox')
    doc.tokens.create(span=slice(20, 21), raw='.')
    doc.sents.create(span=slice(0, 5))
    doc.tokens.create(span=slice(22, 25), raw='The')
    doc.tokens.create(span=slice(26, 30), raw='lazy')
    doc.tokens.create(span=slice(31, 34), raw='cat')
    doc.tokens.create(span=slice(35, 38), raw='too')
    doc.tokens.create(span=slice(38, 39), raw='.')
    doc.sents.create(span=slice(5, 10))

    correct = cStringIO.StringIO()
    correct.write(
    '\x02'
    '\x93'
      '\x92'
        '\xa8__meta__'
        '\x90'
      '\x92'
        '\xa5Token'
        '\x92'
          '\x81\x00\xa3raw'
          '\x82\x00\xa4span\x02\xc0'
      '\x92'
        '\xa4Sent'
        '\x92'
          '\x83\x00\xa4span\x01\x00\x02\xc0'
          '\x81\x00\xa6number'
    '\x92'
      '\x93\xa6tokens\x01\x0a'
      '\x93\xa5sents\x02\x02'
    '\x01'
      '\x80'
    '\x66'
      '\x9a'
        '\x82\x00\xa3The\x01\x92\x00\x03'
        '\x82\x00\xa5quick\x01\x92\x04\x05'
        '\x82\x00\xa5brown\x01\x92\x0b\x05'
        '\x82\x00\xa3fox\x01\x92\x11\x03'
        '\x82\x00\xa1.\x01\x92\x14\x01'
        '\x82\x00\xa3The\x01\x92\x16\x03'
        '\x82\x00\xa4lazy\x01\x92\x1a\x04'
        '\x82\x00\xa3cat\x01\x92\x1f\x03'
        '\x82\x00\xa3too\x01\x92\x23\x03'
        '\x82\x00\xa1.\x01\x92\x26\x01'
    '\x0b'
      '\x92'
        '\x81\x00\x92\x00\x05'
        '\x81\x00\x92\x05\x05'
    )

    out = cStringIO.StringIO()
    writer = dr.Writer(out, Doc)
    writer.write(doc)

    out = out.getvalue()
    correct = correct.getvalue()
    self.assertEqual(out, correct)
