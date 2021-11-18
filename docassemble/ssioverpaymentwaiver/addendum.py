import re
import os
import mimetypes
from typing import Any, Dict, List, Union, Callable
from docassemble.base.util import log, word, DADict, DAList, DAObject, DAFile, DAFileCollection, DAFileList, defined, value, pdf_concatenate, zip_file, DAOrderedDict, action_button_html, include_docx_template, user_logged_in, user_info, send_email, docx_concatenate, get_config, space_to_underscore, DAStaticFile, alpha, currency

def label(dictionary):
  try:
    return list(dictionary.items())[0][1]
  except:
    return ''

def key(dictionary):
  try:
    return list(dictionary.items())[0][0]
  except:
    return ''

def safeattr(object, key):
  try:
    if isinstance(object, dict) or isinstance(object, DADict):
      return str(object.get(key,''))
    elif isinstance(object, DAObject):
      # `location` is not an attribute people usually want shown in the table of people's attributes
      if key == 'location':
        return ''
      # At least for this form assume floats should be formatted as currency values
      if isinstance(getattr(object, key), float):
        return currency(getattr(object, key))
      return str(getattr(object, key))
    else:
      return ''
  except:
    return ''

def html_safe_str(the_string: str) -> str:
  """
  Return a string that can be used as an html class or id
  """
  return re.sub( r'[^A-Za-z0-9]+', '_', the_string )


