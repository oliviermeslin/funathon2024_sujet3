"""
Utils.
"""
from typing import Dict, Optional, List
from FlightRadar24 import FlightRadar24API
import math
import numpy as np

def fetch_flight_data(
    client: FlightRadar24API,
    airline_icao: Optional[str] = None,
    aircraft_type: Optional[str] = None,
    zone_str: Optional[str] = None
) -> List[Dict]:
    """
    Fetch flight data from FlightRadar24 API for
    a given airline, aircraft type and zone.

    Args:
        client (FlightRadar24API): FlightRadar24API client.
        airline_icao (str): ICAO code of the airline.
        aircraft_type (str): Type of aircraft.
        zone_str (str): Zone string.

    Returns:
        List[Dict]: List of flights. A flight should be represented
            as a dictionary with latitude, longitude and id keys.
    """
    zone = client.get_zones()[zone_str]
    bounds = client.get_bounds(zone)

    flights = client.get_flights(
        aircraft_type=aircraft_type,
        airline=airline_icao,
        bounds=bounds
    )
    return [
        {
            "latitude": flight.latitude,
            "longitude": flight.longitude,
            "id": flight.id,
        } for flight in flights
    ]


def update_rotation_angles(data: List[Dict], previous_data: List[Dict]) -> None:
    """
    Update flights data by adding a rotation angle key.

    Args:
        data (List[Dict]): Flight data at time $t$ containing dictionaries
            with longitude, latitude and id keys.
        previous_data (List[Dict]): Flight data at time $t-1$ containing dictionaries
            with longitude, latitude and id keys.
    """
    for idx, flight_data in enumerate(data):
        identifier = flight_data["id"]
        if identifier not in [data["id"] for data in previous_data]:
            bearing = 0
        else:
            previous_flight_data = next(item for item in previous_data if item["id"] == identifier)
            longitude = flight_data["longitude"]
            latitude = flight_data["latitude"]
            previous_longitude = previous_flight_data["longitude"]
            previous_latitude = previous_flight_data["latitude"]

            # If no change keep previous bearing
            if (longitude == previous_longitude) & (latitude == previous_latitude):
                bearing = previous_flight_data["rotation_angle"]
            else:
                bearing = bearing_from_positions(
                    longitude,
                    latitude,
                    previous_longitude,
                    previous_latitude,
                )

        flight_data.update(rotation_angle=bearing)
    return


def bearing_from_positions(
    longitude: float,
    latitude: float,
    previous_longitude: float,
    previous_latitude: float,
) -> float:
    """
    Compute bearing from two sets of coordinates, at
    t-1 and t. Bearing is measured clockwise from the north.

    Args:
        longitude (float): Longitude (in degrees).
        latitude (float): Latitude (in degrees).
        previous_longitude (float): Previous longitude (in degrees).
        previous_latitude (float): Previous latitude (in degrees).

    Returns:
        float: Bearing in degrees.
    """

    # Convert coordinates to radians
    lat1  = previous_latitude  * math.pi / 180
    long1 = previous_longitude * math.pi / 180
    lat2  = latitude * math.pi / 180
    long2 = longitude * math.pi / 180

    # Computing angle
    y = math.sin(long2 - long1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(long2 - long1)
    angle = math.atan2(y, x)

    # Getting a positive angle
    angle = (math.degrees(angle) + 360) % 360

    return(angle)


def get_closest_round_angle(angle: float) -> int:
    """
    Get closest round angle (multiple of 15 degrees)
    to the given angle.

    Args:
        angle (float): Given angle.

    Returns:
        int: Closest angle among the following values:
            0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150,
            165, 180, 195, 210, 225, 240, 255, 270,
            285, 300, 315, 330, 345.
    """
    
    round_angles = [
        0, 15, 30, 45, 60, 75, 90,
        105, 120, 135, 150, 165, 180,
        195, 210, 225, 240, 255, 270,
        285, 300, 315, 330, 345, 360,
    ]
    differences = np.array([
        angle - round_angle for round_angle in round_angles
    ])
    abs_differences = np.abs(differences)
    closest_angle_idx = abs_differences.argmin()
    closest_angle = round_angles[closest_angle_idx]
    if closest_angle == 360:
        return 0
    else:
        return closest_angle


def get_custom_icon(round_angle: int) -> Dict:
    """
    Get custom plane icon corresponding to the
    given round_angle.

    Args:
        round_angle (int): Round angle.

    Returns:
        Dict: Icon dict.
    """
    if round_angle not in [
        0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180,
        195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345
    ]:
        raise ValueError(
            "The round angle provided is not valid. "
            "Use the `get_closest_round_angle` function to get a valid angle."
        )
    icon_url = f'https://github.com/tomseimandi/flightradar/blob/main/img/plane_{round_angle}.png?raw=true'
    return dict(
        iconUrl=icon_url,
        iconSize=[38, 38],
    )
