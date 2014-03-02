/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#ifndef PYSTREAM_H_
#define PYSTREAM_H_

#include <Python.h>

#include <schwa/_base.h>
#include <schwa/tokenizer/stream.h>


namespace schwa {
  namespace tokenizer {

    class PyStream : public Stream {
    public:
      PyStream(void) : Stream() { }
      virtual ~PyStream(void) { }

      virtual PyObject *get(void) = 0;

    private:
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PyStream);
    };

  }
}

#endif  // PYSTREAM_H_
