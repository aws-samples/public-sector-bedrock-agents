# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import Dict, List, Union
import requests
from urllib3.util import parse_url

from aws_lambda_powertools import Logger
logger = Logger()

class WeatherForecast:
    BASE_URL = "https://api.weather.gov"
    ALLOWED_HOSTS = ["api.weather.gov"]

    def __init__(self, latitude: float, longitude: float):
        # Add input validation
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise Exception("Invalid latitude or longitude value")
        self.latitude = latitude
        self.longitude = longitude

    def get_forecast(self, num_periods: int = None) -> List[Dict[str, Union[str, int, float]]]:
        json_data = self._fetch_forecast_data()
        return self._get_periods(json_data, num_periods)

    def _fetch_forecast_data(self) -> Dict:
        """Fetch forecast data from the API."""
        grid_forecast_endpoint = f"{self.BASE_URL}/points/{self.latitude},{self.longitude}"

        try:
            grid_forecast_response = self._make_request(grid_forecast_endpoint)
            local_forecast_endpoint = grid_forecast_response['properties']['forecast']
            return self._make_request(local_forecast_endpoint)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching forecast data: {e}")
            raise

    def _make_request(self, url: str) -> Dict:
        """Make a request to the given URL and return the JSON response."""
        host = parse_url(url).host
        if host not in self.ALLOWED_HOSTS:
            raise Exception(f"URL not allowed: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raises an HTTPError if the status code is 4xx or 5xx
            
            # Process the response if successful
            return response.json()

        except requests.exceptions.HTTPError as err:
            logger.error(f"HTTP error occurred: {err}")
        except requests.exceptions.RequestException as err:
            logger.error(f"An error occurred: {err}")        

    def _get_periods(self, json_data: Dict, num_periods: int = None) -> List[Dict[str, Union[str, int, float]]]:
        """Extract forecast periods from the JSON data."""
        if not isinstance(json_data, dict):
            raise Exception("Invalid json_data: expected a dictionary")

        properties = json_data.get('properties', {})
        periods = properties.get('periods', [])

        if not isinstance(periods, list):
            raise Exception("Invalid data structure: 'periods' is not a list")

        if num_periods is not None:
            if not isinstance(num_periods, int) or num_periods < 0:
                raise Exception("num_periods must be a non-negative integer")
            return periods[:num_periods]

        return periods