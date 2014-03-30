/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#ifndef CALLBACK_STREAM_H_
#define CALLBACK_STREAM_H_

#include "_python.h"

#include <schwa/_base.h>
#include <schwa/utils/enums.h>
#include "pystream.h"


namespace schwa {
  namespace tokenizer {

    class PyCallObjectStream : public PyStream {
    public:
      enum class Method : uint8_t {
        BEGIN_SENTENCE, END_SENTENCE,
        BEGIN_PARAGRAPH, END_PARAGRAPH,
        BEGIN_HEADING, END_HEADING,
        BEGIN_LIST, END_LIST,
        BEGIN_ITEM, END_ITEM,
        BEGIN_DOCUMENT, END_DOCUMENT,
        ADD,
        ERROR,
        UNHANDLED,  // This always has to be the last value.
      };

    protected:
      PyObject *_obj;
      PyObject *_unhandled;
      PyObject *_methods[to_underlying(Method::UNHANDLED) + 1];  // One for each value of Method.
      const char *_method_names[to_underlying(Method::UNHANDLED) + 1];

      void init_method(const char *method_name, Method method);

      void call(Method method);
      void call_i(Method method, int i);

    public:
      PyCallObjectStream(PyObject *obj);
      virtual ~PyCallObjectStream(void);

      PyObject *return_value(void) override;

      void add(Type type, const char *raw, size_t begin, size_t len, const char *norm=nullptr) override;
      void error(const char *raw, size_t begin, size_t len) override;

      void begin_sentence(void) override { call(Method::BEGIN_SENTENCE); }
      void end_sentence(void) override { call(Method::END_SENTENCE); }

      void begin_paragraph(void) override { call(Method::BEGIN_PARAGRAPH); }
      void end_paragraph(void) override { call(Method::END_PARAGRAPH); }

      void begin_heading(int depth) override { call_i(Method::BEGIN_HEADING, depth); }
      void end_heading(int depth) override { call_i(Method::END_HEADING, depth); }

      void begin_list(void) override { call(Method::BEGIN_LIST); }
      void end_list(void) override { call(Method::END_LIST); }

      void begin_item(void) override { call(Method::BEGIN_ITEM); }
      void end_item(void) override { call(Method::END_ITEM); }

      void begin_document(void) override { call(Method::BEGIN_DOCUMENT); }
      void end_document(void) override { call(Method::END_DOCUMENT); }

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

      PyObject *return_value(void) override;

      void add(Type type, const char *raw, size_t begin, size_t len, const char *norm=nullptr) override;
      void error(const char *raw, size_t begin, size_t len) override;

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
