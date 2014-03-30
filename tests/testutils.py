# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from schwa import dr
import six


def write_read(doc, out_schema, in_schema=None):
  if in_schema is None:
    in_schema = out_schema
  print('Writing {0}'.format(out_schema))
  f = six.BytesIO()
  dr.Writer(f, out_schema).write(doc)
  f.seek(0)
  print('Reading {0}'.format(in_schema))
  return dr.Reader(f, in_schema).next()
