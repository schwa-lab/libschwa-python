# vim: set et nosi ai ts=2 sts=2 sw=2:
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os
import sys

from setuptools import Extension, setup

IS_DARWIN = sys.platform == 'darwin'
VERSION = open(os.path.join(os.path.dirname(__file__), 'VERSION')).read().strip()


extra_compile_args = ['-std=c++11']
if IS_DARWIN:
  extra_compile_args.append('-stdlib=libc++')

tokenizer = Extension(
    'schwa.tokenizer',
    language='c++',
    extra_compile_args=extra_compile_args,
    include_dirs=['tokenizer'],
    libraries=['schwa'],
    sources=[
        'tokenizer/callback_stream.cc',
        'tokenizer/pyfile_source.cc',
        'tokenizer/pytokenizer.cc',
        'tokenizer/seq_stream.cc',
        'tokenizer/text_stream.cc',
    ]
)


setup(
    name='schwa',
    version=VERSION,
    description='Python bindings of libschwa',
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
    ext_modules=[tokenizer],
    install_requires=[
        'msgpack-python >= 0.3',
        'python-dateutil',
    ],
)
