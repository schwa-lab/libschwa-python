/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#ifndef EXCEPTION_H_
#define EXCEPTION_H_

#include <Python.h>

#include <exception>
#include <string>

namespace schwa {
  namespace tokenizer {

    class PyRaise {
    public:
      PyRaise(void) { }
      ~PyRaise(void) throw() { }
    };


    class PyError : public std::exception {
    public:
      PyObject *except;
      std::string msg;

      PyError(PyObject *except, const std::string &msg) : except(except), msg(msg) { }
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
