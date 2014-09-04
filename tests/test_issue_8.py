# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
"""
Unit test for #8
https://github.com/schwa-lab/libschwa-python/issues/8

Opaque ReaderException when stream and python class names mismatched.
"""
from __future__ import absolute_import, print_function, unicode_literals
import io
import unittest

from schwa import dr
from schwa.dr.exceptions import ReaderException


class Tok(dr.Ann):
  raw = dr.Field()


class DocTok(dr.Doc):
  tokens = dr.Store(Tok)


class Token(dr.Ann):
  raw = dr.Field()


class DocToken(dr.Doc):
  tokens = dr.Store(Token)


class TestCase(unittest.TestCase):
  def test_exception_message(self):
    doc = DocToken()
    t = doc.tokens.create()
    t.raw = 'meow'

    stream = io.BytesIO()
    writer = dr.Writer(stream, DocToken)
    writer.write(doc)

    stream.seek(0)
    reader = dr.Reader(stream, DocTok)
    with self.assertRaisesRegexp(ReaderException, r"Store u?'tokens' points to annotation type u?'.*Tok' but the store on the stream points to a lazy type \(u?'Token'\)\."):
      doc = next(reader)
