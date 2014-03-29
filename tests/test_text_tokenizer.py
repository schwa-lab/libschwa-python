# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals
import pprint
import unittest

from schwa import dr
from schwa.dr.contrib.tokenizers import TextTokenizer


INPUT = u'''The cat sat on the dog's mat.
The dog was fat.

So said the cat.'''

OUTPUT = [
    (0, 0, 'The'),
    (0, 0, 'cat'),
    (0, 0, 'sat'),
    (0, 0, 'on'),
    (0, 0, 'the'),
    (0, 0, 'dog'),
    (0, 0, "'s"),
    (0, 0, 'mat'),
    (0, 0, '.'),
    (0, 1, 'The'),
    (0, 1, 'dog'),
    (0, 1, 'was'),
    (0, 1, 'fat'),
    (0, 1, '.'),
    (1, 2, 'So'),
    (1, 2, 'said'),
    (1, 2, 'the'),
    (1, 2, 'cat'),
    (1, 2, '.')
]


class Token(dr.Ann):
  span = dr.Slice()
  raw = dr.Field()
  norm = dr.Field()


class Sentence(dr.Ann):
  span = dr.Slice(Token)


class Paragraph(dr.Ann):
  span = dr.Slice(Sentence)


class Document(dr.Doc):
  tokens = dr.Store(Token)
  sentences = dr.Store(Sentence)
  paragraphs = dr.Store(Paragraph)


sentence_on_tokens = dr.decorators.reverse_slices('sentences', 'tokens', 'span', 'sentence')
paragraphs_on_sentences = dr.decorators.reverse_slices('paragraphs', 'sentences', 'span', 'paragraph')


@dr.requires_decoration(sentence_on_tokens, paragraphs_on_sentences)
def iter_output(doc):
  p_map = dict((p, i) for i, p in enumerate(doc.paragraphs))
  s_map = dict((s, i) for i, s in enumerate(doc.sentences))
  for t in doc.tokens:
    yield (p_map[t.sentence.paragraph], s_map[t.sentence], t.norm)


class TestTokenizer(unittest.TestCase):
  def test(self):
    t = TextTokenizer(Document, Paragraph, Sentence, Token)
    doc = t.tokenize(INPUT)
    out = list(iter_output(doc))
    pprint.pprint(out)
    self.assertEqual(OUTPUT, out)
