# vim: set et nosi ai ts=2 sts=2 sw=2:
# coding: utf-8
"""
Manual testing of the Writer. Some hand-written serialisations of various
situations.
"""
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from schwa import dr
import six


class DocWithField(dr.Doc):
  name = dr.Field()

  class Meta:
    serial = 'writer.DocWithField'


class DocWithFieldWithSerial(dr.Doc):
  name = dr.Field(serial='filename')

  class Meta:
    serial = 'writer.DocWithFieldWithSerial'


class A(dr.Ann):
  value = dr.Field()

  class Meta:
    serial = 'writer.A'


class Y(dr.Ann):
  p = dr.Pointer(A)

  class Meta:
    serial = 'writer.Y'


class Z(dr.Ann):
  p = dr.Pointer(A, serial='zp')
  value = dr.Field()

  class Meta:
    serial = 'writer.Z'


class DocWithA(dr.Doc):
  as_ = dr.Store(A, serial='as')

  class Meta:
    serial = 'writer.DocWithA'


class DocWithAYZ(dr.Doc):
  as_ = dr.Store(A, serial='as')
  ys = dr.Store(Y)
  zs = dr.Store(Z)

  class Meta:
    serial = 'writer.DocWithAYZ'


# =============================================================================
# unit testing code
# =============================================================================
def serialise(doc, doc_klass):
  f = six.BytesIO()
  dr.Writer(f, doc_klass).write(doc)
  return f.getvalue()


class TestDocWithField(unittest.TestCase):
  def test_nameisnull(self):
    d = DocWithField()
    s = serialise(d, DocWithField)

    correct = six.BytesIO()
    correct.write(b'\x02')  # <wire_version>
    correct.write(b'\x91')  # <klasses>: 1-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa8__meta__')  # <klass_name>: 8-bytes of utf-8 encoded "__meta__"
    correct.write(b'\x91')  # <fields>: 1-element array
    correct.write(b'\x81')  # <field>: 1-element map
    correct.write(b'\x00')  # 0: NAME
    correct.write(b'\xa4name')  # 4-bytes of utf-8 encoded "name"
    correct.write(b'\x90')  # <stores>: 0-element array
    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this
    correct.write(b'\x80')  # <instance>: 0-element map

    self.assertEqual(s, correct.getvalue())

  def test_name(self):
    d = DocWithField(name='/etc/passwd')
    s = serialise(d, DocWithField)

    correct = six.BytesIO()
    correct.write(b'\x02')  # <wire_version>
    correct.write(b'\x91')  # <klasses>: 1-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write(b'\x91')  # <fields>: 1-element array
    correct.write(b'\x81')  # <field>: 1-element map
    correct.write(b'\x00')  # 0: NAME
    correct.write(b'\xa4name')  # utf-8 encoded "name"
    correct.write(b'\x90')  # <stores>: 0-element array
    correct.write(b'\x0e')  # <instance_nbytes>: 14 bytes after this
    correct.write(b'\x81')  # <instance>: 1-element map
    correct.write(b'\x00')  # 0: field number 0 (=> name)
    correct.write(b'\xab/etc/passwd')  # utf-8 encoded "/etc/passwd"

    self.assertEqual(s, correct.getvalue())


class TestDocWithFieldSerial(unittest.TestCase):
  def test_nameisnull(self):
    d = DocWithFieldWithSerial()
    s = serialise(d, DocWithFieldWithSerial)

    correct = six.BytesIO()
    correct.write(b'\x02')  # <wire_version>
    correct.write(b'\x91')  # <klasses>: 1-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write(b'\x91')  # <fields>: 1-element array
    correct.write(b'\x81')  # <field>: 1-element map
    correct.write(b'\x00')  # 0: NAME
    correct.write(b'\xa8filename')  # utf-8 encoded "filename"
    correct.write(b'\x90')  # <stores>: 0-element array
    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this
    correct.write(b'\x80')  # <instance>: 0-element map

    self.assertEqual(s, correct.getvalue())

  def test_name(self):
    d = DocWithFieldWithSerial(name='/etc/passwd')
    s = serialise(d, DocWithFieldWithSerial)

    correct = six.BytesIO()
    correct.write(b'\x02')  # <wire_version>
    correct.write(b'\x91')  # <klasses>: 1-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write(b'\x91')  # <fields>: 1-element array
    correct.write(b'\x81')  # <field>: 1-element map
    correct.write(b'\x00')  # 0: NAME
    correct.write(b'\xa8filename')  # utf-8 encoded "filename"
    correct.write(b'\x90')  # <stores>: 0-element array
    correct.write(b'\x0e')  # <instance_nbytes>: 14 bytes after this
    correct.write(b'\x81')  # <instance>: 1-element map
    correct.write(b'\x00')  # 0: field number 0 (=> name)
    correct.write(b'\xab/etc/passwd')  # utf-8 encoded "/etc/passwd"

    self.assertEqual(s, correct.getvalue())


