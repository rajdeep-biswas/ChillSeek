import os
import numpy as np
import geopy.distance
import pandas as pd
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Load API key from environment variable
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Center coordinates for Bangalore
lat_center = 12.9716
lon_center = 77.5946
radius_km = 300  # Max radius
num_points = 900  # Target number of points

# Step sizes
distance_step = np.sqrt((radius_km**2) / num_points)  # Spacing per point (~23-24 km)
angle_step = 137.5  # Golden angle for even spacing

# Generate spiral points
points = []
for i in range(num_points):
    r = distance_step * np.sqrt(i)  # Radial distance
    theta = np.radians(i * angle_step)  # Convert to radians

    if r > radius_km:  # Stop if out of radius
        break

    # Convert polar to lat/lon
    new_point = geopy.distance.distance(kilometers=r).destination((lat_center, lon_center), np.degrees(theta))
    points.append((new_point.latitude, new_point.longitude))

# Initialize geolocator
geolocator = Nominatim(user_agent="geo_spiral")

def get_address(lat, lon):
    """Fetch address for given coordinates."""
    try:
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True)
        return location.address if location else "Unknown Location"
    except GeocoderTimedOut:
        return "Timeout Error"

df["Address"] = df.apply(lambda row: get_address(row["Latitude"], row["Longitude"]), axis=1)

def get_weekly_avg_temp(weather_data):
    """Calculate weekly average max temperature from OpenWeatherMap API response."""
    try:
        daily_forecast = weather_data.get("daily", [])
        if not daily_forecast:
            return None
        max_temps_celsius = [(day["temp"]["max"] - 273.15) for day in daily_forecast]
        return sum(max_temps_celsius) / len(max_temps_celsius)
    except (KeyError, TypeError):
        return None

def get_weather_data(lat, lon):
    """Fetch weather data from OpenWeatherMap API."""
    if not API_KEY:
        return {"error": "API key not found"}
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

df["Weekly Temperature"] = df.apply(
    lambda row: get_weekly_avg_temp(get_weather_data(row["Latitude"], row["Longitude"])), axis=1
)

df.to_csv("spiral_coordinates_with_addresses_and_temperature.csv", index=False)
print("Data saved to spiral_coordinates_with_addresses_and_temperature.csv")
