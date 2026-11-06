"""
Lab 7 - Fuzz testing highway_toll.py with Hypothesis.

How to read this file
---------------------
Each test states a PROPERTY: something that must hold for every input.
Hypothesis then generates hundreds of inputs per test and tries to break it.
When it succeeds, it shrinks the input to the smallest failing example and
prints that as "Falsifying example".

The tests look for two kinds of bug:

1. Crashes: the function raises an exception on bad input.
   (test_*_no_crash*)
2. Silent wrong answers: the function returns a value for input it should have
   rejected, such as a negative trip cost. A "does it crash?" test can never
   catch these, so they get their own properties. (test_*_rejects_*)

The test_*_accepts_valid_* and test_axle_class_classifies_* tests guard the
other direction: a "fix" that rejected everything would pass every test above,
so these make sure good input still gives the right answer.

The agreed contract for invalid input: return None and never raise.

Run with:  python -m pytest test_highway_toll.py
"""

import string

from hypothesis import given, settings, strategies as st

from highway_toll import parse_plate, trip_cost, axle_class

# Shared settings for every test.
#   max_examples=500 : the default is 100; more inputs means more edge cases.
#   deadline=None    : Hypothesis normally fails any example slower than 200 ms.
#                      A slow laptop could trip that with no real bug, so it is
#                      switched off to keep failures meaningful.
FUZZ = settings(max_examples=500, deadline=None)

# ---------------------------------------------------------------------------
# Input generators ("strategies")
# ---------------------------------------------------------------------------
# Plain st.text() rarely produces something shaped like "KA-05-AB-1234", so it
# mostly fails at the first split() and never reaches the int() calls behind it.
# These generators build "almost valid" input that gets deeper into the code.

# Characters chosen because each one is awkward for int() or upper():
#   ٣  Arabic-Indic digit 3: int() silently accepts it
#   ²  superscript 2: str.isdigit() says True, but int() raises ValueError
#   _  int("1_000") is legal Python syntax, but is not a sensible plate or count
#   +  int("+5") is accepted
#   whitespace: int(" 5 ") is accepted
TRICKY_CHARS = "0123456789٣²_+-. \t\n"

# 1 to 6 hyphen-separated chunks, so the "exactly 4 parts" rule gets tested from
# both sides, and 4-part values reach the int() conversions.
PLATE_LIKE = st.lists(
    st.text(alphabet="KAab" + TRICKY_CHARS, max_size=4),
    min_size=1,
    max_size=6,
).map("-".join)

# "<chunk><separator><chunk>", where the separator may be missing or doubled.
TRIP_LIKE = st.builds(
    lambda count, separator, rate: count + separator + rate,
    st.text(alphabet=TRICKY_CHARS, max_size=5),
    st.sampled_from(["x", "X", "xx", "", "*"]),
    st.text(alphabet=TRICKY_CHARS, max_size=5),
)

AXLE_LIKE = st.text(alphabet=TRICKY_CHARS, max_size=6)

# Values of the wrong type altogether, including the float special values:
# int(float("inf")) raises OverflowError and int(float("nan")) raises ValueError.
WRONG_TYPES = st.one_of(
    st.floats(),
    st.booleans(),
    st.binary(max_size=8),
    st.lists(st.integers(), max_size=3),
    st.dictionaries(st.text(max_size=3), st.integers(), max_size=2),
)


def assert_no_crash(function, value):
    """Call function(value) and turn any exception into a clear test failure."""
    try:
        function(value)
    except Exception as error:
        assert False, (
            f"{function.__name__}({value!r}) crashed with "
            f"{type(error).__name__}: {error}"
        )


# ---------------------------------------------------------------------------
# parse_plate
# ---------------------------------------------------------------------------

@FUZZ
@given(st.text() | st.none())
def test_parse_plate_no_crash(s):
    """Any string, or None, must never crash parse_plate."""
    assert_no_crash(parse_plate, s)


@FUZZ
@given(PLATE_LIKE)
def test_parse_plate_no_crash_on_plate_like_text(s):
    """Plate-shaped text with bad fields must not crash the int() conversions."""
    assert_no_crash(parse_plate, s)


