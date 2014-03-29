# vim: set et nosi ai ts=2 sts=2 sw=2:
# -*- coding: utf-8 -*-
import os
import shlex
import subprocess

from distutils import log
from setuptools import Extension, setup

VERSION = open(os.path.join(os.path.dirname(__file__), 'VERSION')).read().strip()


def pkg_config(*args):
  try:
    output = subprocess.check_output(('pkg-config',) + args).decode('utf-8')
  except subprocess.CalledProcessError:
    return None
  else:
    return shlex.split(output)


def tokenizer_ext():
  extra_compile_args = []
  extra_link_args = []
  include_dirs = ['tokenizer']
  library_dirs = []
  libraries = []

  # Try and find out if libschwa is installed on the system, and if so, split off the compiler
  # flags into their appropriate sections of the Extension object.
  if pkg_config('--modversion', 'libschwa') is not None:
    for arg in pkg_config('--cflags', 'libschwa'):
      if arg.startswith('-I'):
        include_dirs.append(arg[2:])
      else:
        extra_compile_args.append(arg)
    for arg in pkg_config('--libs', 'libschwa'):
      if arg.startswith('-L'):
        library_dirs.append(arg[2:])
      elif arg.startswith('-l'):
        libraries.append(arg[2:])
      else:
        extra_link_args.append(arg)
  else:
    log.error('Could not find an installed version of libschwa. Call to `pkg-config --modversion libschwa` failed. Compilation will most likely fail.')
    libraries.append('schwa')

  return Extension(
      'schwa.tokenizer',
      language='c++',
      extra_compile_args=extra_compile_args,
      extra_link_args=extra_link_args,
      include_dirs=include_dirs,
      library_dirs=library_dirs,
      libraries=libraries,
      sources=[
          'tokenizer/callback_stream.cc',
          'tokenizer/seq_stream.cc',
          'tokenizer/text_stream.cc',
          'tokenizer/module.cc',
      ]
  )


setup(
    name='libschwa-python',
    version=VERSION,
    description='Schwa Lab NLP tools',
    author='Schwa Lab',
    author_email='schwa-lab@it.usyd.edu.au',
    maintainer='Tim Dawborn',
    maintainer_email='tim.dawborn@gmail.com',
    url='https://github.com/schwa-lab/libschwa-python',
    package_dir={
        'schwa': 'schwa',
        'schwa.dr': 'schwa/dr',
        'schwa.dr.contrib': 'schwa/dr/contrib',
        'schwa.dr.contrib.writers': 'schwa/dr/contrib/writers',
        'schwa.dr.contrib.tokenizers': 'schwa/dr/contrib/tokenizers',
    },
    packages=[
        'schwa',
        'schwa.dr',
        'schwa.dr.contrib',
        'schwa.dr.contrib.writers',
        'schwa.dr.contrib.tokenizers',
    ],
    ext_modules=[tokenizer_ext()],
    install_requires=[
        'msgpack-python >= 0.3',
        'python-dateutil',
        'six',
    ],
    test_suite='nose.collector',
    tests_require=[
        'nose',
    ],
)
