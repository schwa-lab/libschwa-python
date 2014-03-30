#ifndef SCHWA__PYTHON_H_
#define SCHWA__PYTHON_H_

#include <Python.h>

#if PY_MAJOR_VERSION >= 3
  #define IS_PY3K (1)
#endif

#ifdef IS_PY3K
  #define SCHWA_PY_BYTES_TYPE (PyBytes_Type)
  #define SCHWA_PY_MODULE_INIT_RETURN_ERROR(m) return nullptr
  #define SCHWA_PY_MODULE_INIT_RETURN_SUCCESS(m) return m
#else
  #define SCHWA_PY_BYTES_TYPE (PyString_Type)
  #define SCHWA_PY_MODULE_INIT_RETURN_ERROR(m) return
  #define SCHWA_PY_MODULE_INIT_RETURN_SUCCESS(m) return
#endif

#endif  // SCHWA__PYTHON_H_
