import pytest
from app.location import calculate_distance
from app.config import CAMPUS_LATITUDE, CAMPUS_LONGITUDE, CAMPUS_RADIUS


def test_distance_same_coordinates():
    # Jarak titik yang sama harus 0
    dist = calculate_distance(-6.123456, 107.123456, -6.123456, 107.123456)
    assert dist < 1.0  # Mendekati 0


def test_distance_inside_radius():
    # Koordinat yang sangat dekat (dalam radius)
    # 0.0001 derajat sekitar 11 meter
    lat2 = CAMPUS_LATITUDE + 0.0001
    lon2 = CAMPUS_LONGITUDE
    
    dist = calculate_distance(CAMPUS_LATITUDE, CAMPUS_LONGITUDE, lat2, lon2)
    assert dist > 0
    assert dist <= CAMPUS_RADIUS


def test_distance_outside_radius():
    # Koordinat yang jauh (luar radius)
    # 0.01 derajat sekitar 1.1 km
    lat2 = CAMPUS_LATITUDE + 0.01
    lon2 = CAMPUS_LONGITUDE
    
    dist = calculate_distance(CAMPUS_LATITUDE, CAMPUS_LONGITUDE, lat2, lon2)
    assert dist > CAMPUS_RADIUS


def test_realistic_meter_calculation():
    # Jarak Monas ke Bundaran HI kira-kira 2.5km (2500m)
    # Monas: -6.175392, 106.827153
    # Bundaran HI: -6.194770, 106.823026
    dist = calculate_distance(-6.175392, 106.827153, -6.194770, 106.823026)
    
    # Toleransi antara 2.0km dan 2.5km karena jarak udara
    assert 2000 < dist < 2500
