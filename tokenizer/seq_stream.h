/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#ifndef SEQ_STREAM_H_
#define SEQ_STREAM_H_

#include "_python.h"

#include <vector>

#include <schwa/_base.h>
#include "pystream.h"


namespace schwa {
  namespace tokenizer {

    using PyVector = std::vector<PyObject *>;


    class PySeqStream : public PyStream {
    protected:
      PyVector _paragraphs;
      PyVector _sentences;
      PyVector _tokens;

      virtual PyObject *vector2seq(PyVector &vec) const = 0;

    public:
      PySeqStream(void) : PyStream() { }
      virtual ~PySeqStream(void);

      virtual void add(Type type, const char *raw, size_t begin, size_t len, const char *norm=nullptr) override;
      virtual void error(const char *raw, size_t begin, size_t len) override { }

      PyObject *return_value(void) override;

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
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PySeqStream);
    };


    class PyListStream : public PySeqStream {
    protected:
      PyObject *vector2seq(PyVector &vec) const override;

    public:
      PyListStream(void) : PySeqStream() { }
      virtual ~PyListStream(void) { }

    private:
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PyListStream);
    };


    class PyTupleStream : public PySeqStream {
    protected:
      PyObject *vector2seq(PyVector &vec) const override;

    public:
      PyTupleStream(void) : PySeqStream() { }
      virtual ~PyTupleStream(void) { }

    private:
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PyTupleStream);
    };

  }
}

#endif  // SEQ_STREAM_H_
