/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#include "text_stream.h"


namespace schwa {
namespace tokenizer {

// ============================================================================
// PyBytesStream
// ============================================================================
PyObject *
PyBytesStream::return_value(void) {
  const std::string res = _out.str();
  return PyString_FromStringAndSize(res.data(), res.size());
}


// ============================================================================
// PyUnicodeStream
// ============================================================================
PyObject *
PyUnicodeStream::return_value(void) {
  const std::string res = _out.str();
  return PyUnicode_DecodeUTF8(res.data(), res.size(), "strict");
}

}  // namespace tokenizer
}  // namespace schwa
