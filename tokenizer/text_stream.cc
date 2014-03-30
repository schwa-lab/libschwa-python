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
  return PyBytes_FromStringAndSize(res.data(), res.size());
}


// ============================================================================
// PyUnicodeStream
// ============================================================================
PyObject *
PyUnicodeStream::return_value(void) {
  const std::string res = _out.str();
  return PyUnicode_FromStringAndSize(res.data(), res.size());
}

}  // namespace tokenizer
}  // namespace schwa
