import json
import os

def load_mock_flights():
    """Loads flight data from the JSON file."""
    # Resolve the path to data/mock_flights.json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "mock_flights.json")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("flights", [])
    except Exception as e:
        print(f"Error loading {json_path}: {e}")
        return []

def get_flight_status(flight_code: str, date: str) -> dict:
    """
    Search for a flight in the mock database by flight code and departure date.
    Note: date should be in 'YYYY-MM-DD' format.
    """
    flights = load_mock_flights()
    # Normalize inputs
    f_code = flight_code.strip().upper()
    
    for flight in flights:
        if flight["flight_code"].upper() == f_code:
            # Check if the date matches the scheduled departure time
            sched_time = flight.get("scheduled_departure_time", "")
            if date in sched_time:
                return flight
    
    return None
