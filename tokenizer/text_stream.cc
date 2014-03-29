/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#include "_python.h"
#include "text_stream.h"


namespace schwa {
namespace tokenizer {

// ============================================================================
// PyBytesStream
// ============================================================================
PyObject *
PyBytesStream::return_value(void) {
  const std::string res = _out.str();
#ifdef IS_PY3K
  return PyBytes_FromStringAndSize(res.data(), res.size());
#else
  return PyString_FromStringAndSize(res.data(), res.size());
#endif
}


// ============================================================================
// PyUnicodeStream
// ============================================================================
PyObject *
PyUnicodeStream::return_value(void) {
  const std::string res = _out.str();
#ifdef IS_PY3K
  return PyUnicode_FromStringAndSize(res.data(), res.size());
#else
  return PyUnicode_DecodeUTF8(res.data(), res.size(), "strict");
#endif
}

}  // namespace tokenizer
}  // namespace schwa
