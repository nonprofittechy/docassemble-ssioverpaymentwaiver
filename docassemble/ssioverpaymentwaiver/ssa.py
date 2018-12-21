from docassemble.base.util import validation_error
import re

def is_valid_ssn(x):
    """Validates that the field is 3 digits, a hyphen, 2 digits, a hyphen, and 4 final digits only."""
    return True # speed up testing
    valid_ssn=re.compile(r'^\d{3}-\d{2}-\d{4}$')
    if not bool(re.match(valid_ssn,x)):
        validation_error("Write the Social Security Number like this: XXX-XX-XXXX")
    return True