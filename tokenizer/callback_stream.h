/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#ifndef CALLBACK_STREAM_H_
#define CALLBACK_STREAM_H_

#include <Python.h>

#include <schwa/_base.h>
#include "pystream.h"


namespace schwa {
  namespace tokenizer {

    class PyCallObjectStream : public PyStream {
    protected:
      PyObject *_obj;

      bool is_handled(const char* method);
      void call(const char *method);
      void call_i(const char *method, int i);

    public:
      PyCallObjectStream(PyObject *obj);
      virtual ~PyCallObjectStream(void);

      PyObject *get(void) override;

      void add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm=0) override;
      void error(const char *raw, offset_type begin, offset_type len) override;

      void begin_sentence(void) override { call("begin_sentence"); }
      void end_sentence(void) override { call("end_sentence"); }

      void begin_paragraph(void) override { call("begin_paragraph"); }
      void end_paragraph(void) override { call("end_paragraph"); }

      void begin_heading(int depth) override { call_i("begin_heading", depth); }
      void end_heading(int depth) override { call_i("end_heading", depth); }

      void begin_list(void) override { call("begin_list"); }
      void end_list(void) override { call("end_list"); }

      void begin_item(void) override { call("begin_item"); }
      void end_item(void) override { call("end_item"); }

      void begin_document(void) override { call("begin_document"); }
      void end_document(void) override { call("end_document"); }

    private:
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PyCallObjectStream);
    };


    class PyCallFuncStream : public PyStream {
    protected:
      PyObject *_func;

      void call(const char *type);
      void call_i(const char *type, int i);

    public:
      PyCallFuncStream(PyObject *func);
      virtual ~PyCallFuncStream(void);

      PyObject *get(void) override;

      void add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm=0) override;
      void error(const char *raw, offset_type begin, offset_type len) override;

      void begin_sentence(void) override { call("begin_sentence"); }
      void end_sentence(void) override { call("end_sentence"); }

      void begin_paragraph(void) override { call("begin_paragraph"); }
      void end_paragraph(void) override { call("end_paragraph"); }

      void begin_heading(int depth) override { call_i("begin_heading", depth); }
      void end_heading(int depth) override { call_i("end_heading", depth); }

      void begin_list(void) override { call("begin_list"); }
      void end_list(void) override { call("end_list"); }

      void begin_item(void) override { call("begin_item"); }
      void end_item(void) override { call("end_item"); }

      void begin_document(void) override { call("begin_document"); }
      void end_document(void) override { call("end_document"); }

    private:
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PyCallFuncStream);
    };

  }
}

#endif  // CALLBACK_STREAM_H_
