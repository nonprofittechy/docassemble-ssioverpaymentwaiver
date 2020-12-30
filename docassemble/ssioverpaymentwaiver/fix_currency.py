from docassemble.base.util import DAEmpty, currency
from docassemble.base.functions import update_language_function, currency_default

def empty_currency(*pargs, **kwargs):
  if isinstance(pargs[0], DAEmpty):
    return ""
  return currency_default(*pargs, **kwargs)

update_language_function('*', 'currency', empty_currency)

def thousands(num:float) -> str:
  """
  Return a whole number formatted with thousands separator.
  """
  try:
    return f"{num:,.2f}"
  except:
    return num