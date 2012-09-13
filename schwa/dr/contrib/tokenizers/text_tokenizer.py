#!/usr/bin/env python
# vim: set ts=2 et:

import logging
from operator import attrgetter
from schwa import dr, tokenizer

log = logging.getLogger()

ENC = 'utf-8'

class TextTokenizer(object):
  def __init__(self, document_klass, paragraph_klass, sentence_klass, token_klass, save_paragraphs=True, save_sentences=True, save_spans=True):
    self.save_paragraphs = save_paragraphs
    self.save_sentences = save_sentences
    self.save_spans = save_spans
    self.tokenizer = tokenizer.Tokenizer()
    self.document_klass = document_klass
    self.paragraph_klass = paragraph_klass
    self.sentence_klass = sentence_klass
    self.token_klass = token_klass

  def tokenize(self, text):
    assert isinstance(text, unicode)
    self.offset = 0
    self.doc = self.document_klass()
    self.tokenizer.tokenize(text.encode(ENC), dest=self)
    return self.doc

  def unhandled(self, method_name):
    log.info('%r unhandled during tokenization' % method_name)

  def error(self, start, raw):
    log.error('Error processing %r at %d' % (raw, start))

  def add(self, start, raw, norm=None):
    if self.save_spans:
      span = slice(self.offset + start, self.offset + start + len(raw))
    else:
      span = None
    norm = self.fix_token_norm(norm or raw)
    tok = self.token_klass(span=span, raw=raw if norm != raw else None, norm=norm)
    self.doc.tokens.append(tok)

  def fix_token_norm(self, norm):
    return norm

  def len(self, annot='tokens'):
    return len(getattr(self.doc, annot))

  def begin_sentence(self):
    if self.save_sentences:
      self.sent_start = self.len()

  def end_sentence(self):
    if self.save_sentences:
      a = self.sentence_klass(span=slice(self.sent_start, self.len()))
      self.doc.sentences.append(a)
      delattr(self, 'sent_start')

  def begin_paragraph(self):
    if self.save_paragraphs:
      self.para_start = self.len('sentences')

  def end_paragraph(self):
    if self.save_paragraphs:
      a = self.paragraph_klass(span=slice(self.para_start, self.len('sentences')))
      self.doc.paragraphs.append(a)
      delattr(self, 'para_start')
