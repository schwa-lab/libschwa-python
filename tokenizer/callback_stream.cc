/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#define PY_SSIZE_T_CLEAN

#include "callback_stream.h"

#include "exception.h"


namespace schwa {
namespace tokenizer {

// ============================================================================
// PyCallObjectStream
// ============================================================================
PyCallObjectStream::PyCallObjectStream(PyObject *obj) : _obj(obj) {
  Py_INCREF(_obj);
}

PyCallObjectStream::~PyCallObjectStream(void) {
  Py_DECREF(_obj);
}


bool
PyCallObjectStream::is_handled(const char* method) {
  if (PyObject_HasAttrString(_obj, method))
    return true;
  if (PyObject_HasAttrString(_obj, "unhandled"))
    PyObject_CallMethod(_obj, (char *)"unhandled", (char *)"s", method);
  return false;
}


void
PyCallObjectStream::call(const char *method) {
  if (!is_handled(method))
    return;
  if (!PyObject_CallMethod(_obj, (char *)method, 0))
    throw PyRaise();
}


void
PyCallObjectStream::call_i(const char *method, const int i) {
  if (!is_handled(method))
    return;
  if (!PyObject_CallMethod(_obj, (char *)method, (char *)"i", i))
    throw PyRaise();
}


PyObject *
PyCallObjectStream::get(void) {
  Py_RETURN_NONE;
}


void
PyCallObjectStream::add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm) {
  if (!is_handled("add"))
    return;

  const Py_ssize_t pybegin = begin;
  const Py_ssize_t pylen = len;
  if (norm)
    PyObject_CallMethod(_obj, (char *)"add", (char *)"ns#s", pybegin, raw, pylen, norm);
  else
    PyObject_CallMethod(_obj, (char *)"add", (char *)"ns#", pybegin, raw, pylen);
}


void
PyCallObjectStream::error(const char *raw, offset_type begin, offset_type len) {
  if (!is_handled("error"))
    return;

  const Py_ssize_t pybegin = begin;
  const Py_ssize_t pylen = len;

  PyObject_CallMethod(_obj, (char *)"error", (char *)"ns#", pybegin, raw, pylen);
}


// ============================================================================
// PyCallFuncStream
// ============================================================================
PyCallFuncStream::PyCallFuncStream(PyObject *func) : _func(func) {
  Py_INCREF(_func);
}

PyCallFuncStream::~PyCallFuncStream(void) {
  Py_DECREF(_func);
}


void
PyCallFuncStream::call(const char *type) {
  if (!PyObject_CallFunction(_func, (char *)"s", type))
    throw PyRaise();
}


void
PyCallFuncStream::call_i(const char *type, const int i) {
  if (!PyObject_CallFunction(_func, (char *)"si", type, i))
    throw PyRaise();
}


PyObject *
PyCallFuncStream::get(void) {
  Py_RETURN_NONE;
}


void
PyCallFuncStream::add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm) {
  const Py_ssize_t pybegin = begin;
  const Py_ssize_t pylen = len;

  if (norm)
    PyObject_CallFunction(_func, (char *)"sns#s", "token", pybegin, raw, pylen, norm);
  else
    PyObject_CallFunction(_func, (char *)"sns#", "token", pybegin, raw, pylen);
}


void
PyCallFuncStream::error(const char *raw, offset_type begin, offset_type len) {
  const Py_ssize_t pybegin = begin;
  const Py_ssize_t pylen = len;

  PyObject_CallFunction(_func, (char *)"sns#", "error", pybegin, raw, pylen);
}

}  // namespace tokenizer
}  // namespace schwa
