/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#include "_python.h"

#include <fstream>
#include <memory>

#include <schwa/_base.h>
#include <schwa/exception.h>
#include <schwa/tokenizer.h>
#include <schwa/utils/enums.h>

#include "callback_stream.h"
#include "exception.h"
#include "pystream.h"
#include "seq_stream.h"
#include "text_stream.h"

namespace io = schwa::io;
namespace tok = schwa::tokenizer;

using schwa::to_underlying;


// ============================================================================
// Module-level objects
// ============================================================================
static PyObject *module_TokenError = nullptr;


// ============================================================================
// PyTokenizer
// ============================================================================
typedef struct {
  PyObject_HEAD
  tok::Tokenizer *tokenizer;
} PyTokenizer;


static PyObject *
PyTokenizer_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  PyTokenizer *self = (PyTokenizer *)type->tp_alloc(type, 0);
  if (self != nullptr)
    self->tokenizer = new tok::Tokenizer();
  return (PyObject *)self;
}


static void
PyTokenizer_dealloc(PyTokenizer *self) {
  PyObject *const pyself = (PyObject *)self;
  delete self->tokenizer;
  pyself->ob_type->tp_free(pyself);
}


static const char *const PyTokenizer_tokenize__doc =
  "Identifies paragraph, sentence and token boundaries in (English) text or HTML,\n"
  "using a rule-based lexer.\n"
  "\n"
  "Arguments:\n"
  "\n"
  "  source: a UTF-8 byte string\n"
  "\n"
  "  dest: the output method, one of the following Python types:\n"
  "    - " SCHWA_PY_BINARY_TYPE_NAME " (default): outputs a UTF-8 string with '\\n\\n', '\\n' and ' ' as\n"
  "      paragraph, sentence and token delimiters respectively\n"
  "    - " SCHWA_PY_TEXT_TYPE_NAME ": like " SCHWA_PY_BINARY_TYPE_NAME ", but with UTF-8 decoded\n"
  "    - list: outputs a list of paragraphs, each containing a list of sentences,\n"
  "      each containing a list of (offset, raw_token, [normalised_token]) tuples\n"
  "    or:\n"
  "    - any other callable: makes callbacks with arguments\n"
  "      (emit_type, offset, raw, norm)\n"
  "    - any other object: calls methods named according to emit_type when present\n"
  "\n"
  "    Offset is a byte offset into the input string.\n"
  "    Emit types are:\n"
  "      begin_{document,paragraph,sentence,heading,list,item},\n"
  "      end_{document,paragraph,sentence,heading,list,item},\n"
  "      token and error\n"
  "\n"
  "  filename: the path to a file to use instead of source\n"
  "\n"
  "  buffer_size: \n"
  "\n"
  "  errors: a method for dealing with bad byte sequences, may be one of:\n"
  "    - ERROR_SKIP (default): ignores errors\n"
  "    - ERROR_CALL: emits ('error', offset, bytes)\n"
  "    - ERROR_THROW: throws a TokenError\n"
  "\n"
  "  normalise: a boolean (default True) indicating whether to perform\n"
  "    normalisation on the output (such as directed quotes, all dashes as --, and\n"
  "    * to indicate list items). Only applies when dest is a string-like value.\n"
  "\n"
  "  mmap: a boolean (default False) indicating whether to process the file\n"
  "    memory-mapped, when the filename argument is used.";

