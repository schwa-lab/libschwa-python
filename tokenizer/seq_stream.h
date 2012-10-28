/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#ifndef SEQ_STREAM_H_
#define SEQ_STREAM_H_

#include <Python.h>

#include <vector>

#include <schwa/_base.h>
#include "pystream.h"


namespace schwa {
  namespace tokenizer {

    typedef std::vector<PyObject *> PyVector;

    class PySeqStream : public PyStream {
    protected:
      PyVector _paragraphs;
      PyVector _sentences;
      PyVector _tokens;

      virtual PyObject *vector2seq(PyVector &vec) const = 0;

    public:
      PySeqStream(void) : PyStream() { }
      virtual ~PySeqStream(void);

      virtual void add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm=0) override;
      virtual void error(const char *raw, offset_type begin, offset_type len) override { }

      PyObject *get(void) override;

      virtual void begin_sentence(void) override { }
      virtual void end_sentence(void) override;

      virtual void begin_paragraph(void) override { }
      virtual void end_paragraph(void) override;

      virtual void begin_heading(int depth) override { begin_paragraph(); }
      virtual void end_heading(int depth) override { end_paragraph(); }

      virtual void begin_list(void) override { }
      virtual void end_list(void) override;

      virtual void begin_item(void) override { }
      virtual void end_item(void) override { }

      virtual void begin_document(void) override { }
      virtual void end_document(void) override { }

    private:
      DISALLOW_COPY_AND_ASSIGN(PySeqStream);
    };


    class PyListStream : public PySeqStream {
    protected:
      PyObject *vector2seq(PyVector &vec) const override;

    public:
      PyListStream(void) : PySeqStream() { }
      virtual ~PyListStream(void) { }

    private:
      DISALLOW_COPY_AND_ASSIGN(PyListStream);
    };


    class PyTupleStream : public PySeqStream {
    protected:
      PyObject *vector2seq(PyVector &vec) const override;

    public:
      PyTupleStream(void) : PySeqStream() { }
      virtual ~PyTupleStream(void) { }

    private:
      DISALLOW_COPY_AND_ASSIGN(PyTupleStream);
    };

  }
}

#endif  // SEQ_STREAM_H_
