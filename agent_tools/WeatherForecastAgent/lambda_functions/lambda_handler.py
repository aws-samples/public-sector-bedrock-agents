# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This module provides a set of functions to retrieve weather forecasts and point coordinates
for a given location. It uses the WeatherForecast and PlaceIndexService classes from the
weather and geolocation modules, respectively.

The module also includes an AWS Lambda handler function that leverages the
Bedrock Agent Resolver from AWS Lambda PowerTools to automatically resolve and inject
dependencies into the Lambda function handler.
"""

from typing import Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from datetime import datetime, timezone

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from urllib.parse import quote as escape, unquote as unescape
from typing import Callable

from weather import WeatherForecast
from geolocation import PlaceIndexService

tracer = Tracer(service="WeatherForecastAgent")
logger = Logger()
app = BedrockAgentResolver()

@app.get(
    "/forecast",
    summary="Get Forecast",
    operation_id="get_forecast",
    description="Returns the weather forecast for a given location.",
)
@tracer.capture_method
def get_forecast(
    latitude: float = Query(..., description="Latitude of the location."),
    longitude: float = Query(..., description="Longitude of the location."),
    num_forecast_periods: Optional[int] = Query(None, description="Number of forecast periods to return. Two periods is a full day (Day and Night). Maximum is 5."),
) -> dict:
    """
    Returns the weather forecast for a given location.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        num_forecast_periods (Optional[int]): Number of forecast periods to return.

    Returns:
        dict: A dictionary containing the status code and the weather forecast.
    """

    # Log API call
    logger.info(
        f"Retrieving weather data for location: {latitude}, {longitude}"
    )

    # Fetch the weather forecast via API endpoint
    weather = WeatherForecast(latitude, longitude)
    forecast = weather.get_forecast(num_forecast_periods)
  
    # Log retrieved data
    logger.info(
        f"Returning weather data for location: {latitude}, {longitude}. Forecast: {forecast}"
    )

    return {"statusCode": 200, "body": forecast}

@app.get(
    "/get-datetime",
    summary="Get Current Date and Time",
    operation_id="get_current_datetime",
    description="Returns the current date, time, and day of the week.",
)
@tracer.capture_method
def get_current_datetime() -> dict:
    """
    Returns the current date, time, and day of the week.

    Returns:
        dict: A dictionary containing the current date, time, and day of the week.
    """
    now = datetime.now(timezone.utc)
    return {
        'statusCode': 200,
        'body': {
            'date': now.strftime("%m/%d/%Y"),
            'time': now.strftime("%H:%M:%S"),
            'day': now.strftime("%A")
        }
    }

@app.get(
    "/coords",
    summary="Get Point Coordinates",
    operation_id="get_point_coordinates",
    description="Returns the longitude and latitude for a free-form location search.",
)
@tracer.capture_method
def get_point_coordinates(
    location_description: str = Query(..., description="Location description to search for.")
) -> dict:
    """
    Returns the longitude and latitude for a given location description.

    Args:
        location_description (str): Location description to search for.

    Returns:
        dict: A dictionary containing the status code and the point coordinates.
    """
    place_index_service = PlaceIndexService(index_name="My-Demo-Place-Index", description="My Demo Place Index")
    try:
        coordinates = place_index_service.get_point_coordinates(unescape(location_description))
        return {"statusCode": 200, "body": coordinates}
    except Exception as e:
        logger.error(f"Error getting coordinates for {unescape(location_description)}: {str(e)}")
        return {"statusCode": 500, "body": {"error": "Failed to retrieve coordinates"}}

# Adding function to escape all query string parameters
@lambda_handler_decorator
def escape_query_params(
    handler: Callable[[dict, LambdaContext], dict],
    event: dict, 
    context: LambdaContext
) -> dict:
    """Middleware that escapes all query string parameters."""
    
    # GET parameters
    parameters = event.get('parameters', [])
    if parameters:
        escaped_params = []
        for param in parameters:
            escaped_name = escape(param.get('name', ''))
            escaped_value = escape(param.get('value', ''))
            escaped_param = {
                'name': escaped_name,
                'type': param.get('type', ''),
                'value': escaped_value
            }
            escaped_params.append(escaped_param)
        
        # Update event with escaped parameters
        event["parameters"] = escaped_params
        logger.debug(f"Escaped query parameters: {event['parameters']}")

    return handler(event, context)

@escape_query_params
@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """
    AWS Lambda handler function.

    Args:
        event (dict): The event data received by the Lambda function.
        context (LambdaContext): The Lambda context object.

    Returns:
        dict: The response from the Lambda function.
    """
    return app.resolve(event, context)

if __name__ == "__main__":
    print(
        app.get_openapi_json_schema(
            title="Weather Forecast Agent",
            version="1.0.0",
            description="This API provides functionality to retrieve the weather forecast and point coordinates for US cities.",
            tags=["weather", "forecast", "coordinates"],
        )
    )