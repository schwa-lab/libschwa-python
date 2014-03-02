/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#ifndef TEXT_STREAM_H_
#define TEXT_STREAM_H_

#include <Python.h>

#include <sstream>

#include <schwa/_base.h>
#include <schwa/tokenizer/text_stream.h>
#include "pystream.h"


namespace schwa {
  namespace tokenizer {

    // the multiple inheritance option is a dog in C++
    class PyTextStream : public PyStream {
    protected:
      std::ostringstream _out;
      TextStream _delegate;

    public:
      PyTextStream(bool normalise) : _delegate(_out, normalise) { }
      virtual ~PyTextStream(void) { }

      virtual PyObject *get(void) override;

      void add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm=0) override {
        _delegate.add(type, raw, begin, len, norm);
      }

      void error(const char *raw, offset_type begin, offset_type len) override {
        _delegate.error(raw, begin, len);
      }

      void begin_sentence(void) override { _delegate.begin_sentence(); }
      void end_sentence(void) override { _delegate.end_sentence(); }

      void begin_paragraph(void) override { _delegate.begin_paragraph(); }
      void end_paragraph(void) override { _delegate.end_paragraph(); }

      void begin_heading(int depth) override { _delegate.begin_heading(depth); }
      void end_heading(int depth) override { _delegate.end_heading(depth); }

      void begin_list(void) override { _delegate.begin_list(); }
      void end_list(void) override { _delegate.end_list(); }

      void begin_item(void) override { _delegate.begin_item(); }
      void end_item(void) override { _delegate.end_item(); }

      void begin_document(void) override { _delegate.begin_document(); }
      void end_document(void) override { _delegate.end_document(); }

    private:
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PyTextStream);
    };


    class PyBytesStream : public PyTextStream {
    public:
      PyBytesStream(bool normalise) : PyTextStream(normalise) { }
      virtual ~PyBytesStream(void) { }

    private:
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PyBytesStream);
    };


    class PyUnicodeStream : public PyTextStream {
    public:
      PyUnicodeStream(bool normalise) : PyTextStream(normalise) { }
      virtual ~PyUnicodeStream(void) { }

      PyObject *get(void) override;

    private:
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PyUnicodeStream);
    };

  }
}

#endif
