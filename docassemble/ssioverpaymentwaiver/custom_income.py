def generate_income_list() -> list:
  return [
    "SSDI",
    "SSR",
    "SSI",
    "other Social Security benefits",
    "pension",
    "SNAP",
    "rent",
    "room and board",
    "child support",
    "alimony",
    "other support",
    "other"
  ]

def income_types_map() -> dict:
  return {
    "SSDI": "Social Security Disability Benefits",
    "SSR": "Social Security Retirement Benefits",
    "SSI": "Supplemental Security Income (SSI)",
    "other Social Security benefits": "other Social Security benefits [TODO]",
    "pension": "Pension",
    "SNAP": "Food Stamps (SNAP)",
    "rent": "Income from real estate (rent, etc)",
    "room and board": "Room and/or Board Payments",
    "child support": "Child Support",
    "alimony": "Alimony",
    "other support": "Other Support",
    "other": "Other"
  }

def expense_types() -> list:
  return {
    "rent": "Rent",
    "mortgate": "Mortgage",
    "food": "Food",
    "utilities": "Utilities",
    "fuel": "Other Heating/Cooking Fuel",
    "clothing": "Clothing",
    "household items": "Household items (such as hygiene)",
    "property tax": "Property Tax (State and Local)",
    "insurance": "Insurance",
    "medical": "Medical-Dental (after amount paid by insurance)",
    "car loan": "Car Loan/Lease",
    "car expenses": "Car operation and maintenance",
    "transporation": "Other transportation",
    "school": "Tuition and School Expenses",
    "court order": "Court Ordered Payments Paid Directly to the Court",
    "credit card": "Credit Card Payments (minimum monthly payment, excluding other expenses)",
    "other": "Other"
  }