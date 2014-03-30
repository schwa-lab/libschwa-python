# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import abc
import sys

import six

from .writer import AbstractWriter


class Column(object):
  """ Handles column output, wrapping a function that takes a token, returning the value. """

  def __init__(self, func, id_delimiter='', default=''):
    self.func = func
    self.id_delimiter = id_delimiter
    self.default = default
    self.flush()

  def __call__(self, *args):
    v = self.func(*args)
    if v is None:
      v = self.default
    # Remap the id if there's an id delimiter.
    elif self.id_delimiter:
      v_label, v_id = v.split(self.id_delimiter, 1)
      new_id = self.ids[v_label].get(v_id)
      if new_id is None:
        new_id = len(self.ids[v_label])
        self.ids[v_label][v_id] = new_id
      v = u'%s-%d' % (v_label, new_id)
    return six.text_type(v)

  def flush(self):
    """ Columns should be flushed if ids need to be reset between docs. """
    self.ids = {}


class AbstractColumnWriter(AbstractWriter):
  """ One token per line with other attributes as columns. """
  def __init__(self, columns, output=sys.stdout, delimiter=u'\t', encoding='utf-8', exclude=lambda t: False, between=u'\n'):
    super(AbstractColumnWriter, self).__init__()
    assert all(isinstance(c, Column) for c in columns)
    self.output = output
    self.columns = columns
    self.delimiter = delimiter
    self.encoding = encoding
    self.exclude = exclude
    self.between = between

  def write(self, doc):
    for c in self.columns:
      c.flush()
    lines = []
    self.on_begin_doc(doc, lines)
    lines.extend(self.iter_lines(doc))
    self.on_end_doc(doc, lines)
    d = u'\n'.join(lines) + self.between
    self.output.write(d.encode(self.encoding))

  @abc.abstractmethod
  def iter_lines(self, doc):
    """ Yields lines from the Document. """
    raise NotImplementedError

  def on_begin_doc(self, doc, lines):
    """ Hook for adding lines before a Document. """
    pass

  def on_end_doc(self, doc, lines):
    """ Hook for adding lines after a Document. """
    pass


class SentenceColumnWriter(AbstractColumnWriter):
  """ Writes one line per token. Sentences are split with an empty line. """

  def iter_lines(self, doc):
    for s in doc.sentences:
      for token in doc.tokens[s.span]:
        if self.exclude(token):
          continue
        yield self.delimiter.join(c(token) for c in self.columns)
      yield u''

  def on_begin_doc(self, doc, lines):
    lines.append(u'# begin %s' % doc.docid if hasattr(doc, 'docid') else None)


class NodeColumnWriter(AbstractColumnWriter):
  def iter_lines(self, doc):
    for s in doc.sentences:
      for node in s.parses:
        all_nodes = []
        self._iter_nodes(node, all_nodes)
        for node in all_nodes:
          if self.exclude(node):
            continue
          yield self.delimiter.join(c(doc, node) for c in self.columns)
      yield u''

  def _iter_nodes(self, node, all_nodes):
    all_nodes.append(node)
    for c in node.children:
      self._iter_nodes(c, all_nodes)
