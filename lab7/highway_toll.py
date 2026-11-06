"""
Highway toll helpers, hardened after fuzz testing with Hypothesis (Lab 7).

The rule for every function: invalid input returns None and never raises.
Callers therefore need only one check (`if result is None`) and no try/except.

Why regular expressions instead of int() inside try/except?
int() is far more generous than this input format should be. It accepts
int("٣") == 3, int("1_000") == 1000, int("+5") == 5 and int(" 5 ") == 5.
Catching exceptions would stop the crashes but still let those through as wrong
answers. A regex describes exactly what is allowed and rejects the rest.

Three details in the patterns below matter:
  * re.ASCII       makes \\d and \\s match ASCII only, so "٣" is not a digit.
  * re.fullmatch   must match the whole string, so trailing junk fails.
  * \\d{1,9}        caps the length, so int() never sees a huge digit string.
"""

import re

# <state>-<district>-<series>-<number>, e.g. KA-05-AB-1234.
# [A-Za-z] is spelled out because upper() has surprises outside ASCII:
# "ß".upper() == "SS" turns one character into two.
PLATE_PATTERN = re.compile(
    r"\s*([A-Za-z]{2})-(\d{1,2})-[A-Za-z]{1,3}-(\d{1,4})\s*",
    re.ASCII,
)

# <count>x<rate>, e.g. 3x150. There is no sign in the pattern, so negative
# values are rejected. Spaces around the numbers are allowed, as "3 x 150" is
# a natural thing to type.
TRIP_PATTERN = re.compile(r"\s*(\d{1,9})\s*[xX]\s*(\d{1,9})\s*", re.ASCII)

# A whole number of axles given as text, e.g. "3".
AXLE_PATTERN = re.compile(r"\s*(\d{1,9})\s*", re.ASCII)

MIN_AXLES = 2   # No road vehicle has fewer than 2 axles.
MAX_AXLES = 99  # Sanity limit, so nonsense like 10**100 is not called 'heavy'.


def parse_plate(plate):
    """
    Return (STATE, district, number) for a plate such as 'KA-05-AB-1234'.
    Return None if the plate is not valid.
    """
    # Without this check, None or 123 would crash the regex with TypeError.
    if not isinstance(plate, str):
        return None

    match = PLATE_PATTERN.fullmatch(plate)
    if match is None:
        return None

    state, district, number = match.group(1), int(match.group(2)), int(match.group(3))

    # The regex allows "00" and "0000", but neither is ever issued on a plate.
    if district < 1 or number < 1:
        return None

    return state.upper(), district, number


def trip_cost(text):
    """
    Return count * rate for text such as '3x150'.
    Return None if the text is not valid.
    """
    if not isinstance(text, str):
        return None

    match = TRIP_PATTERN.fullmatch(text)
    if match is None:
        return None

    return int(match.group(1)) * int(match.group(2))


def axle_class(axles):
    """
    Return 'car' (2 axles), 'truck' (3-4) or 'heavy' (5+).
    Accepts an int or a numeric string. Return None for anything else.
    """
    # bool is checked first because it is a subclass of int in Python: without
    # this, True would quietly count as 1 axle.
    if isinstance(axles, bool):
        return None

    if isinstance(axles, int):
        count = axles
    elif isinstance(axles, str):
        match = AXLE_PATTERN.fullmatch(axles)
        if match is None:
            return None
        count = int(match.group(1))
    else:
        # float is rejected deliberately: int(3.7) would silently become 3, and
        # int(float("inf")) raises OverflowError.
        return None

    # This range check fixes the original logic bug, where `n <= 4` also
    # labelled 1, 0 and negative axle counts as 'truck'.
    if count < MIN_AXLES or count > MAX_AXLES:
        return None

    if count == 2:
        return 'car'
    if count <= 4:
        return 'truck'
    return 'heavy'


def ask(prompt):
    """
    Read one line of input. Return None if input ends (Ctrl+Z / Ctrl+D, or a
    piped file running out) or the user presses Ctrl+C, instead of crashing.
    """
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def main():
    print("==== Running parse_plate ====")
    user_input = ask("Enter a plate (e.g. KA-05-AB-1234): ")
    result = parse_plate(user_input)
    if result is None:
        print("Invalid plate. Expected a format like KA-05-AB-1234.")
    else:
        print("State, District and Number:", result)

    print("\n==== Running trip_cost ====")
    user_input = ask("Enter trips x rate (e.g. 3x150): ")
    result = trip_cost(user_input)
    if result is None:
        print("Invalid trip. Expected non-negative whole numbers like 3x150.")
    else:
        print("Trip Cost:", result)

    print("\n==== Running axle_class ====")
    user_input = ask("Enter an axle count (e.g. 3): ")
    result = axle_class(user_input)
    if result is None:
        print(f"Invalid axle count. Expected a whole number from {MIN_AXLES} to {MAX_AXLES}.")
    else:
        print("Vehicle Class:", result)


if __name__ == "__main__":
    main()
