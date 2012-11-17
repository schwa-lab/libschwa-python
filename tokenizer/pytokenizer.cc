/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#include <Python.h>

#include "callback_stream.h"
#include "exception.h"
#include "pyfile_source.h"
#include "pystream.h"
#include "seq_stream.h"
#include "text_stream.h"

#include <fstream>
#include <memory>

#include <schwa/_base.h>
#include <schwa/exception.h>
#include <schwa/tokenizer.h>

namespace io = schwa::io;
namespace tok = schwa::tokenizer;


static PyObject *TokenError = 0;

static PyObject *token_ERROR_SKIP = 0;
static PyObject *token_ERROR_CALL = 0;
static PyObject *token_ERROR_THROW = 0;

typedef struct {
  PyObject_HEAD
  tok::Tokenizer tokenizer;
} PyTokenizer;


inline static PyObject *
add_to_module(PyObject *mod, const char *name, PyObject *obj) {
  Py_INCREF(obj);
  PyModule_AddObject(mod, name, obj);
  return obj;
}


inline static PyObject *
add_long_to_module(PyObject *mod, const char *name, long value) {
  return add_to_module(mod, name, PyInt_FromLong(value));
}


static tok::PyStream *
pyobj2dest(PyObject *dest, bool normalise) {
  if ((void *)dest == (void *)&PyString_Type)
    return new tok::PyBytesStream(normalise);
  else if ((void *)dest == (void *)&PyUnicode_Type)
    return new tok::PyUnicodeStream(normalise);
  else if ((void *)dest == (void *)&PyList_Type)
    return new tok::PyListStream();
  else if ((void *)dest == (void *)&PyTuple_Type)
    return new tok::PyTupleStream();
  else if (PyCallable_Check(dest))
    return new tok::PyCallFuncStream(dest);
  else
    return new tok::PyCallObjectStream(dest);
}


PyObject *
PyTokenizer_tokenize(PyTokenizer *self, PyObject *args, PyObject *kwargs) {
  tok::Tokenizer &tok = self->tokenizer;

  PyObject *pysrc = 0;
  PyObject *pydest = (PyObject *)&PyString_Type;
  const char *filename = 0;

  long buffer_size = tok::BUFFER_SIZE;
  int errors = tok::ERROR_SKIP;
  int normalise = 1;
  int use_mmap = 0;

  static const char *kwlist[] = {"source", "dest", "filename", "buffer_size", "errors", "normalise", "mmap", 0};
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|OOsliii:tokenize", (char **)kwlist, &pysrc, &pydest, &filename, &buffer_size, &errors, &normalise, &use_mmap))
    return 0;
  if (!pysrc && !filename)
    return PyErr_Format(PyExc_TypeError, "tokenize() requires either a source or filename argument");
  if (pysrc && PyUnicode_Check(pysrc))
    return PyErr_Format(PyExc_TypeError, "tokenize() does not accept unicode objects, use unicode.encode('utf-8')");
  if (buffer_size <= 0)
    return PyErr_Format(PyExc_ValueError, "tokenize() buffer_size must be positive, %ld given", buffer_size);
  if (errors < tok::ERROR_SKIP || errors > tok::ERROR_THROW)
    return PyErr_Format(PyExc_ValueError, "tokenize() unknown bad byte error handler, %d given", errors);

  try {
    std::unique_ptr<tok::PyStream> dest(pyobj2dest(pydest, normalise));
    if (filename) {
      if (use_mmap) {
        tok.tokenize_mmap(*dest, filename, errors);
      }
      else {
        std::ifstream stream(filename);
        if (!stream)
          return PyErr_Format(PyExc_IOError,"tokenize() could not open file '%s' for reading", filename);
        tok.tokenize_stream(*dest, stream, static_cast<tok::offset_type>(buffer_size), errors);
      }
    }
    else if (PyObject_CheckBuffer(pysrc)) {
      Py_buffer buffer;
      if (PyObject_GetBuffer(pysrc, &buffer, PyBUF_SIMPLE) != 0)
        return PyErr_Format(PyExc_ValueError, "tokenize() only supports simple buffer objects");
      tok.tokenize(*dest, (char *)buffer.buf, static_cast<tok::offset_type>(buffer.len), errors);
      PyBuffer_Release(&buffer);
    }
    else if (PyFile_Check(pysrc)) {
      io::PyFileSource src(pysrc);
      tok.tokenize(*dest, src, buffer_size, errors);
    }
    return dest->get();
  }
  catch (tok::TokenError &e) {
    PyErr_SetString(TokenError, e.what());
    return 0;
  }
  catch (tok::PyRaise &e) {
    return 0;
  }
  catch (schwa::IOException &e) {
    PyErr_SetString(PyExc_IOError, e.what());
    return 0;
  }
}


