/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#include "callback_stream.h"

#include <cstring>
#include <sstream>

#include "exception.h"


namespace schwa {
namespace tokenizer {

// ============================================================================
// PyCallObjectStream
// ============================================================================
PyCallObjectStream::PyCallObjectStream(PyObject *obj) : _obj(obj), _unhandled(nullptr) {
  Py_INCREF(_obj);

  // Ensure the initial value for all function pointers is NULL so the destructor behaves corectly.
  std::memset(_methods, static_cast<int>(NULL), sizeof(_methods));

  // Init all of the methods, with `unhandled` first so that we have a method to fall back to.
  init_method("unhandled", Method::UNHANDLED);
  init_method("begin_sentence", Method::BEGIN_SENTENCE);
  init_method("end_sentence", Method::END_SENTENCE);
  init_method("begin_paragraph", Method::BEGIN_PARAGRAPH);
  init_method("end_paragraph", Method::END_PARAGRAPH);
  init_method("begin_heading", Method::BEGIN_HEADING);
  init_method("end_heading", Method::END_HEADING);
  init_method("begin_list", Method::BEGIN_LIST);
  init_method("end_list", Method::END_LIST);
  init_method("begin_item", Method::BEGIN_ITEM);
  init_method("end_item", Method::END_ITEM);
  init_method("begin_document", Method::BEGIN_DOCUMENT);
  init_method("end_document", Method::END_DOCUMENT);
  init_method("add", Method::ADD);
  init_method("error", Method::ERROR);
}

PyCallObjectStream::~PyCallObjectStream(void) {
  Py_DECREF(_obj);
  for (uint8_t i = 0; i != to_underlying(Method::UNHANDLED) + 1; ++i)
    Py_XDECREF(_methods[i]);
}


void
PyCallObjectStream::init_method(const char *const method_name, const Method method) {
  // Does an attr exist on the object with the name `method_name`?
  PyObject *func = PyObject_GetAttrString(_obj, method_name);
  if (func == nullptr) {
    PyErr_Clear();
    if (method == Method::UNHANDLED)
      return;

    // Fallback to the unhandled method, ensuring it exists.
    if (_unhandled == nullptr) {
      std::ostringstream ss;
      ss << "Neither methods '" << method_name << "' or 'unhandled' exist.";
      throw TypeError(ss.str());
    }
  }
  else if (!PyCallable_Check(func)) {  // Ensure the found attr is callable.
    Py_DECREF(func);
    std::ostringstream ss;
    ss << "Attribute '" << method_name << "' is not callable.";
    throw TypeError(ss.str());
  }

  // Store the method in the lookup table.
  _methods[to_underlying(method)] = func;
  _method_names[to_underlying(method)] = method_name;
  if (method == Method::UNHANDLED)
    _unhandled = func;
}


void
PyCallObjectStream::call(const Method method) {
  PyObject *const func = _methods[to_underlying(method)];
  PyObject *ret;
  if (func == nullptr) {
#ifdef IS_PY3K
    const char *const fmt = "y";
#else
    const char *const fmt = "s";
#endif
    ret = PyObject_CallFunction(_unhandled, (char *)fmt, _method_names[to_underlying(method)]);
  }
  else
    ret = PyObject_CallFunction(func, nullptr);
  if (ret == nullptr)
    throw PyRaise();
  Py_DECREF(ret);
}


void
PyCallObjectStream::call_i(const Method method, const int i) {
  PyObject *const func = _methods[to_underlying(method)];
  PyObject *ret;
  if (func == nullptr) {
#ifdef IS_PY3K
    const char *const fmt = "yi";
#else
    const char *const fmt = "si";
#endif
    ret = PyObject_CallFunction(_unhandled, (char *)fmt, _method_names[to_underlying(method)], i);
  }
  else
    ret = PyObject_CallFunction(func, (char *)"i", i);
  if (ret == nullptr)
    throw PyRaise();
  Py_DECREF(ret);
}


PyObject *
PyCallObjectStream::return_value(void) {
  Py_RETURN_NONE;
}


void
PyCallObjectStream::add(Type type, const char *raw, size_t begin, size_t len, const char *norm) {
  PyObject *const func = _methods[to_underlying(Method::ADD)];
  const Py_ssize_t pybegin = begin;
  const Py_ssize_t pylen = len;

  PyObject *ret;
  if (func == nullptr) {
    if (norm) {
#ifdef IS_PY3K
      const char *const fmt = "yny#y";
#else
      const char *const fmt = "sns#s";
#endif
      ret = PyObject_CallFunction(_unhandled, (char *)fmt, _method_names[to_underlying(Method::ADD)], pybegin, raw, pylen, norm);
    }
    else {
#ifdef IS_PY3K
      const char *const fmt = "yny#";
#else
      const char *const fmt = "sns#";
#endif
      ret = PyObject_CallFunction(_unhandled, (char *)fmt, _method_names[to_underlying(Method::ADD)], pybegin, raw, pylen);
    }
  }
  else {
    if (norm) {
#ifdef IS_PY3K
      const char *const fmt = "ny#y";
#else
      const char *const fmt = "ns#s";
#endif
      ret = PyObject_CallFunction(func, (char *)fmt, pybegin, raw, pylen, norm);
    }
    else {
#ifdef IS_PY3K
      const char *const fmt = "ny#";
#else
      const char *const fmt = "ns#";
#endif
      ret = PyObject_CallFunction(func, (char *)fmt, pybegin, raw, pylen);
    }
  }
  if (ret == nullptr)
    throw PyRaise();
  Py_DECREF(ret);
}


void
PyCallObjectStream::error(const char *raw, size_t begin, size_t len) {
  PyObject *const func = _methods[to_underlying(Method::ERROR)];
  const Py_ssize_t pybegin = begin;
  const Py_ssize_t pylen = len;

  PyObject *ret;
  if (func == nullptr) {
#ifdef IS_PY3K
    const char *const fmt = "yny#";
#else
    const char *const fmt = "sns#";
#endif
    ret = PyObject_CallFunction(_unhandled, (char *)fmt, _method_names[to_underlying(Method::ERROR)], pybegin, raw, pylen);
  }
  else {
#ifdef IS_PY3K
    const char *const fmt = "ny#";
#else
    const char *const fmt = "ns#";
#endif
    ret = PyObject_CallFunction(func, (char *)fmt, pybegin, raw, pylen);
  }
  if (ret == nullptr)
    throw PyRaise();
  Py_DECREF(ret);
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
#ifdef IS_PY3K
  const char *const fmt = "y";
#else
  const char *const fmt = "s";
#endif
  PyObject *ret = PyObject_CallFunction(_func, (char *)fmt, type);
  if (ret == nullptr)
    throw PyRaise();
  Py_DECREF(ret);
}


void
PyCallFuncStream::call_i(const char *type, const int i) {
#ifdef IS_PY3K
  const char *const fmt = "yi";
#else
  const char *const fmt = "si";
#endif
  PyObject *ret = PyObject_CallFunction(_func, (char *)fmt, type, i);
  if (ret == nullptr)
    throw PyRaise();
  Py_DECREF(ret);
}


PyObject *
PyCallFuncStream::return_value(void) {
  Py_RETURN_NONE;
}


void
PyCallFuncStream::add(Type type, const char *raw, size_t begin, size_t len, const char *norm) {
  const Py_ssize_t pybegin = begin;
  const Py_ssize_t pylen = len;

  PyObject *ret;
  if (norm) {
#ifdef IS_PY3K
    const char *const fmt = "yny#y";
#else
    const char *const fmt = "sns#s";
#endif
    ret = PyObject_CallFunction(_func, (char *)fmt, "token", pybegin, raw, pylen, norm);
  }
  else {
#ifdef IS_PY3K
    const char *const fmt = "yny#";
#else
    const char *const fmt = "sns#";
#endif
    ret = PyObject_CallFunction(_func, (char *)fmt, "token", pybegin, raw, pylen);
  }

  if (ret == nullptr)
    throw PyRaise();
  Py_DECREF(ret);
}


void
PyCallFuncStream::error(const char *raw, size_t begin, size_t len) {
  const Py_ssize_t pybegin = begin;
  const Py_ssize_t pylen = len;

#ifdef IS_PY3K
  const char *const fmt = "yny#";
#else
  const char *const fmt = "sns#";
#endif
  PyObject *ret = PyObject_CallFunction(_func, (char *)fmt, "error", pybegin, raw, pylen);
  if (ret == nullptr)
    throw PyRaise();
  Py_DECREF(ret);
}

}  // namespace tokenizer
}  // namespace schwa