static PyObject *
PyTokenizer_tokenize(PyTokenizer *self, PyObject *args, PyObject *kwargs) {
  // Setup default values for kwarg parsing.
  PyObject *pysrc = nullptr;
  PyObject *pydest = (PyObject *)&SCHWA_PY_BYTES_TYPE;
  const char *filename = nullptr;
  Py_ssize_t buffer_size = static_cast<Py_ssize_t>(tok::DEFAULT_BUFFER_SIZE);
  int pyerrors = to_underlying(tok::OnError::SKIP);
  int normalise = 1;
  int use_mmap = 0;

  // Parse the kwargs.
  static const char *kwlist[] = {"source", "dest", "filename", "buffer_size", "errors", "normalise", "mmap", 0};
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|OOsniii:tokenize", (char **)kwlist, &pysrc, &pydest, &filename, &buffer_size, &pyerrors, &normalise, &use_mmap))
    return 0;

  // Validate the arguments.
  if (!pysrc && !filename)
    return PyErr_Format(PyExc_TypeError, "tokenize() requires either a source or filename argument");
  if (pysrc) {
    if (PyUnicode_Check(pysrc))
      return PyErr_Format(PyExc_TypeError, "tokenize() does not accept " SCHWA_PY_TEXT_TYPE_NAME " objects, use .encode('utf-8')");
    else if (!PyObject_CheckBuffer(pysrc))
      return PyErr_Format(PyExc_TypeError, "tokenize() source must support the buffer interface");
  }
  if (buffer_size <= 0)
    return PyErr_Format(PyExc_ValueError, "tokenize() buffer_size must be positive, %zu given", buffer_size);
  tok::OnError onerror = tok::OnError::SKIP;
  switch (pyerrors) {
  case to_underlying(tok::OnError::CALL):
    onerror = tok::OnError::CALL;
    break;
  case to_underlying(tok::OnError::SKIP):
    onerror = tok::OnError::SKIP;
    break;
  case to_underlying(tok::OnError::THROW):
    onerror = tok::OnError::THROW;
    break;
  default:
    return PyErr_Format(PyExc_ValueError, "tokenize() unknown bad byte error handler, %d given", pyerrors);
  }

  try {
    // Work out what the destination for the tokenizers output should be.
    std::unique_ptr<tok::PyStream> stream;
    if ((void *)pydest == (void *)&SCHWA_PY_BYTES_TYPE)
      stream.reset(new tok::PyBytesStream(normalise));
    else if ((void *)pydest == (void *)&PyUnicode_Type)
      stream.reset(new tok::PyUnicodeStream(normalise));
    else if ((void *)pydest == (void *)&PyList_Type)
      stream.reset(new tok::PyListStream());
    else if ((void *)pydest == (void *)&PyTuple_Type)
      stream.reset(new tok::PyTupleStream());
    else if (PyCallable_Check(pydest))
      stream.reset(new tok::PyCallFuncStream(pydest));
    else
      stream.reset(new tok::PyCallObjectStream(pydest));

    // Call the appropriate tokenize method on the Tokenizer object.
    if (filename) {
      if (use_mmap)
        self->tokenizer->tokenize_mmap(*stream, filename, onerror);
      else {
        std::ifstream in(filename);
        if (!in)
          return PyErr_Format(PyExc_IOError, "tokenize() could not open file '%s' for reading", filename);
        self->tokenizer->tokenize_stream(*stream, in, static_cast<size_t>(buffer_size), onerror);
      }
    }
    else {
      // Obtain the underlying buffer and pass it to the tokenizer, ensuring we release it.
      Py_buffer buffer;
      if (PyObject_GetBuffer(pysrc, &buffer, PyBUF_SIMPLE) != 0)
        return PyErr_Format(PyExc_ValueError, "tokenize() only supports simple buffer objects");
      if (buffer.len < 0)
        return PyErr_Format(PyExc_ValueError, "Size of the provided source's underlying buffer is negative");
      try {
        self->tokenizer->tokenize(*stream, (char *)buffer.buf, static_cast<size_t>(buffer.len), onerror);
      }
      catch (...) {
        PyBuffer_Release(&buffer);
        throw;
      }
    }

    // Return what the stream defines is the return value for this function.
    return stream->return_value();
  }
  catch (tok::TokenError &e) {
    PyErr_SetString(module_TokenError, e.what());
    return nullptr;
  }
  catch (tok::PyRaise &e) {
    return nullptr;
  }
  catch (tok::TypeError &e) {
    PyErr_SetString(PyExc_TypeError, e.what());
    return nullptr;
  }
  catch (tok::ValueError &e) {
    PyErr_SetString(PyExc_ValueError, e.what());
    return nullptr;
  }
  catch (schwa::IOException &e) {
    PyErr_SetString(PyExc_IOError, e.what());
    return nullptr;
  }
  catch (schwa::Exception &e) {
    PyErr_SetString(PyExc_Exception, e.what());
    return nullptr;
  }
}


