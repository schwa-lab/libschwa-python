/* -*- Mode: C++; indent-tabs-mode: nil -*- */

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

      virtual PyObject *get(void) {
        const std::string res = _out.str();
        return PyString_FromStringAndSize(res.data(), res.size());
      }

      virtual void add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm=0) {
        _delegate.add(type, raw, begin, len, norm);
      }

      virtual void error(const char *raw, offset_type begin, offset_type len) {
        _delegate.error(raw, begin, len);
      }

      virtual void begin_sentence(void) { _delegate.begin_sentence(); }
      virtual void end_sentence(void) { _delegate.end_sentence(); }

      virtual void begin_paragraph(void) { _delegate.begin_paragraph(); }
      virtual void end_paragraph(void) { _delegate.end_paragraph(); }

      virtual void begin_heading(int depth) { _delegate.begin_heading(depth); }
      virtual void end_heading(int depth) { _delegate.end_heading(depth); }

      virtual void begin_list(void) { _delegate.begin_list(); }
      virtual void end_list(void) { _delegate.end_list(); }

      virtual void begin_item(void) { _delegate.begin_item(); }
      virtual void end_item(void) { _delegate.end_item(); }

      virtual void begin_document(void) { _delegate.begin_document(); }
      virtual void end_document(void) { _delegate.end_document(); }
    };


    class PyBytesStream : public PyTextStream {
    public:
      PyBytesStream(bool normalise) : PyTextStream(normalise) { }
      virtual ~PyBytesStream(void) { }
    };


    class PyUnicodeStream : public PyTextStream {
    public:
      PyUnicodeStream(bool normalise) : PyTextStream(normalise) { }
      virtual ~PyUnicodeStream(void) { }

      virtual PyObject *get(void) {
        const std::string res = _out.str();
        return PyUnicode_DecodeUTF8(res.data(), res.size(), "strict");
      }
    };

  }
}
