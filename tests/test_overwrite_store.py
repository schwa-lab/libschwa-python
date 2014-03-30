# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr


class Node(dr.Ann):
  label = dr.Field()


class Doc(dr.Doc):
  store = dr.Store(Node)


class Test(unittest.TestCase):
  def _test_example(self, doc):
    doc.store = None

  def test_example(self):
    R = 'Cannot overwrite a store (.*)'

    d = Doc()
    d.store.create()
    self.assertRaisesRegexp(ValueError, R, lambda: self._test_example(d))
