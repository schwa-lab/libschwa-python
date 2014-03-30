/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#include "seq_stream.h"


namespace schwa {
namespace tokenizer {

// ============================================================================
// PySeqStream
// ============================================================================
PySeqStream::~PySeqStream(void) {
  for (PyObject *obj : _paragraphs)
    Py_DECREF(obj);
  for (PyObject *obj : _sentences)
    Py_DECREF(obj);
  for (PyObject *obj : _tokens)
    Py_DECREF(obj);
}


void
PySeqStream::add(Type type, const char *raw, size_t begin, size_t len, const char *norm) {
  const Py_ssize_t pybegin = begin;
  const Py_ssize_t pylen = len;

#ifdef IS_PY3K
  const char *const fmt = "ny#y";
#else
  const char *const fmt = "ns#s";
#endif
  PyObject *const tuple = Py_BuildValue(fmt, pybegin, raw, pylen, norm);
  _tokens.push_back(tuple);
}


PyObject *
PySeqStream::return_value(void) {
  PyObject *seq = vector2seq(_paragraphs);
  _tokens.resize(0);
  _sentences.resize(0);
  _paragraphs.resize(0);
  return seq;
}


void
PySeqStream::end_sentence(void) {
  _sentences.push_back(vector2seq(_tokens));
  _tokens.resize(0);
}


void
PySeqStream::end_paragraph(void) {
  _paragraphs.push_back(vector2seq(_sentences));
  _sentences.resize(0);
}

void
PySeqStream::end_list(void) {
  end_paragraph();
}


// ============================================================================
// PyListStream
// ============================================================================
PyObject *
PyListStream::vector2seq(PyVector &vec) const {
  PyObject *list = PyList_New(vec.size());
  Py_ssize_t index = 0;
  for (PyVector::iterator it = vec.begin(); it != vec.end(); ++it, ++index)
    PyList_SET_ITEM(list, index, *it);
  return list;
}


// ============================================================================
// PyTupleStream
// ============================================================================
PyObject *
PyTupleStream::vector2seq(PyVector &vec) const {
  PyObject *tuple = PyTuple_New(vec.size());
  Py_ssize_t index = 0;
  for (PyVector::iterator it = vec.begin(); it != vec.end(); ++it, ++index)
    PyTuple_SET_ITEM(tuple, index, *it);
  return tuple;
}

}  // namespace tokenizer
}  // namespace schwa;