class TestDocWithA(unittest.TestCase):
  def test_empty(self):
    d = DocWithA()
    s = serialise(d, DocWithA)

    correct = six.BytesIO()
    correct.write(b'\x02')  # <wire_version>
    correct.write(b'\x92')  # <klasses>: 2-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write(b'\x90')  # <fields>: 0-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa8writer.A')  # <klass_name>: utf-8 encoded "writer.A"
    correct.write(b'\x91')  # <fields>: 1-element array
    correct.write(b'\x81')  # <field>: 1-element map
    correct.write(b'\x00')  # 0: NAME
    correct.write(b'\xa5value')  # utf-8 encoded "value"
    correct.write(b'\x91')  # <stores>: 1-element array
    correct.write(b'\x93')  # <store>: 3-element array
    correct.write(b'\xa2as')  # <store_name>: utf-8 encoded "as"
    correct.write(b'\x01')  # <klass_id>: 1
    correct.write(b'\x00')  # <store_nelem>: 0
    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this for the document
    correct.write(b'\x80')  # <instance>: 0-element map
    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this for the "as" store
    correct.write(b'\x90')  # <instance>: 0-element array

    self.assertEqual(s, correct.getvalue())

  def test_four_elements(self):
    d = DocWithA()
    d.as_.create(value='first')
    d.as_.create(value=2)
    d.as_.create()
    d.as_.create(value=True)
    s = serialise(d, DocWithA)

    correct = six.BytesIO()
    correct.write(b'\x02')  # <wire_version>
    correct.write(b'\x92')  # <klasses>: 2-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write(b'\x90')  # <fields>: 0-element array
    correct.write(b'\x92')  # <klass>: 2-element array
    correct.write(b'\xa8writer.A')  # <klass_name>: utf-8 encoded "writer.A"
    correct.write(b'\x91')  # <fields>: 1-element array
    correct.write(b'\x81')  # <field>: 1-element map
    correct.write(b'\x00')  # 0: NAME
    correct.write(b'\xa5value')  # utf-8 encoded "value"
    correct.write(b'\x91')  # <stores>: 1-element array
    correct.write(b'\x93')  # <store>: 3-element array
    correct.write(b'\xa2as')  # <store_name>: utf-8 encoded "as"
    correct.write(b'\x01')  # <klass_id>: 1
    correct.write(b'\x04')  # <store_nelem>: 4
    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this for the document
    correct.write(b'\x80')  # <instance>: 0-element map
    correct.write(b'\x10')  # <instance_nbytes>: 16 byte after this for the "as" store
    correct.write(b'\x94')  # <instance>: 4-element array
    correct.write(b'\x81\x00\xa5first')  # {0: 'first'}
    correct.write(b'\x81\x00\x02')      # {0: 2}
    correct.write(b'\x80')              # {}
    correct.write(b'\x81\x00\xc3')      # {0: True}

    self.assertEqual(s, correct.getvalue())


