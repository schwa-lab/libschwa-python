# vim: set ts=2 et:
"""
Unit test for #1501
http://schwa.org/issues/1501

Reading a docrep stream without specifying a doc_klass dies.
"""
from StringIO import StringIO
import unittest

from schwa import dr


class Issue1501Test(unittest.TestCase):
  def test_issue(self):
    dr.AnnotationMeta.clear_cache()

    f = StringIO()
    f.write('\x91\x92\xa8__meta__\x91\x81\x00\xa3foo\x90\x08\x81\x00\xa5hello')
    f.seek(0)

    d = dr.Reader().stream(f).next()
    self.assertIsNotNone(d)
    self.assertEqual(d.foo, 'hello')
