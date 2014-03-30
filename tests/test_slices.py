# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr
import six


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

    correct = six.BytesIO()
    correct.write(
    b'\x02'
    b'\x93'
      b'\x92'
        b'\xa8__meta__'
        b'\x90'
      b'\x92'
        b'\xa4Sent'
        b'\x92'
          b'\x81\x00\xa6number'
          b'\x83\x00\xa4span\x01\x01\x02\xc0'
      b'\x92'
        b'\xa5Token'
        b'\x92'
          b'\x81\x00\xa3raw'
          b'\x82\x00\xa4span\x02\xc0'
    b'\x92'
      b'\x93\xa5sents\x01\x02'
      b'\x93\xa6tokens\x02\x0a'
    b'\x01'
      b'\x80'
    b'\x0b'
      b'\x92'
        b'\x81\x01\x92\x00\x05'
        b'\x81\x01\x92\x05\x05'
    b'\x66'
      b'\x9a'
        b'\x82\x00\xa3The\x01\x92\x00\x03'
        b'\x82\x00\xa5quick\x01\x92\x04\x05'
        b'\x82\x00\xa5brown\x01\x92\x0b\x05'
        b'\x82\x00\xa3fox\x01\x92\x11\x03'
        b'\x82\x00\xa1.\x01\x92\x14\x01'
        b'\x82\x00\xa3The\x01\x92\x16\x03'
        b'\x82\x00\xa4lazy\x01\x92\x1a\x04'
        b'\x82\x00\xa3cat\x01\x92\x1f\x03'
        b'\x82\x00\xa3too\x01\x92\x23\x03'
        b'\x82\x00\xa1.\x01\x92\x26\x01'
    )

    out = six.BytesIO()
    writer = dr.Writer(out, Doc)
    writer.write(doc)

    out = out.getvalue()
    correct = correct.getvalue()
    self.assertEqual(out, correct)