class TestDocWithAYZ(unittest.TestCase):
  def test_empty(self):
    dschema = DocWithAYZ.schema()
    d = DocWithAYZ()
    s = serialise(d, dschema)

    klass_ids = {}
    for i, ann_schema in enumerate(dschema.klasses()):
      klass_ids[ann_schema.serial] = i + 1
    store_ids = {}
    for i, store_schema in enumerate(dschema.stores()):
      store_ids[store_schema.serial] = i

    correct = six.BytesIO()
    correct.write(b'\x02')  # <wire_version>
    correct.write(b'\x94')  # <klasses>: 4-element array
    correct.write(b'\x92')  # <klass>: 2-element array

    correct.write(b'\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write(b'\x90')  # <fields>: 0-element array

    klass_A = six.BytesIO()
    klass_A.write(b'\x92')  # <klass>: 2-element array
    klass_A.write(b'\xa8writer.A')  # <klass_name>: utf-8 encoded "writer.A"
    klass_A.write(b'\x91')  # <fields>: 1-element array
    klass_A.write(b'\x81')  # <field>: 1-element map
    klass_A.write(b'\x00')  # 0: NAME
    klass_A.write(b'\xa5value')  # utf-8 encoded "value"

    klass_Y = six.BytesIO()
    klass_Y.write(b'\x92')  # <klass>: 2-element array
    klass_Y.write(b'\xa8writer.Y')  # <klass_name>: utf-8 encoded "writer.Y"
    klass_Y.write(b'\x91')  # <fields>: 1-element array
    klass_Y.write(b'\x82')  # <field>: 2-element map
    klass_Y.write(b'\x00')  # 0: NAME
    klass_Y.write(b'\xa1p')  # utf-8 encoded "p"
    klass_Y.write(b'\x01')  # 1: POINTER_TO
    klass_Y.write(six.int2byte(store_ids['as']))  # <store_id>

    klass_Z = six.BytesIO()
    klass_Z.write(b'\x92')  # <klass>: 2-element array
    klass_Z.write(b'\xa8writer.Z')  # <klass_name>: utf-8 encoded "writer.Z"
    klass_Z.write(b'\x92')  # <fields>: 2-element array
    klass_Z.write(b'\x82')  # <field>: 2-element map
    klass_Z.write(b'\x00')  # 0: NAME
    klass_Z.write(b'\xa2zp')  # utf-8 encoded "zp"
    klass_Z.write(b'\x01')  # 1: POINTER_TO
    klass_Z.write(six.int2byte(store_ids['as']))  # <store_id>
    klass_Z.write(b'\x81')  # <field>: 1-element map
    klass_Z.write(b'\x00')  # 0: NAME
    klass_Z.write(b'\xa5value')  # utf-8 encoded "value"

    correct_klasses = {
        'writer.A': klass_A,
        'writer.Y': klass_Y,
        'writer.Z': klass_Z,
    }
    for i, ann_schema in enumerate(dschema.klasses()):
      correct.write(correct_klasses[ann_schema.serial].getvalue())

    correct.write(b'\x93')  # <stores>: 3-element array

    store_as = six.BytesIO()
    store_as.write(b'\x93')  # <store>: 3-element array
    store_as.write(b'\xa2as')  # <store_name>: utf-8 encoded "as"
    store_as.write(six.int2byte(klass_ids['writer.A']))  # <klass_id>
    store_as.write(b'\x00')  # <store_nelem>: 0

    store_ys = six.BytesIO()
    store_ys.write(b'\x93')  # <store>: 3-element array
    store_ys.write(b'\xa2ys')  # <store_name>: utf-8 encoded "ys"
    store_ys.write(six.int2byte(klass_ids['writer.Y']))  # <klass_id>
    store_ys.write(b'\x00')  # <store_nelem>: 0

    store_zs = six.BytesIO()
    store_zs.write(b'\x93')  # <store>: 3-element array
    store_zs.write(b'\xa2zs')  # <store_name>: utf-8 encoded "zs"
    store_zs.write(six.int2byte(klass_ids['writer.Z']))  # <klass_id>
    store_zs.write(b'\x00')  # <store_nelem>: 0

    correct_stores = {
        'as': store_as,
        'ys': store_ys,
        'zs': store_zs,
    }
    for store_schema in dschema.stores():
      correct.write(correct_stores[store_schema.serial].getvalue())

    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this for the document
    correct.write(b'\x80')  # <instance>: 0-element map

    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this for the "as" store
    correct.write(b'\x90')  # <instance>: 0-element array

    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this for the "ys" store
    correct.write(b'\x90')  # <instance>: 0-element array

    correct.write(b'\x01')  # <instance_nbytes>: 1 byte after this for the "zs" store
    correct.write(b'\x90')  # <instance>: 0-element array

    self.assertEqual(s, correct.getvalue())
