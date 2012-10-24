# vim: set ts=2 et:
"""
Manual testing of the Writer. Some hand-written serialisations of various
situations.
"""
import cStringIO
import unittest

from schwa import dr


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
  f = cStringIO.StringIO()
  dr.Writer(f, doc_klass).write(doc)
  return f.getvalue()


class TestDocWithField(unittest.TestCase):
  def test_nameisnull(self):
    d = DocWithField()
    s = serialise(d, DocWithField)

    correct = cStringIO.StringIO()
    correct.write('\x02')  # <wire_version>
    correct.write('\x91')  # <klasses>: 1-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa8__meta__')  # <klass_name>: 8-bytes of utf-8 encoded "__meta__"
    correct.write('\x91')  # <fields>: 1-element array
    correct.write('\x81')  # <field>: 1-element map
    correct.write('\x00')  # 0: NAME
    correct.write('\xa4name')  # 4-bytes of utf-8 encoded "name"
    correct.write('\x90')  # <stores>: 0-element array
    correct.write('\x01')  # <instance_nbytes>: 1 byte after this
    correct.write('\x80')  # <instance>: 0-element map

    self.assertEqual(s, correct.getvalue())

  def test_name(self):
    d = DocWithField(name='/etc/passwd')
    s = serialise(d, DocWithField)

    correct = cStringIO.StringIO()
    correct.write('\x02')  # <wire_version>
    correct.write('\x91')  # <klasses>: 1-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write('\x91')  # <fields>: 1-element array
    correct.write('\x81')  # <field>: 1-element map
    correct.write('\x00')  # 0: NAME
    correct.write('\xa4name')  # utf-8 encoded "name"
    correct.write('\x90')  # <stores>: 0-element array
    correct.write('\x0e')  # <instance_nbytes>: 14 bytes after this
    correct.write('\x81')  # <instance>: 1-element map
    correct.write('\x00')  # 0: field number 0 (=> name)
    correct.write('\xab/etc/passwd')  # utf-8 encoded "/etc/passwd"

    self.assertEqual(s, correct.getvalue())


class TestDocWithFieldSerial(unittest.TestCase):
  def test_nameisnull(self):
    d = DocWithFieldWithSerial()
    s = serialise(d, DocWithFieldWithSerial)

    correct = cStringIO.StringIO()
    correct.write('\x02')  # <wire_version>
    correct.write('\x91')  # <klasses>: 1-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write('\x91')  # <fields>: 1-element array
    correct.write('\x81')  # <field>: 1-element map
    correct.write('\x00')  # 0: NAME
    correct.write('\xa8filename')  # utf-8 encoded "filename"
    correct.write('\x90')  # <stores>: 0-element array
    correct.write('\x01')  # <instance_nbytes>: 1 byte after this
    correct.write('\x80')  # <instance>: 0-element map

    self.assertEqual(s, correct.getvalue())

  def test_name(self):
    d = DocWithFieldWithSerial(name='/etc/passwd')
    s = serialise(d, DocWithFieldWithSerial)

    correct = cStringIO.StringIO()
    correct.write('\x02')  # <wire_version>
    correct.write('\x91')  # <klasses>: 1-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write('\x91')  # <fields>: 1-element array
    correct.write('\x81')  # <field>: 1-element map
    correct.write('\x00')  # 0: NAME
    correct.write('\xa8filename')  # utf-8 encoded "filename"
    correct.write('\x90')  # <stores>: 0-element array
    correct.write('\x0e')  # <instance_nbytes>: 14 bytes after this
    correct.write('\x81')  # <instance>: 1-element map
    correct.write('\x00')  # 0: field number 0 (=> name)
    correct.write('\xab/etc/passwd')  # utf-8 encoded "/etc/passwd"

    self.assertEqual(s, correct.getvalue())


