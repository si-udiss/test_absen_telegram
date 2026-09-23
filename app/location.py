from math import (
    radians,
    sin,
    cos,
    sqrt,
    atan2
)


EARTH_RADIUS = 6_371_000


def calculate_distance(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float
) -> float:

    latitude1 = radians(latitude1)
    latitude2 = radians(latitude2)

    delta_latitude = radians(
        latitude2 - latitude1
    )

    delta_longitude = radians(
        longitude2 - longitude1
    )

    a = (
        sin(delta_latitude / 2) ** 2
        +
        cos(latitude1)
        * cos(latitude2)
        * sin(delta_longitude / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return EARTH_RADIUS * c