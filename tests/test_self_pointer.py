# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr

from testutils import write_read


class Node(dr.Ann):
  label = dr.Field()
  parent = dr.SelfPointer()
  other = dr.Pointer('Node', store='nodes2')

  def __repr__(self):
    return 'Node({0})'.format(self.label)

  class Meta:
    name = 'Node'


class Doc(dr.Doc):
  nodes1 = dr.Store(Node)
  nodes2 = dr.Store(Node)
  nodes3 = dr.Store(Node)


class TestDoc(unittest.TestCase):
  def test_example(self):
    #    a
    #  b   c
    #  d  e f
    d = Doc()

    n1 = d.nodes3.create(label='1')
    n1.parent = n1

    nA = d.nodes2.create(label='A')
    nB = d.nodes2.create(label='B', parent=nA)
    nC = d.nodes2.create(label='C', parent=nB)
    nD = d.nodes2.create(label='D', parent=nC)
    nA.other = nD
    nB.other = nD
    nC.other = nD
    nD.other = nD

    na = d.nodes1.create(label='a', other=nD)
    nb = d.nodes1.create(label='b', parent=na, other=nC)
    nc = d.nodes1.create(label='c', parent=na, other=nB)
    nd = d.nodes1.create(label='d', parent=nb, other=nA)
    ne = d.nodes1.create(label='e', parent=nc, other=nD)
    nf = d.nodes1.create(label='f', parent=nc, other=nC)

    self.assertEqual(len(d.nodes1), 6)
    self.assertEqual(len(d.nodes2), 4)
    self.assertEqual(len(d.nodes3), 1)
    self.assertIsNone(na.parent)
    self.assertIs(nb.parent, na)
    self.assertIs(nc.parent, na)
    self.assertIs(nd.parent, nb)
    self.assertIs(ne.parent, nc)
    self.assertIs(nf.parent, nc)

    d = write_read(d, Doc)

    self.assertEqual(len(d.nodes1), 6)
    self.assertEqual(len(d.nodes2), 4)
    self.assertEqual(len(d.nodes3), 1)
    na, nb, nc, nd, ne, nf = d.nodes1
    nA, nB, nC, nD = d.nodes2
    n1, = d.nodes3
    self.assertIsNone(na.parent)
    self.assertIs(nb.parent, na)
    self.assertIs(nc.parent, na)
    self.assertIs(nd.parent, nb)
    self.assertIs(ne.parent, nc)
    self.assertIs(nf.parent, nc)
    self.assertIs(na.other, nD)
    self.assertIs(nb.other, nC)
    self.assertIs(nc.other, nB)
    self.assertIs(nd.other, nA)
    self.assertIs(ne.other, nD)
    self.assertIs(nf.other, nC)
    self.assertIs(n1.parent, n1)
    self.assertIsNone(n1.other)
