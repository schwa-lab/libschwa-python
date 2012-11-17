/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#include "text_stream.h"


namespace schwa {
namespace tokenizer {

// ============================================================================
// PyTextStream
// ============================================================================
PyObject *
PyTextStream::get(void) {
  const std::string res = _out.str();
  return PyString_FromStringAndSize(res.data(), res.size());
}


// ============================================================================
// PyUnicodeStream
// ============================================================================
PyObject *
PyUnicodeStream::get(void) {
  const std::string res = _out.str();
  return PyUnicode_DecodeUTF8(res.data(), res.size(), "strict");
}

}  // namespace tokenizer
}  // namespace schwa
