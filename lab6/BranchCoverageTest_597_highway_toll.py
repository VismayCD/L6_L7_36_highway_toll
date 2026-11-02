"""
Lab 6 - BRANCH COVERAGE tests for highway_toll.py

Goal of this file
-----------------
Branch coverage asks a stricter question than line coverage: "Did every
decision go BOTH ways?" A line can run while its decision only ever goes one
way, so this file is organised by decision rather than by line.

How to run (from inside the lab6 folder)
----------------------------------------
    coverage run --branch -m pytest BranchCoverageTest_597_highway_toll.py
    coverage report -m

Decisions in highway_toll.py (9 decisions = 18 branches)
--------------------------------------------------------
    D1  line 6   if axles < 2
    D2  line 8   if axles in BASE_TOLL
    D3  line 12  if is_peak
    D4  line 14  if has_fastag
    D5  line 15  if axles == 2
    D6  line 23  if vehicle in EXEMPT
    D7  line 30  for is_peak, has_fastag in trips  (enter loop / skip loop)
    D8  line 32  if cost > pass_price
    D9  line 34  if cost == pass_price

Boundary values (for example 1 and 2 axles for D1) are used on purpose, because
off-by-one mistakes such as "<" written as "<=" only show up at the boundary.
"""

import pytest

from highway_toll import pass_advice, toll_charge, toll_for


# ---------------------------------------------------------------------------
# D1: if axles < 2
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("axles", [1, 0, -1])
def test_d1_true_too_few_axles_raises_error(axles):
    # True branch. 1 is the largest value that is still invalid.
    with pytest.raises(ValueError, match="invalid axle count"):
        toll_for(axles, False, False)


def test_d1_false_two_axles_is_the_smallest_valid_count():
    # False branch. 2 is the boundary value on the valid side.
    assert toll_for(2, False, False) == 100


# ---------------------------------------------------------------------------
# D2: if axles in BASE_TOLL
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "axles, expected_base",
    [(2, 100), (3, 150), (4, 250)],
)
def test_d2_true_axle_count_is_in_the_table(axles, expected_base):
    # True branch. Every entry in BASE_TOLL is checked.
    assert toll_for(axles, False, False) == expected_base


@pytest.mark.parametrize("axles", [5, 6, 12])
def test_d2_false_other_axle_counts_use_flat_rate(axles):
    # False branch. 5 is the first count past the end of the table.
    assert toll_for(axles, False, False) == 400


# ---------------------------------------------------------------------------
# D3, D4 and D5: is_peak, has_fastag and axles == 2 in every combination
# ---------------------------------------------------------------------------

# Each row is: axles, is_peak, has_fastag, expected toll.
# The expected values were worked out by hand from the rules, not copied from
# the program's output. For example, 4 axles at peak with a tag is:
#     250 x 1.25 x 0.95 = 296.875, which rounds to 296.88
# 3 axles at peak with a tag is 150 x 1.25 x 0.95 = 178.125, which rounds DOWN
# to 178.12. Python's round() sends an exact tie to the nearest even digit, so
# the last digit goes to 2 here and to 8 in the example above.
TOLL_COMBINATIONS = [
    # 2 axles: FASTag takes the 10% path (D5 True)
    (2, False, False, 100),
    (2, False, True, 90),
    (2, True, False, 125),
    (2, True, True, 112.5),
    # 3 axles: FASTag takes the 5% path (D5 False)
    (3, False, False, 150),
    (3, False, True, 142.5),
    (3, True, False, 187.5),
    (3, True, True, 178.12),
    # 4 axles
    (4, False, False, 250),
    (4, False, True, 237.5),
    (4, True, False, 312.5),
    (4, True, True, 296.88),
    # 5 axles: flat rate
    (5, False, False, 400),
    (5, False, True, 380),
    (5, True, False, 500),
    (5, True, True, 475),
]


@pytest.mark.parametrize("axles, is_peak, has_fastag, expected", TOLL_COMBINATIONS)
def test_d3_d4_d5_every_toll_combination(axles, is_peak, has_fastag, expected):
    # Drives D3, D4 and D5 both ways, and also checks that the peak and FASTag
    # multipliers work together rather than only on their own.
    assert toll_for(axles, is_peak, has_fastag) == expected


# ---------------------------------------------------------------------------
# D6: if vehicle in EXEMPT
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("vehicle", ["ambulance", "fire_engine"])
def test_d6_true_exempt_vehicles_pay_nothing(vehicle):
    # True branch. Peak and FASTag are on to show they make no difference.
    assert toll_charge(vehicle, 4, True, True) == 0


def test_d6_true_exemption_is_checked_before_axles():
    # An exempt vehicle returns before toll_for runs, so a bad axle count
    # does not raise an error here.
    assert toll_charge("ambulance", 1, False, False) == 0


@pytest.mark.parametrize(
    "vehicle, axles, is_peak, has_fastag, expected",
    [
        ("car", 2, False, False, 100),
        ("car", 2, True, True, 112.5),
        ("truck", 5, True, False, 500),
    ],
)
def test_d6_false_other_vehicles_pay_the_calculated_toll(
    vehicle, axles, is_peak, has_fastag, expected
):
    # False branch. The arguments must be passed on to toll_for correctly.
    assert toll_charge(vehicle, axles, is_peak, has_fastag) == expected


def test_d6_false_other_vehicle_with_bad_axles_raises_error():
    # False branch. The ValueError from toll_for reaches the caller.
    with pytest.raises(ValueError, match="invalid axle count"):
        toll_charge("car", 1, False, False)


# ---------------------------------------------------------------------------
# D7: for is_peak, has_fastag in trips
# ---------------------------------------------------------------------------

def test_d7_skip_loop_no_trips_means_zero_cost():
    # An empty list skips the loop body, so cost stays at 0.
    # This case cannot be reached by simply running every line once.
    assert pass_advice([], 2, 100) == "pay_per_trip"


def test_d7_skip_loop_zero_cost_equals_free_pass():
    # With no trips and a free pass, 0 == 0 gives "either".
    assert pass_advice([], 2, 0) == "either"


def test_d7_enter_loop_single_trip():
    # One pass through the loop: the trip costs 100.
    assert pass_advice([(False, False)], 2, 99) == "buy_pass"


def test_d7_enter_loop_adds_up_mixed_trips():
    # Each trip must use its own flags: 112.5 (peak + tag) + 100 (plain) = 212.5
    assert pass_advice([(True, True), (False, False)], 2, 212.5) == "either"


def test_d7_enter_loop_uses_the_given_axle_count():
    # Two plain 3-axle trips cost 150 + 150 = 300.
    assert pass_advice([(False, False), (False, False)], 3, 300) == "either"


def test_d7_enter_loop_invalid_axles_raises_error():
    # The loop calls toll_for, so its ValueError reaches the caller.
    with pytest.raises(ValueError, match="invalid axle count"):
        pass_advice([(False, False)], 1, 100)


# ---------------------------------------------------------------------------
# D8 and D9: if cost > pass_price, then if cost == pass_price
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "pass_price, expected",
    [
        (199, "buy_pass"),      # D8 True:                just below the cost
        (200, "either"),        # D8 False, D9 True:      exactly the cost
        (201, "pay_per_trip"),  # D8 False, D9 False:     just above the cost
    ],
)
def test_d8_d9_pass_price_around_the_trip_cost(pass_price, expected):
    # The trips always cost 200, so prices of 199, 200 and 201 test each
    # comparison right at its boundary.
    trips = [(False, False), (False, False)]
    assert pass_advice(trips, 2, pass_price) == expected
