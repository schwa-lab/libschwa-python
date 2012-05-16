/* -*- Mode: C++; indent-tabs-mode: nil -*- */

namespace schwa {
  namespace tokenizer {

    class PyCallObjectStream : public PyStream {
    protected:
      PyObject *_obj;

      bool is_handled(const char* method) {
        if (PyObject_HasAttrString(_obj, method))
          return true;
        if (PyObject_HasAttrString(_obj, "unhandled"))
          PyObject_CallMethod(_obj, (char *)"unhandled", (char *)"s", method);
        return false;
      }

      void call(const char *method) {
        if (!is_handled(method))
          return;
        if (!PyObject_CallMethod(_obj, (char *)method, 0))
          throw PyRaise();
      }

    public:
      PyCallObjectStream(PyObject *obj) : _obj(obj) {
        Py_INCREF(_obj);
      }
      virtual ~PyCallObjectStream(void) {
        Py_DECREF(_obj);
      }

      PyObject *get(void) {
        Py_RETURN_NONE;
      }

      void add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm=0) {
        if (!is_handled("add"))
          return;

        Py_ssize_t pybegin = begin;
        int pylen = len;

        PyObject *res = 0;
        if (norm)
          res = PyObject_CallMethod(_obj, (char *)"add", (char *)"ns#s", pybegin, raw, pylen, norm);
        else
          res = PyObject_CallMethod(_obj, (char *)"add", (char *)"ns#", pybegin, raw, pylen);
      }

      virtual void error(const char *raw, offset_type begin, offset_type len) {
        if (!is_handled("error"))
          return;

        Py_ssize_t pybegin = begin;
        int pylen = len;

        PyObject_CallMethod(_obj, (char *)"error", (char *)"ns#", pybegin, raw, pylen);
      }

      void begin_sentence(void) { call("begin_sentence"); }
      void end_sentence(void) { call("end_sentence"); }

      void begin_paragraph(void) { call("begin_paragraph"); }
      void end_paragraph(void) { call("end_paragraph"); }

      void begin_heading(int depth) {
        if (!is_handled("begin_heading"))
          return;
        PyObject_CallMethod(_obj, (char *)"begin_heading", (char *)"i", depth);
      }
      void end_heading(int depth) {
        if (!is_handled("end_heading"))
          return;
        PyObject_CallMethod(_obj, (char *)"end_heading", (char *)"i", depth);
      }

      virtual void begin_list(void) { call("begin_list"); }
      virtual void end_list(void) { call("end_list"); }

      virtual void begin_item(void) { call("begin_item"); }
      virtual void end_item(void) { call("end_item"); }

      virtual void begin_document(void) { call("begin_document"); }
      virtual void end_document(void) { call("end_document"); }
    };


    class PyCallFuncStream : public PyStream {
    protected:
      PyObject *_func;

      void call(const char *type) {
        if (!PyObject_CallFunction(_func, (char *)"s", type))
          throw PyRaise();
      }

    public:
      PyCallFuncStream(PyObject *func) : _func(func) {
        Py_INCREF(_func);
      }
      virtual ~PyCallFuncStream(void) {
        Py_DECREF(_func);
      }

      PyObject *get(void) {
        Py_RETURN_NONE;
      }

      void add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm=0) {
        Py_ssize_t pybegin = begin;
        int pylen = len;

        PyObject *res = 0;
        if (norm)
          res = PyObject_CallFunction(_func, (char *)"sns#s", "token", pybegin, raw, pylen, norm);
        else
          res = PyObject_CallFunction(_func, (char *)"sns#", "token", pybegin, raw, pylen);
      }

      virtual void error(const char *raw, offset_type begin, offset_type len) {
        Py_ssize_t pybegin = begin;
        int pylen = len;

        PyObject_CallFunction(_func, (char *)"sns#", "error", pybegin, raw, pylen);
      }

      void begin_sentence(void) { call("begin_sentence"); }
      void end_sentence(void) { call("end_sentence"); }

      void begin_paragraph(void) { call("begin_paragraph"); }
      void end_paragraph(void) { call("end_paragraph"); }

      void begin_heading(int depth) {
        PyObject_CallFunction(_func, (char *)"si", "begin_heading", depth);
      }
      void end_heading(int depth) {
        PyObject_CallFunction(_func, (char *)"si", "end_heading", depth);
      }

      virtual void begin_list(void) { call("begin_list"); }
      virtual void end_list(void) { call("end_list"); }

      virtual void begin_item(void) { call("begin_item"); }
      virtual void end_item(void) { call("end_item"); }

      virtual void begin_document(void) { call("begin_document"); }
      virtual void end_document(void) { call("end_document"); }
    };

  }
}
