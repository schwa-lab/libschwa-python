/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#ifndef EXCEPTION_H_
#define EXCEPTION_H_

#include "_python.h"

#include <string>

#include <schwa/exception.h>


namespace schwa {
  namespace tokenizer {

    class PyRaise {
    public:
      PyRaise(void) { }
      ~PyRaise(void) throw() { }
    };


    class PyError : public Exception {
    public:
      PyObject *const except;

      PyError(PyObject *except, const std::string &msg) : Exception(msg), except(except) { }
      virtual ~PyError(void) throw() {}
    };


    class ValueError : public PyError {
    public:
      ValueError(const std::string &msg) : PyError(PyExc_ValueError, msg) { }
      virtual ~ValueError(void) throw() { }
    };


    class TypeError : public PyError {
    public:
      TypeError(const std::string &msg) : PyError(PyExc_TypeError, msg) { }
      virtual ~TypeError(void) throw() { }
    };

  }
}

#endif  // EXCEPTION_H_