static PyMethodDef PyTokenizer_methods[] = {
  {"tokenize", (PyCFunction)PyTokenizer_tokenize, METH_VARARGS | METH_KEYWORDS,
"Identifies paragraph, sentence and token boundaries in (English) text or HTML,\n\
using a rule-based lexer.\n\
\n\
Arguments:\n\
\n\
  source: a string in UTF-8 or a file to tokenize\n\
\n\
  dest: the output method, one of the following Python types:\n\
    - str (default): outputs a UTF-8 string with '\\n\\n', '\\n' and ' ' as\n\
      paragraph, sentence and token delimiters respectively\n\
    - unicode: like str, but with UTF-8 decoded\n\
    - list: outputs a list of paragraphs, each containing a list of sentences,\n\
      each containing a list of (offset, raw_token, [normalised_token]) tuples\n\
    or:\n\
    - any other callable: makes callbacks with arguments\n\
      (emit_type, offset, raw, norm)\n\
    - any other object: calls methods named according to emit_type when present\n\
\n\
    Offset is a byte offset into the input string.\n\
    Emit types are:\n\
      begin_{document,paragraph,sentence,heading,list,item},\n\
      end_{document,paragraph,sentence,heading,list,item},\n\
      token and error\n\
\n\
  filename: the path to a file to use instead of source\n\
\n\
  buffer_size: \n\
\n\
  errors: a method for dealing with bad byte sequences, may be one of:\n\
    - ERROR_SKIP (default): ignores errors\n\
    - ERROR_CALL: emits ('error', offset, bytes)\n\
    - ERROR_THROW: throws a TokenError\n\
\n\
  normalise: a boolean (default True) indicating whether to perform\n\
  normalisation on the output (such as directed quotes, all dashes as --, and *\n\
  to indicate list items). Only applies when dest is str or unicode.\n\
\n\
  mmap: a boolean (default False) indicating whether to process the file\n\
  memory-mapped, when the filename argument is used."
  },
  {0}  /* Sentinel */
};


static PyGetSetDef PyTokenizer_getsets[] = {
  {0}  /* Sentinel */
};


static PyTypeObject PyTokenizerType = {
  PyObject_HEAD_INIT(NULL)
  0,                         /* ob_size */
  "tokens.Tokenizer",        /* tp_name */
  sizeof(PyTokenizer),       /* tp_basicsize */
  0,                         /* tp_itemsize */
  0,                         /* tp_dealloc */
  0,                         /* tp_print */
  0,                         /* tp_getattr */
  0,                         /* tp_setattr */
  0,                         /* tp_compare */
  0,                         /* tp_repr */
  0,                         /* tp_as_number */
  0,                         /* tp_as_sequence */
  0,                         /* tp_as_mapping */
  0,                         /* tp_hash  */
  0,                         /* tp_call */
  0,                         /* tp_str */
  0,                         /* tp_getattro */
  0,                         /* tp_setattro */
  0,                         /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT,        /* tp_flags */
  "Tokenizer object",        /* tp_doc */
  0,                         /* tp_traverse */
  0,                         /* tp_clear */
  0,                         /* tp_richcompare */
  0,                         /* tp_weaklistoffset */
  0,                         /* tp_iter */
  0,                         /* tp_iternext */
  PyTokenizer_methods,       /* tp_methods */
  0,                         /* tp_members */
  PyTokenizer_getsets,       /* tp_getset */
  0,                         /* tp_base */
  0,                         /* tp_dict */
  0,                         /* tp_descr_get */
  0,                         /* tp_descr_set */
  0,                         /* tp_dictoffset */
  (initproc)0,               /* tp_init */
  0,                         /* tp_alloc */
  PyType_GenericNew,         /* tp_new */
};


static PyMethodDef token_functions[] = {
  {0, 0, 0, 0}
};


PyMODINIT_FUNC
inittokenizer(void) {
  PyObject *m = Py_InitModule3("tokenizer", token_functions, "Schwa Lab tokenizer module");
  if (m == 0)
    return;
  if (PyType_Ready(&PyTokenizerType) < 0)
    return;

  add_to_module(m, "Tokenizer", (PyObject *)&PyTokenizerType);

  TokenError = PyErr_NewException((char *)"tokenizer.TokenError", 0, 0);
  add_to_module(m, "TokenError", TokenError);

  token_ERROR_SKIP = add_long_to_module(m, "ERROR_SKIP", tok::ERROR_SKIP);
  token_ERROR_CALL = add_long_to_module(m, "ERROR_CALL", tok::ERROR_CALL);
  token_ERROR_THROW = add_long_to_module(m, "ERROR_THROW", tok::ERROR_THROW);
}