@FUZZ
@given(
    st.text(alphabet=string.ascii_letters, min_size=2, max_size=2),
    st.integers(min_value=1, max_value=99),
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=3),
    st.integers(min_value=1, max_value=9999),
)
def test_parse_plate_accepts_valid_plates(state, district, series, number):
    """A correct plate returns (STATE in capitals, district, number)."""
    plate = f"{state}-{district:02d}-{series}-{number:04d}"
    assert parse_plate(plate) == (state.upper(), district, number)


@FUZZ
@given(
    st.sampled_from(["00", "٣", "٠٥", "1_0", "+5", " 5", "123"]),
    st.sampled_from(["0000", "٣٣", "1_000", "+12", "12345"]),
)
def test_parse_plate_rejects_bad_numeric_fields(district, number):
    """
    These all pass the buggy code's int() call, so nothing crashes: it just
    returns a wrong answer. The hardened code must return None instead.
    """
    assert parse_plate(f"KA-{district}-AB-{number}") is None


# ---------------------------------------------------------------------------
# trip_cost
# ---------------------------------------------------------------------------

@FUZZ
@given(st.text() | st.none())
def test_trip_cost_no_crash(s):
    """Any string, or None, must never crash trip_cost."""
    assert_no_crash(trip_cost, s)


@FUZZ
@given(TRIP_LIKE)
def test_trip_cost_no_crash_on_trip_like_text(s):
    """Text shaped like '<count>x<rate>' must not crash the int() conversions."""
    assert_no_crash(trip_cost, s)


@FUZZ
@given(
    st.integers(min_value=0, max_value=999_999_999),
    st.sampled_from(["x", "X", " x ", " X "]),
    st.integers(min_value=0, max_value=999_999_999),
)
def test_trip_cost_accepts_valid_trips(count, separator, rate):
    """A correct trip string returns count multiplied by rate."""
    assert trip_cost(f"{count}{separator}{rate}") == count * rate


@FUZZ
@given(
    st.integers(max_value=-1),
    st.integers(min_value=0, max_value=1000),
    st.booleans(),
)
def test_trip_cost_rejects_negative_values(negative, positive, negative_first):
    """
    The buggy code returns a negative price for '-3x150', with no crash at all.
    A negative count or rate must be rejected in either position.
    """
    if negative_first:
        text = f"{negative}x{positive}"
    else:
        text = f"{positive}x{negative}"
    assert trip_cost(text) is None


@FUZZ
@given(st.integers(min_value=10, max_value=6000))
def test_trip_cost_rejects_absurdly_long_numbers(digit_count):
    """
    Numbers over 9 digits are rejected. Python 3.11+ makes int() raise ValueError
    above 4300 digits; older versions convert them slowly, a denial-of-service
    risk. The limit makes both cases safe.
    """
    assert trip_cost("9" * digit_count + "x2") is None


# ---------------------------------------------------------------------------
# axle_class
# ---------------------------------------------------------------------------

@FUZZ
@given(st.text() | st.none())
def test_axle_class_no_crash(s):
    """Any string, or None, must never crash axle_class."""
    assert_no_crash(axle_class, s)


@FUZZ
@given(AXLE_LIKE)
def test_axle_class_no_crash_on_number_like_text(s):
    """Text that nearly looks like a number must not crash int()."""
    assert_no_crash(axle_class, s)


@FUZZ
@given(WRONG_TYPES)
def test_axle_class_no_crash_on_wrong_types(value):
    """Floats (inf and nan included), bytes, lists and dicts must not crash."""
    assert_no_crash(axle_class, value)


@FUZZ
@given(st.integers(min_value=2, max_value=99), st.booleans())
def test_axle_class_classifies_valid_counts(axles, as_text):
    """2 is a car, 3-4 a truck, 5+ heavy, whether given as an int or as text."""
    if axles == 2:
        expected = "car"
    elif axles <= 4:
        expected = "truck"
    else:
        expected = "heavy"
    assert axle_class(str(axles) if as_text else axles) == expected


@FUZZ
@given(st.integers(max_value=1), st.booleans())
def test_axle_class_rejects_impossible_counts(axles, as_text):
    """
    The buggy code's `n <= 4` check labels 1, 0 and -7 axles as 'truck', with no
    crash at all. No vehicle has fewer than 2 axles, so these must be rejected.
    """
    assert axle_class(str(axles) if as_text else axles) is None
