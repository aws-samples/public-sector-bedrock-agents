# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This module provides functions to interact with the National Weather Service API
and retrieve weather forecast data for a given weather station.
"""

import requests
from urllib.parse import urlparse

def get_weather_data(station_id: str) -> dict:
    # Get latest observation for the weather station
    base_url = "https://api.weather.gov/stations"
    url = f"{base_url}/{station_id}/observations/latest"
    allowed_hosts = ["api.weather.gov"]
    host = urlparse(url).netloc
    
    if host in allowed_hosts:
        response = requests.get(url, timeout=30)
    else:
        raise RuntimeError("URL is invalid")
    response.raise_for_status()

    # Parse API response
    data = response.json()

    # Extract weather info
    temperature = data['properties']['temperature']['value']
    description = data['properties']['textDescription']

    return {"temperature": temperature, "description": description, "data": data}