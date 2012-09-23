# vim: set ts=2 et:
import collections
import sys


def create(name):
  if not hasattr(create, 'rtclass_count'):
    create.rtclass_count = collections.defaultdict(int)
  num = create.rtclass_count[name]
  create.rtclass_count[name] += 1
  klass_name = name + str(num)
  klass = type(klass_name, (object,), {})
  setattr(sys.modules[__name__], klass_name, klass)

  return klass
