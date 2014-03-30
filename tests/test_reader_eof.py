# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr
import six


class X(dr.Ann):
  name = dr.Field()


class Doc(dr.Doc):
  xs = dr.Store(X)


def create_stream():
  stream = six.BytesIO()
  writer = dr.Writer(stream, Doc)

  d = Doc()
  for name in ('hello', 'world', '.'):
    d.xs.create(name=name)
  writer.write(d)

  d = Doc()
  for name in ('how', 'are', 'you', '?'):
    d.xs.create(name=name)
  writer.write(d)

  stream.seek(0)
  return stream


class Test(unittest.TestCase):
  def test_empty__iter(self):
    stream = six.BytesIO()
    count = 0
    reader = dr.Reader(stream, Doc)
    for doc in reader:
      self.assertIsNotNone(doc)
      count += 1
    self.assertEquals(count, 0)

  def test_empty__read(self):
    stream = six.BytesIO()
    reader = dr.Reader(stream, Doc)
    doc = reader.read()
    self.assertIsNone(doc)

  def test_nonempty__iter(self):
    stream = create_stream()
    count = 0
    reader = dr.Reader(stream, Doc)
    for doc in reader:
      self.assertIsNotNone(doc)
      count += 1
    self.assertEquals(count, 2)

  def test_nonempty__read(self):
    stream = create_stream()
    reader = dr.Reader(stream, Doc)
    doc = reader.read()
    self.assertIsNotNone(doc)
    doc = reader.read()
    self.assertIsNotNone(doc)
    doc = reader.read()
    self.assertIsNone(doc)
