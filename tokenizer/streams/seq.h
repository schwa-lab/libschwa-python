/* -*- Mode: C++; indent-tabs-mode: nil -*- */

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
      PySeqStream(void) { }
      virtual ~PySeqStream(void) {
        for (PyVector::iterator it = _paragraphs.begin(); it != _paragraphs.end(); ++it)
          Py_DECREF(*it);
        for (PyVector::iterator it = _sentences.begin(); it != _sentences.end(); ++it)
          Py_DECREF(*it);
        for (PyVector::iterator it = _tokens.begin(); it != _tokens.end(); ++it)
          Py_DECREF(*it);
      }

      virtual void add(Type type, const char *raw, offset_type begin, offset_type len, const char *norm=0) {
        PyObject *tuple = 0;
        Py_ssize_t pybegin = begin;
        int pylen = len;
        if (norm)
          tuple = Py_BuildValue("ns#s", pybegin, raw, pylen, norm);
        else
          tuple = Py_BuildValue("ns#", pybegin, raw, pylen);
        _tokens.push_back(tuple);
      }

      virtual void error(const char *raw, offset_type begin, offset_type len) { }

      PyObject *get(void) {
        PyObject *seq = vector2seq(_paragraphs);
        _tokens.resize(0);
        _sentences.resize(0);
        _paragraphs.resize(0);
        return seq;
      }

      virtual void begin_sentence(void) { }
      virtual void end_sentence(void) {
        _sentences.push_back(vector2seq(_tokens));
        _tokens.resize(0);
      }

      virtual void begin_paragraph(void) { }
      virtual void end_paragraph(void) {
        _paragraphs.push_back(vector2seq(_sentences));
        _sentences.resize(0);
      }

      virtual void begin_heading(int depth) { begin_paragraph(); }
      virtual void end_heading(int depth) { end_paragraph(); }

      virtual void begin_list(void) { }
      virtual void end_list(void) {
        end_paragraph();
      }

      virtual void begin_item(void) { }
      virtual void end_item(void) { }

      virtual void begin_document(void) { }
      virtual void end_document(void) { }
    };


    class PyListStream : public PySeqStream {
    protected:
      virtual PyObject *
      vector2seq(PyVector &vec) const {
        PyObject *list = PyList_New(vec.size());
        Py_ssize_t index = 0;
        for (PyVector::iterator it = vec.begin(); it != vec.end(); ++it, ++index)
          PyList_SET_ITEM(list, index, *it);
        return list;
      }
    };


    class PyTupleStream : public PySeqStream {
    protected:
      virtual PyObject *
      vector2seq(PyVector &vec) const {
        PyObject *tuple = PyTuple_New(vec.size());
        Py_ssize_t index = 0;
        for (PyVector::iterator it = vec.begin(); it != vec.end(); ++it, ++index)
          PyTuple_SET_ITEM(tuple, index, *it);
        return tuple;
      }
    };

  }
}
