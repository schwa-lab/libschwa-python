# vim: set ts=2 et:
from .meta import Ann, Doc, MetaBase

__all__ = ['get_or_create_klass']


def get_or_create_klass(module_id, klass_name, is_doc=False, attrs=None):
  """
  Creates an Ann or Doc subclass at runtime.
  @param module_id a unique id for the module to create the class in
  @param klass_name the string name of the class
  @param is_doc whether or not the class to be created should be a Doc or Ann subclass
  @param attrs dict of the docrep attrs to create on the class
  @return the class object for the newly created class
  """
  if not hasattr(get_or_create_klass, 'klasses'):
    get_or_create_klass.klasses = {}

  key = (module_id, klass_name)
  if key in get_or_create_klass.klasses:
    return get_or_create_klass.klasses[key]

  if attrs is None:
    attrs = {}
  attrs['__module__'] = '{0}.m{1}'.format(get_or_create_klass.__module__, module_id)

  base = Doc if is_doc else Ann
  klass = MetaBase(klass_name, (base, ), attrs)

  get_or_create_klass.klasses[key] = klass
  return klass
