#ifndef SCHWA__PYTHON_H_
#define SCHWA__PYTHON_H_

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#if PY_MAJOR_VERSION >= 3
  #define IS_PY3K (1)
#endif

#ifdef IS_PY3K
  #define SCHWA_PY_BYTES_TYPE (PyBytes_Type)
  #define SCHWA_PY_MODULE_INIT_RETURN_ERROR(m) return nullptr
  #define SCHWA_PY_MODULE_INIT_RETURN_SUCCESS(m) return m
  #define SCHWA_PY_BINARY_FMT "y"
  #define SCHWA_PY_BINARY_TYPE_NAME "bytes"
  #define SCHWA_PY_TEXT_TYPE_NAME "str"
#else
  #define SCHWA_PY_BYTES_TYPE (PyString_Type)
  #define SCHWA_PY_MODULE_INIT_RETURN_ERROR(m) return
  #define SCHWA_PY_MODULE_INIT_RETURN_SUCCESS(m) return
  #define SCHWA_PY_BINARY_FMT "s"
  #define SCHWA_PY_BINARY_TYPE_NAME "str"
  #define SCHWA_PY_TEXT_TYPE_NAME "unicode"
#endif

#endif  // SCHWA__PYTHON_H_
