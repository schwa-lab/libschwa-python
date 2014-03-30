# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import tokenizer
import six


INPUT = r'''
<h1>This is a page title</h1>
<p>Once upon a time, there was a "sentence" with:</p>
<ul>
  <li>One dot point</li>
  <li>And another dot point</li>
</ul>
<p>It has a concluding paragraph too. With more than one sentence. Tschüß. 再见。</p>
'''.strip()


class TestCase__callback_object(unittest.TestCase):
  METHODS = (
      b'begin_sentence',
      b'end_sentence',
      b'begin_paragraph',
      b'end_paragraph',
      b'begin_heading',
      b'end_heading',
      b'begin_list',
      b'end_list',
      b'begin_item',
      b'end_item',
      b'begin_document',
      b'end_document',
      b'add',
      b'error',
  )

  def setUp(self):
    self.tokenizer = tokenizer.Tokenizer()
    self.expected_called = {m: True for m in TestCase__callback_object.METHODS}
    self.expected_called[b'error'] = False
    self.maxDiff = 1000

  def test_all_methods(self):
    class X(object):
      def __init__(self):
        self.called = {m: False for m in TestCase__callback_object.METHODS}
        self.raw = self.norm = None
        self.tokens = []

      def begin_sentence(self):
        self.called[b'begin_sentence'] = True

      def end_sentence(self):
        self.called[b'end_sentence'] = True

      def begin_paragraph(self):
        self.called[b'begin_paragraph'] = True

      def end_paragraph(self):
        self.called[b'end_paragraph'] = True

      def begin_heading(self, depth):
        self.called[b'begin_heading'] = True

      def end_heading(self, depth):
        self.called[b'end_heading'] = True

      def begin_list(self):
        self.called[b'begin_list'] = True

      def end_list(self):
        self.called[b'end_list'] = True

      def begin_item(self):
        self.called[b'begin_item'] = True

      def end_item(self):
        self.called[b'end_item'] = True

      def begin_document(self):
        self.called[b'begin_document'] = True

      def end_document(self):
        self.called[b'end_document'] = True

      def add(self, begin, raw, norm=None):
        self.called[b'add'] = True
        if self.raw is None:
          self.raw = raw
        if self.norm is None:
          self.norm = norm
        self.tokens.append((begin, raw, norm))

      def error(self):
        self.called[b'error'] = True

    x = X()
    self.tokenizer.tokenize(INPUT.encode('utf-8'), dest=x)
    self.assertIsNotNone(x.raw)
    self.assertIsInstance(x.raw, six.binary_type)
    self.assertIsNotNone(x.norm)
    self.assertIsInstance(x.norm, six.binary_type)
    self.assertDictEqual(self.expected_called, x.called)
    self.assertEqual(42, len(x.tokens))
    self.assertEqual('再见'.encode('utf-8'), x.tokens[-2][1])

  def test_missing_methods(self):
    class X(object):
      def __init__(self):
        self.called = {m: False for m in TestCase__callback_object.METHODS}
        self.raw = self.norm = None
        self.tokens = []

      def add(self, begin, raw, norm=None):
        self.called[b'add'] = True
        if self.raw is None:
          self.raw = raw
        if self.norm is None:
          self.norm = norm
        self.tokens.append((begin, raw, norm))

      def error(self):
        self.called[b'error'] = True

      def unhandled(self, method_name, *args):
        self.called[method_name] = True

    x = X()
    self.tokenizer.tokenize(INPUT.encode('utf-8'), dest=x)
    self.assertDictEqual(self.expected_called, x.called)
    self.assertEqual(42, len(x.tokens))

  def test_only_unhandled(self):
    class X(object):
      def __init__(self):
        self.called = {m: False for m in TestCase__callback_object.METHODS}
        self.tokens = []
        self.values = []

      def unhandled(self, method_name, *args):
        self.called[method_name] = True
        self.values.append((method_name, args))
        if method_name == b'add':
          if len(args) == 2:
            begin, raw = args
            norm = None
          else:
            begin, raw, norm = args
          self.tokens.append((begin, raw, norm))

    x = X()
    self.tokenizer.tokenize(INPUT.encode('utf-8'), dest=x)
    self.assertEqual(70, len(x.values))
    self.assertDictEqual(self.expected_called, x.called)
    self.assertEqual(42, len(x.tokens))

  def test_invalid(self):
    class X(object):
      pass

    x = X()
    with self.assertRaises(TypeError):
      self.tokenizer.tokenize(INPUT.encode('utf-8'), dest=x)

    class X(object):
      unhandled = b'this is not callable'

    x = X()
    with self.assertRaises(TypeError):
      self.tokenizer.tokenize(INPUT.encode('utf-8'), dest=x)
