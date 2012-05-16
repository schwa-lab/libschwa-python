/* -*- Mode: C++; indent-tabs-mode: nil -*- */

namespace schwa {
  namespace tokenizer {

    class PyStream : public Stream {
    public:
      PyStream(void) { }
      virtual ~PyStream(void) { }

      virtual PyObject *get(void) = 0;
    };

  }
}
