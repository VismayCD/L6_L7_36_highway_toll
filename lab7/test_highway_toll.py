from hypothesis import given, strategies as st
from highway_toll import parse_plate, trip_cost, axle_class

@given(st.text() | st.none())
def test_parse_plate_no_crash(s):

@given(st.text() | st.none())
def test_trip_cost_no_crash(s):

@given(st.text() | st.none())
def test_axle_class_no_crash(s):
