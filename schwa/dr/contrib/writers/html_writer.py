# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import collections
import re
import sys
from xml.etree import ElementTree

from schwa import dr
import six
from six.move import xrange

from .writer import AbstractWriter

ENC = 'utf-8'
REMOVE_XML = re.compile(r' *<\?xml[^>]*>\s*<div>')


class NELinkedHTMLWriter(AbstractWriter):
  def __init__(self, f=sys.stdout, doc_attrs=['docid']):
    super(NELinkedHTMLWriter, self).__init__()
    self.f = f
    self.doc_attrs = doc_attrs

  @dr.method_requires_decoration(dr.decorators.reverse_slices('paragraphs', 'sentences', 'span', pointer_attr='paragraph'))
  @dr.method_requires_decoration(dr.decorators.reverse_slices('sentences', 'tokens', 'span', pointer_attr='sentence'))
  def write(self, doc):
    doc_attrs = dict((a, six.text_type(getattr(doc, a))) for a in self.doc_attrs)
    doc_elem = ElementTree.Element('doc', attrib=doc_attrs)
    # TODO Use decorator functions for this...
    sentences_to_paragraphs = collections.defaultdict(list)
    for s in doc.sentences:
      sentences_to_paragraphs[s].append(getattr(s, 'paragraph', None))
    last_t = None
    last_p = None
    text_buffer = []
    for tag, span in (('h1', doc.headline_span), ('h2', doc.byline_span)):
      if span is not None:
        e = ElementTree.Element(tag)
        for s in doc.sentences[span]:
          for t in doc.tokens[s.span]:
            self.padded_append(last_t, t, text_buffer)
            last_t = t
        e.text = ''.join(text_buffer)
        doc_elem.append(e)
      text_buffer = []
      last_t = None
    p_elem = None
    for t in doc.tokens:
      p = sentences_to_paragraphs[t.sentence]
      # Skip headline and byline tokens.
      if p is None or not t.span:
        continue
      if last_p is None or p != last_p:
        # Add collected strings.
        if text_buffer:
          p_elem.text = ''.join(text_buffer)
        p_elem = ElementTree.Element('p')
        doc_elem.append(p_elem)
        text_buffer = []
        last_p = p
      # TODO Handle entities.
      self.padded_append(last_t, t, text_buffer)
      last_t = t
    if text_buffer:
      p_elem.text = ''.join(text_buffer)
    self.f.write(REMOVE_XML.sub('', ElementTree.tostring(doc_elem, ENC)) + '\n')

  def padded_append(self, last_token, token, text_buffer):
      if last_token and last_token.span:
        spaces = token.span.start - last_token.span.stop
      elif last_token:
        spaces = 1
      else:
        spaces = 0
      for i in xrange(spaces):
        text_buffer.append(' ')
      text_buffer.append(token.norm)
