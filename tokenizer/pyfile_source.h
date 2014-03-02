/* -*- Mode: C++; indent-tabs-mode: nil -*- */
#ifndef PYFILE_SOURCE_H_
#define PYFILE_SOURCE_H_

#include <Python.h>

#include <schwa/_base.h>
#include <schwa/io/file_source.h>


namespace schwa {
  namespace io {

    class PyFileSource : public FileSource {
    protected:
      PyFileObject *_obj;

    public:
      PyFileSource(PyObject *obj);
      virtual ~PyFileSource(void);

    private:
      SCHWA_DISALLOW_COPY_AND_ASSIGN(PyFileSource);
    };

  }
}

#endif  // PYFILE_SOURCE_H_
