/* -*- Mode: C++; indent-tabs-mode: nil -*- */

namespace schwa {
  namespace io {

    class PyFileSource : public FileSource {
    protected:
      PyFileObject *_obj;

    public:
      PyFileSource(PyObject *obj) : FileSource(PyFile_AsFile(obj)), _obj((PyFileObject *)obj) {
        Py_INCREF(_obj);
        PyFile_IncUseCount(_obj);
      }

      virtual ~PyFileSource(void) {
        PyFile_DecUseCount(_obj);
        Py_DECREF(_obj);
      }
    };

  }
}