class ALAddendumField(DAObject):
  """
  Object representing a single field and its attributes as related to whether
  it should be displayed in an addendum. Useful for PDF templates.
  The items can be strings or lists/list-like objects. It does not know
  how to handle overflow for a dictionary, e.g.
  Required attributes:
    - field_name (str): represents the name of a docassemble variable
    - overflow_trigger (int | bool): determines when text is cut off and sent to addendum
  Optional/planned (not implemented yet):
    - headers->dict(attribute: display label for table)
    - field_style->"list"|"table"|"string" (optional: defaults to "string")
  """

  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)

  def overflow_value(self, preserve_newlines:bool=False, input_width:int=80, overflow_message:str=""):
    """
    Try to return just the portion of the variable (list-like object or string)
    that is not contained in the safe_value().
    """
    # Handle a Boolean overflow first
    if isinstance(self.overflow_trigger, bool) and self.overflow_trigger:
      return self.value()

    # If trigger is not a boolean value, overflow value is the value that starts at the end of the safe value.
    original_value = self.value_if_defined()
    safe_text = self.safe_value(overflow_message = overflow_message, 
                                input_width=input_width, 
                                preserve_newlines=preserve_newlines, 
                                _original_value = original_value)
    if isinstance(safe_text,str):
      # Always get rid of double newlines, for consistency with safe_value.
      value_to_process = re.sub(r"[\r\n]+|\r+|\n+",r"\n",original_value).rstrip()
      if safe_text == value_to_process: # no overflow
        return ""
      # If this is a string, the safe value will include an overflow message. Delete
      # the overflow message from the length of the safe value to get the starting character.
      # Note: if preserve newlines is False:
      #   1. All single and double newlines are replaced with a space
      #   2. Character count will adjust to reflect double-newlines being replaced with one char.
      # If preserve newlines is True:
      #   1. We replace all double newlines with \n.
      #   2. Character count will adjust to reflect double-newlines being replaced with one char.
      overflow_start = max(len(safe_text) - len(overflow_message), 0)
      return value_to_process[overflow_start:]

    # Do not subtract length of overflow message if this is a list of objects instead of a string
    return original_value[self.overflow_trigger:]

  def max_lines(self, input_width:int=80, overflow_message_length=0) -> int:
    """
    Estimate the number of rows in the field in the output document.
    """
    return int(max(self.overflow_trigger-overflow_message_length,0) / input_width) + 1

  def value(self) -> Any:
    """
    Return the full value, disregarding overflow. Could be useful in addendum
    if you want to show the whole value without making user flip back/forth between multiple
    pages.
    """
    return self.value_if_defined()

  def safe_value(self, overflow_message:str="", input_width:int=80, preserve_newlines:bool=False, _original_value=None):
    """
    Try to return just the portion of the variable
    that is _shorter than_ the overflow trigger. Otherwise, return empty string.
    Args:
        overflow_message (str): A short message to go on the page where text is cutoff.
        input_width (int): The width, in characters, of the input box. Defaults to 80.
        preserve_newlines (bool): Determines whether newlines are preserved in the "safe" text.
            Defaults to False, which means all newlines are removed. This allows more text to appear
            before being sent to the addendum.
        _original_value (Any): for speed reasons, you can provide the full text and just use this
            method to determine if the overflow trigger is exceeded. If no _original_value is
            provided, this method will determine it using the value_if_defined() method.
    """

    # Handle simplest case first
    if _original_value:
      value = _original_value
    else:
      value = self.value_if_defined()
    if isinstance(value, str) and len(value) <= self.overflow_trigger and (value.count('\r') + value.count('\n')) == 0:
      return value

    max_lines = self.max_lines(input_width=input_width,overflow_message_length=len(overflow_message))
    max_chars = max(self.overflow_trigger - len(overflow_message),0)

    # If there are at least 2 lines, we can ignore overflow trigger.
    # each line will be at least input_width wide
    if preserve_newlines and max_lines > 1:
      if isinstance(value, str):
        # Replace all new line characters with just \n. \r\n inserts two lines in a PDF
        value = re.sub(r"[\r\n]+|\r+|\n+",r"\n",value).rstrip()
        line = 1
        retval = ""
        paras = value.split('\n')
        para = 0
        while line <= max_lines and para < len(paras):
          # add the whole paragraph if less than width of input
          if len(paras[para]) <= input_width:
            retval += paras[para] + "\n"
            line += 1
            para += 1
          else:
            # Keep taking the first input_width characters until we hit max_lines
            # or we finish the paragraph
            while line <= max_lines and len(paras[para]):
              retval += paras[para][:input_width]
              paras[para] = paras[para][input_width:]
              line += 1
            if not len(paras[para]):
              para += 1
              retval += "\n"
        # TODO: check logic here to only add overflow message when we exceed length
        if len(paras) > para:
          return retval.rstrip() + overflow_message # remove trailing newline before adding overflow message
        else:
          return retval

    # Strip newlines from strings
    if isinstance(value, str):
      if len(value) > self.overflow_trigger:
        return re.sub(r"[\r\n]+|\r+|\n+"," ",value).rstrip()[:max_chars] + overflow_message
      else:
        return re.sub(r"[\r\n]+|\r+|\n+"," ",value).rstrip()[:max_chars]

    # If the overflow item is a list or DAList
    if isinstance(value, list) or isinstance(value, DAList):
      return value[:self.overflow_trigger]
    else:
      # We can't slice objects that are not lists or strings
      return value

  def value_if_defined(self) -> Any:
    """
    Return the value of the field if it is defined, otherwise return an empty string.
    Addendum should never trigger docassemble's variable gathering.
    """
    if defined(self.field_name):
      return value(self.field_name)
    return ""

  def __str__(self):
    return str(self.value_if_defined())

  def columns(self, skip_empty_attributes:bool=True, skip_attributes:set = {'complete'} ) -> list:
    """
    Return a list of the columns in this object.
    By default, skip empty attributes and the `complete` attribute.
    """
    if hasattr(self, 'headers'):
      return self.headers
    else:
      # Use the first row as an exemplar
      try:
        first_value = self.value_if_defined()[0]

        if isinstance(first_value, dict) or isinstance(first_value, DADict):
          return list([{key:key} for key in first_value.keys()])
        elif isinstance(first_value, DAObject):
          attr_to_ignore = {'has_nonrandom_instance_name','instanceName','attrList'}
          if skip_empty_attributes:
            return [{key:key} for key in list( set(first_value.__dict__.keys()) - set(skip_attributes) - attr_to_ignore ) if safeattr(first_value, key)]
          else:
            return [{key:key} for key in list( set(first_value.__dict__.keys()) - set(skip_attributes) - attr_to_ignore )]
      except:
        return None
      # None means the value has no meaningful columns we can extract


  def type(self) -> str:
    """
    list | object_list | other
    """
    value = self.value_if_defined()
    if isinstance(value, list) or isinstance(value, DAList):
      if len(value) and (isinstance(value[0], dict) or isinstance(value[0], DADict) or isinstance(value[0], DAObject)):
        return "object_list"
      return "list"
    return "other"

  def is_list(self) -> bool:
    """
    Identify whether the field is a list, whether of objects/dictionaries or just plain variables.
    """
    return self.type() == 'object_list' or self.type() == 'list'

  def is_object_list(self) -> bool:
    """
    Identify whether the field represents a list of either dictionaries or objects.
    """
    return self.type() == 'object_list'

  def overflow_markdown(self) -> str:
    """
    Return a formatted markdown table or bulleted list representing the values in the list.
    This method does not give you any control over the output other than labels of columns,
    but you also do not need to use this output if you want to independently control the format
    of the table.
    """
    if not self.columns():
      if self.overflow_value():
        retval = "* "
        retval += "\n* ".join(self.overflow_value())
        return retval + "\n"
      else:
        return ""

    num_columns = len(self.columns())

    header = " | ".join([list(item.items())[0][1] for item in self.columns()])
    header += "\n"
    header += "|".join(["-----"] * num_columns)

    flattened_columns = []
    for column in self.columns():
      flattened_columns.append(list(column.items())[0][0])

    rows = "\n"
    for row in self.overflow_value():
      if isinstance(row, dict) or isinstance(row, DADict):
        row_values = []
        for column in flattened_columns:
          row_values.append(str(row.get(column,'')))
        rows += "|".join(row_values)
      else:
        row_values = []
        for column in flattened_columns:
          # don't trigger collecting attributes that are required to resolve
          # to a string
          try:
            row_values.append(str(getattr(row, column,'')))
          except:
            row_values.append("")
        rows += "|".join(row_values)
      rows += "\n"

    return header + rows

  def overflow_docx(self, path:str="docassemble.ALDocumentDict:data/templates/addendum_table.docx"):
    """
    Light wrapper around insert_docx_template() that inserts a formatted table into a docx
    file. If the object in the list is a plain string/int, it returns a bulleted list.
    Using this method will not give you any control at all over the formatting, but you can directly
    call field.overflow_value() instead of using this method.
    """
    return include_docx_template(path, columns=self.columns(), rows=self.overflow_value())

