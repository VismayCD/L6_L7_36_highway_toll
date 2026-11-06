def parse_plate(plate):
    state, district, series, number = plate.split('-')
    return state.upper(), int(district), int(number)

def trip_cost(text):
    count, rate = text.lower().split('x')
    return int(count) * int(rate)

def axle_class(axles):
    n = int(axles)
    if n == 2:
        return 'car'
    if n <= 4:
        return 'truck'
    return 'heavy'

def main():
    print("==== Running parse_plate ====")
    user_input = input("Enter a plate (e.g. KA-05-AB-1234): ")
    result = parse_plate(user_input)
    print("State, District and Number:", result)

    print("\n==== Running trip_cost ====")
    user_input = input("Enter trips x rate (e.g. 3x150): ")
    result = trip_cost(user_input)
    print("Trip Cost:", result)

    print("\n==== Running axle_class ====")
    user_input = input("Enter an axle count (e.g. 3): ")
    result = axle_class(user_input)
    print("Vehicle Class:", result)

if __name__ == "__main__":
    main()