static PyMethodDef PyTokenizer_methods[] = {
  {"tokenize", (PyCFunction)PyTokenizer_tokenize, METH_VARARGS | METH_KEYWORDS, PyTokenizer_tokenize__doc},
  {nullptr}  /* Sentinel */
};


static PyTypeObject PyTokenizerType = {
  PyVarObject_HEAD_INIT(nullptr, 0)
  "tokenizer.Tokenizer",     /* tp_name */
  sizeof(PyTokenizer),       /* tp_basicsize */
  0,                         /* tp_itemsize */
  (destructor)PyTokenizer_dealloc,  /* tp_dealloc */
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
  "Wrapper around the C++ Tokenizer class.",  /* tp_doc */
  0,                         /* tp_traverse */
  0,                         /* tp_clear */
  0,                         /* tp_richcompare */
  0,                         /* tp_weaklistoffset */
  0,                         /* tp_iter */
  0,                         /* tp_iternext */
  PyTokenizer_methods,       /* tp_methods */
  0,                         /* tp_members */
  0,                         /* tp_getset */
  0,                         /* tp_base */
  0,                         /* tp_dict */
  0,                         /* tp_descr_get */
  0,                         /* tp_descr_set */
  0,                         /* tp_dictoffset */
  (initproc)0,               /* tp_init */
  0,                         /* tp_alloc */
  PyTokenizer_new,           /* tp_new */
};


// ============================================================================
// Module
// ============================================================================
static const char *const module_name = "tokenizer";
static const char *const module_doc = "Schwa Lab tokenizer module";

static PyMethodDef module_methods[] = {
  {nullptr}  /* Sentinel */
};

#ifdef IS_PY3K
static PyModuleDef module_def = {
  PyModuleDef_HEAD_INIT,  /* m_base */
  module_name,            /* m_name */
  module_doc,             /* m_doc */
  0,                      /* m_size */
  module_methods,         /* m_methods */
  nullptr,                /* m_reload */
  nullptr,                /* m_traverse */
  nullptr,                /* m_clear */
  nullptr,                /* m_free */
};
#endif


static PyObject *
_inittokenizer(void) {
  // Ensure that PyTokenizerType is ready for use.
  if (PyType_Ready(&PyTokenizerType) != 0)
    return nullptr;

  // Construct the module.
#ifdef IS_PY3K
  PyObject *const m = PyModule_Create(&module_def);
#else
  PyObject *const m = Py_InitModule3(module_name, module_methods, module_doc);
#endif
  if (m == nullptr)
    return nullptr;

  // Add PyTokenizerType to the module.
  Py_INCREF(&PyTokenizerType);
  if (PyModule_AddObject(m, "Tokenizer", (PyObject *)&PyTokenizerType) != 0)
    return nullptr;

  // Create the TokenError exception and add it to the module.
  module_TokenError = PyErr_NewException((char *)"tokenizer.TokenError", nullptr, nullptr);
  if (module_TokenError == nullptr)
    return nullptr;
  Py_INCREF(module_TokenError);
  if (PyModule_AddObject(m, "TokenError", module_TokenError) != 0)
    return nullptr;

  // Add the error handling enums to the module.
  if (PyModule_AddIntConstant(m, "ERROR_CALL", to_underlying(tok::OnError::CALL)) != 0)
    return nullptr;
  if (PyModule_AddIntConstant(m, "ERROR_SKIP", to_underlying(tok::OnError::SKIP)) != 0)
    return nullptr;
  if (PyModule_AddIntConstant(m, "ERROR_THROW", to_underlying(tok::OnError::THROW)) != 0)
    return nullptr;

  return m;
}


PyMODINIT_FUNC
#ifdef IS_PY3K
PyInit_tokenizer(void) {
#else
inittokenizer(void) {
#endif
  PyObject *const m = _inittokenizer();
  if (m == nullptr && PyErr_Occurred()) {
    PyErr_SetString(PyExc_ImportError, "tokenizer: init failed");
    SCHWA_PY_MODULE_INIT_RETURN_ERROR(m);
  }

  SCHWA_PY_MODULE_INIT_RETURN_SUCCESS(m);
}
