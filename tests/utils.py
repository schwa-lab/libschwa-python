# vim: set ts=2 et:
from cStringIO import StringIO

from schwa import dr


def write_read(doc, out_schema, in_schema=None):
  if in_schema is None:
    in_schema = out_schema
  print 'Writing {0}'.format(out_schema)
  f = StringIO()
  dr.Writer(f, out_schema).write(doc)
  f.seek(0)
  print 'Reading {0}'.format(in_schema)
  return dr.Reader(in_schema).stream(f).next()