class ALAddendumFieldDict(DAOrderedDict):
  """
  Object representing a list of fields in your output document, together
  with the character limit for each field.
  Provides convenient methods to determine if an addendum is needed and to
  control the display of fields so the appropriate text (overflow or safe amount)
  is displayed in each context.
  Adding a new entry will implicitly set the `field_name` attribute of the field.
  optional:
    - style: if set to "overflow_only" will only display the overflow text
  """
  def init(self, *pargs, **kwargs):
    super(ALAddendumFieldDict, self).init(*pargs, **kwargs)
    self.object_type = ALAddendumField
    self.auto_gather=False
    if not hasattr(self, 'style'):
      self.style = 'overflow_only'
    if hasattr(self, 'data'):
      self.from_list(self.data)
      del self.data

  def initializeObject(self, *pargs, **kwargs):
    """
    When we create a new entry implicitly, make sure we also set the .field_name
    attribute to the key name so it knows its own field_name.
    """
    the_key = pargs[0]
    super().initializeObject(*pargs, **kwargs)
    self[the_key].field_name = the_key

  def from_list(self, data):
    for entry in data:
      new_field = self.initializeObject(entry['field_name'], ALAddendumField)
      new_field.field_name = entry['field_name']
      new_field.overflow_trigger = entry['overflow_trigger']

  def defined_fields(self, style='overflow_only'):
    """
    Return a filtered list of just the defined fields.
    If the "style" is set to overflow_only, only return the overflow values.
    """
    if style == 'overflow_only':
      return [field for field in self.values() if len(field.overflow_value())]
    else:
      return [field for field in self.values() if defined(field.field_name)]

  def overflow(self):
    return self.defined_fields(style='overflow_only')
  
  def has_overflow(self)->bool:
    """Returns True if any defined field's length exceeds the overflow trigger.
    Returns:
      bool: True if at least 1 field has "overflow" content, False otherwise.
    """
    for field in self.values():
      if field.overflow_value():
        return True
    return False      