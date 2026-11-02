"""
Lab 6 - CODE (LINE) COVERAGE tests for highway_toll.py

Goal of this file
-----------------
Line coverage asks one question: "Did this line run at least once?"
So this file is deliberately small. Each test exists to reach specific lines
that nothing else reaches, and the comment above each test names those lines.

How to run (from inside the lab6 folder)
----------------------------------------
    coverage run -m pytest CodeCoverageTest_597_highway_toll.py
    coverage report -m

What highway_toll.py does
-------------------------
    Base toll : 2 axles = 100, 3 axles = 150, 4 axles = 250, 5 or more = 400
    Peak hours: base x 1.25
    FASTag    : x 0.90 for 2 axles, x 0.95 for everything else
    Exempt    : ambulance and fire_engine pay 0
"""

import pytest

from highway_toll import pass_advice, toll_charge, toll_for

# Two off-peak, no-tag trips on a 2-axle vehicle cost 100 + 100 = 200.
# The pass_advice tests compare this known cost against different pass prices.
TWO_PLAIN_TRIPS = [(False, False), (False, False)]


# ---------------------------------------------------------------------------
# Starter tests supplied with the lab
# ---------------------------------------------------------------------------

def test_ambulance_is_exempt():
    # Lines 23-24: an exempt vehicle returns 0 immediately.
    assert toll_charge("ambulance", 2, False, False) == 0


def test_two_axle_base_toll():
    # Lines 6, 8, 9, 12, 14, 19: the straight path through toll_for.
    assert toll_for(2, False, False) == 100


# ---------------------------------------------------------------------------
# toll_for: lines the starter tests never reach
# ---------------------------------------------------------------------------

def test_invalid_axle_count_raises_error():
    # Line 7: fewer than 2 axles is rejected.
    # pytest.raises passes only if the ValueError is actually raised, and
    # match= also checks the error message.
    with pytest.raises(ValueError, match="invalid axle count"):
        toll_for(1, False, False)


def test_axle_count_missing_from_table_uses_flat_rate():
    # Line 11: 5 axles is not in BASE_TOLL, so the else branch sets 400.
    assert toll_for(5, False, False) == 400


def test_peak_hours_add_25_percent():
    # Line 13: 100 x 1.25 = 125.
    assert toll_for(2, True, False) == 125


def test_fastag_gives_two_axle_vehicle_10_percent_off():
    # Lines 15-16: 100 x 0.90 = 90.
    assert toll_for(2, False, True) == 90


def test_fastag_gives_larger_vehicle_5_percent_off():
    # Line 18: 150 x 0.95 = 142.5.
    assert toll_for(3, False, True) == 142.5


# ---------------------------------------------------------------------------
# toll_charge: the non-exempt line
# ---------------------------------------------------------------------------

def test_ordinary_vehicle_pays_normal_toll():
    # Line 25: a vehicle not in EXEMPT is passed on to toll_for.
    assert toll_charge("car", 2, False, False) == 100


# ---------------------------------------------------------------------------
# pass_advice: one test for each of the three return statements
# ---------------------------------------------------------------------------

def test_advice_is_buy_pass_when_trips_cost_more():
    # Lines 29-33: trips cost 200 and the pass costs 150.
    assert pass_advice(TWO_PLAIN_TRIPS, 2, 150) == "buy_pass"


def test_advice_is_either_when_costs_are_equal():
    # Lines 34-35: trips cost 200 and the pass costs 200.
    assert pass_advice(TWO_PLAIN_TRIPS, 2, 200) == "either"


def test_advice_is_pay_per_trip_when_trips_cost_less():
    # Line 36: trips cost 200 and the pass costs 500.
    assert pass_advice(TWO_PLAIN_TRIPS, 2, 500) == "pay_per_trip"
