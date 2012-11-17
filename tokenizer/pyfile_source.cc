/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#include "pyfile_source.h"


namespace schwa {
namespace io {

PyFileSource::PyFileSource(PyObject *obj) :
    FileSource(PyFile_AsFile(obj)),
    _obj((PyFileObject *)obj) {
  Py_INCREF(_obj);
  PyFile_IncUseCount(_obj);
}

PyFileSource::~PyFileSource(void) {
  PyFile_DecUseCount(_obj);
  Py_DECREF(_obj);
}

}  // namespace io
}  // namespace schwa
