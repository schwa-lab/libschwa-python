# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr


class Test(unittest.TestCase):
  def _test_example(self):
    class Node(dr.Ann):
      label = dr.Field()
      children = dr.Store('Node')

      class Meta:
        name = 'Node'

  def test_example(self):
    R = r'Class .* cannot house a Store .* as it is not a Doc subclass'
    self.assertRaisesRegexp(ValueError, R, self._test_example)