class TestDocWithA(unittest.TestCase):
  def test_empty(self):
    d = DocWithA()
    s = serialise(d, DocWithA)

    correct = cStringIO.StringIO()
    correct.write('\x02')  # <wire_version>
    correct.write('\x92')  # <klasses>: 2-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write('\x90')  # <fields>: 0-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa8writer.A')  # <klass_name>: utf-8 encoded "writer.A"
    correct.write('\x91')  # <fields>: 1-element array
    correct.write('\x81')  # <field>: 1-element map
    correct.write('\x00')  # 0: NAME
    correct.write('\xa5value')  # utf-8 encoded "value"
    correct.write('\x91')  # <stores>: 1-element array
    correct.write('\x93')  # <store>: 3-element array
    correct.write('\xa2as')  # <store_name>: utf-8 encoded "as"
    correct.write('\x01')  # <klass_id>: 1
    correct.write('\x00')  # <store_nelem>: 0
    correct.write('\x01')  # <instance_nbytes>: 1 byte after this for the document
    correct.write('\x80')  # <instance>: 0-element map
    correct.write('\x01')  # <instance_nbytes>: 1 byte after this for the "as" store
    correct.write('\x90')  # <instance>: 0-element array

    self.assertEqual(s, correct.getvalue())

  def test_four_elements(self):
    d = DocWithA()
    d.as_.create(value='first')
    d.as_.create(value=2)
    d.as_.create()
    d.as_.create(value=True)
    s = serialise(d, DocWithA)

    correct = cStringIO.StringIO()
    correct.write('\x02')  # <wire_version>
    correct.write('\x92')  # <klasses>: 2-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write('\x90')  # <fields>: 0-element array
    correct.write('\x92')  # <klass>: 2-element array
    correct.write('\xa8writer.A')  # <klass_name>: utf-8 encoded "writer.A"
    correct.write('\x91')  # <fields>: 1-element array
    correct.write('\x81')  # <field>: 1-element map
    correct.write('\x00')  # 0: NAME
    correct.write('\xa5value')  # utf-8 encoded "value"
    correct.write('\x91')  # <stores>: 1-element array
    correct.write('\x93')  # <store>: 3-element array
    correct.write('\xa2as')  # <store_name>: utf-8 encoded "as"
    correct.write('\x01')  # <klass_id>: 1
    correct.write('\x04')  # <store_nelem>: 4
    correct.write('\x01')  # <instance_nbytes>: 1 byte after this for the document
    correct.write('\x80')  # <instance>: 0-element map
    correct.write('\x10')  # <instance_nbytes>: 16 byte after this for the "as" store
    correct.write('\x94')  # <instance>: 4-element array
    correct.write('\x81\x00\xa5first')  # {0: 'first'}
    correct.write('\x81\x00\x02')      # {0: 2}
    correct.write('\x80')              # {}
    correct.write('\x81\x00\xc3')      # {0: True}

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

    correct = cStringIO.StringIO()
    correct.write('\x02')  # <wire_version>
    correct.write('\x94')  # <klasses>: 4-element array
    correct.write('\x92')  # <klass>: 2-element array

    correct.write('\xa8__meta__')  # <klass_name>: utf-8 encoded "__meta__"
    correct.write('\x90')  # <fields>: 0-element array

    klass_A = cStringIO.StringIO()
    klass_A.write('\x92')  # <klass>: 2-element array
    klass_A.write('\xa8writer.A')  # <klass_name>: utf-8 encoded "writer.A"
    klass_A.write('\x91')  # <fields>: 1-element array
    klass_A.write('\x81')  # <field>: 1-element map
    klass_A.write('\x00')  # 0: NAME
    klass_A.write('\xa5value')  # utf-8 encoded "value"

    klass_Y = cStringIO.StringIO()
    klass_Y.write('\x92')  # <klass>: 2-element array
    klass_Y.write('\xa8writer.Y')  # <klass_name>: utf-8 encoded "writer.Y"
    klass_Y.write('\x91')  # <fields>: 1-element array
    klass_Y.write('\x82')  # <field>: 2-element map
    klass_Y.write('\x00')  # 0: NAME
    klass_Y.write('\xa1p')  # utf-8 encoded "p"
    klass_Y.write('\x01')  # 1: POINTER_TO
    klass_Y.write(chr(store_ids['as']))  # <store_id>

    klass_Z = cStringIO.StringIO()
    klass_Z.write('\x92')  # <klass>: 2-element array
    klass_Z.write('\xa8writer.Z')  # <klass_name>: utf-8 encoded "writer.Z"
    klass_Z.write('\x92')  # <fields>: 2-element array
    klass_Z.write('\x82')  # <field>: 2-element map
    klass_Z.write('\x00')  # 0: NAME
    klass_Z.write('\xa2zp')  # utf-8 encoded "zp"
    klass_Z.write('\x01')  # 1: POINTER_TO
    klass_Z.write(chr(store_ids['as']))  # <store_id>
    klass_Z.write('\x81')  # <field>: 1-element map
    klass_Z.write('\x00')  # 0: NAME
    klass_Z.write('\xa5value')  # utf-8 encoded "value"

    correct_klasses = {
      'writer.A': klass_A,
      'writer.Y': klass_Y,
      'writer.Z': klass_Z,
    }
    for i, ann_schema in enumerate(dschema.klasses()):
      correct.write(correct_klasses[ann_schema.serial].getvalue())

    correct.write('\x93')  # <stores>: 3-element array

    store_as = cStringIO.StringIO()
    store_as.write('\x93')  # <store>: 3-element array
    store_as.write('\xa2as')  # <store_name>: utf-8 encoded "as"
    store_as.write(chr(klass_ids['writer.A']))  # <klass_id>
    store_as.write('\x00')  # <store_nelem>: 0

    store_ys = cStringIO.StringIO()
    store_ys.write('\x93')  # <store>: 3-element array
    store_ys.write('\xa2ys')  # <store_name>: utf-8 encoded "ys"
    store_ys.write(chr(klass_ids['writer.Y']))  # <klass_id>
    store_ys.write('\x00')  # <store_nelem>: 0

    store_zs = cStringIO.StringIO()
    store_zs.write('\x93')  # <store>: 3-element array
    store_zs.write('\xa2zs')  # <store_name>: utf-8 encoded "zs"
    store_zs.write(chr(klass_ids['writer.Z']))  # <klass_id>
    store_zs.write('\x00')  # <store_nelem>: 0

    correct_stores = {
      'as': store_as,
      'ys': store_ys,
      'zs': store_zs,
    }
    for store_schema in dschema.stores():
      correct.write(correct_stores[store_schema.serial].getvalue())

    correct.write('\x01')  # <instance_nbytes>: 1 byte after this for the document
    correct.write('\x80')  # <instance>: 0-element map

    correct.write('\x01')  # <instance_nbytes>: 1 byte after this for the "as" store
    correct.write('\x90')  # <instance>: 0-element array

    correct.write('\x01')  # <instance_nbytes>: 1 byte after this for the "ys" store
    correct.write('\x90')  # <instance>: 0-element array

    correct.write('\x01')  # <instance_nbytes>: 1 byte after this for the "zs" store
    correct.write('\x90')  # <instance>: 0-element array

    self.assertEqual(s, correct.getvalue())
