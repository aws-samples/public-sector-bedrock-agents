# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This module provides functions to interact with geolocation services using Amazon Location Services (ESRI).
It includes operations such as getting coordinates, searching for places, reverse geocoding, and calculating routes.
The module uses AWS Lambda PowerTools for logging, tracing, and dependency injection.
"""

import math
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from urllib.parse import quote as escape
from typing import Callable

from geolocation import PlaceIndexService, RouteService

tracer = Tracer(service="GeolocationAgent")
logger = Logger()
app = BedrockAgentResolver()

try:
    place_index_service = PlaceIndexService(index_name='My-Demo-Place-Index', description="Demo Place Index")
    route_service = RouteService(description="Demo Route Calculator")
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    raise

@app.get("/geocode",
         summary="Returns the coordinates for a given US postal address: <street number> <street name> <city>, <state> <zip code>",
         operation_id="get_point_coordinates",
         description="Returns longitude and latitude as decimal values for a given location. ALWAYS use this service for any reverse geocoding")
@tracer.capture_method
def get_point_coordinates(
    street_number: str = Query(..., description="The street number of the address. Example: '123'"),
    street_name: str = Query(..., description="The street name of the address. Example: 'Main St'"),
    city: str = Query(..., description="The city of the address. Example: 'Anytown'"),
    state: str = Query(..., description="The state of the address. Example: 'CA'"),
    zip_code: str = Query(..., description="The zip code of the address. Example: '90210'")
) -> dict:
    """
    Returns the longitude and latitude for a given location description.

    Args:
        street_number (str): The street number of the address. Example: '123'.
        street_name (str): The street name of the address. Example: 'Main St'.
        city (str): The city of the address. Example: 'Anytown'.
        state (str): The state of the address. Example: 'CA'.
        zip_code (str): The zip code of the address. Example: '90210'.

    Returns:
        dict: Coordinates or an error if not found.
    """
    postal_address = f"{street_number} {street_name}, {city}, {state} {zip_code}"
    coordinates = place_index_service.get_point_coordinates(postal_address)
    if coordinates:
        return {"status": 200, "body": coordinates}
    else:
        raise NotFoundError("Coordinates not found")

@app.get("/search",
         summary="Searches for the given text and attempts to return a US postal address: <street number> <street name> <city>, <state> <zip code>",
         operation_id="search_place_index_for_text",
         description="Searches for the given text and attempts to return a US postal address: <street number> <street name> <city>, <state> <zip code>")
@tracer.capture_method
def search_place_index_for_text(
    location_description: str = Query(..., description="Text to search for in the place index. Example: 'Statue of Liberty'")
) -> dict:
    """
    Searches the place index for the given text and attempts to return an address.

    Args:
        location_description (str): Text to search for (e.g., "Statue of Liberty").

    Returns:
        dict: Search results or an error if not found.
    """
    search_result = place_index_service.search_place_index_for_text(location_description)
    if search_result:
        return {"status": 200, "body": search_result}
    else:
        raise NotFoundError("Search result not found")

@app.get("/rev-geocode",
         summary="Reverse Geocode",
         operation_id="reverse_geocode",
         description="Returns the address for given coordinates.")
@tracer.capture_method
def reverse_geocode(
    longitude: str = Query(..., description="Longitude coordinate. Example: '-74.0060'"),
    latitude: str = Query(..., description="Latitude coordinate. Example: '40.7128'")
) -> dict:
    """
    Returns the address for a given set of coordinates.

    Args:
        longitude (str): Longitude coordinate (e.g., "-74.0060").
        latitude (str): Latitude coordinate (e.g., "40.7128").

    Returns:
        dict: Reverse geocoded address or an error if not found.
    """
    try:
        lon = float(longitude)
        lat = float(latitude)
        if math.isnan(lon) or math.isnan(lat): #import math
            raise ValueError("Input contains NaN")
        coordinate_tuple = (lon, lat)
        address = place_index_service.reverse_geocode(coordinate_tuple)
        if address:
            return {"status": 200, "body": address}
        else:
            raise NotFoundError("Address not found")
    except ValueError as e:
        raise ValueError(f"Invalid coordinate values: {e}")

@app.get("/route",
         summary="Calculate Route",
         operation_id="calculate_route",
         description="Calculates the walking or driving routes between two sets of coordinates, including distances and times.")
@tracer.capture_method
def calculate_route(
    departure_longitude: str = Query(..., description="Departure longitude coordinate. Example: '-118.2437'"),
    departure_latitude: str = Query(..., description="Departure latitude coordinate. Example: '34.0522'"),
    destination_longitude: str = Query(..., description="Destination longitude coordinate. Example: '-122.4194'"),
    destination_latitude: str = Query(..., description="Destination latitude coordinate. Example: '37.7749'"),
    travel_mode: str = Query("Car", description="Travel mode (e.g., Car, Walking). Example: 'Car'"),
    distance_unit: str = Query("Miles", description="Distance unit (e.g., Miles, Kilometers). Example: 'Miles'")
) -> dict:
    """
    Calculates the route between two sets of coordinates.

    Args:
        departure_longitude (str): Departure longitude (e.g., "-118.2437").
        departure_latitude (str): Departure latitude (e.g., "34.0522").
        destination_longitude (str): Destination longitude (e.g., "-122.4194").
        destination_latitude (str): Destination latitude (e.g., "37.7749").
        travel_mode (str): Travel mode (default is "Car"). Example: "Car".
        distance_unit (str): Distance unit (default is "Miles"). Example: "Miles".

    Returns:
        dict: Calculated route or an error if not found.
    """
    try:
        departure_long = float(departure_longitude)
        departure_lat = float(departure_latitude)
        destination_long = float(destination_longitude)
        destination_lat = float(destination_latitude)
        
        if math.isnan(departure_long) or math.isnan(departure_lat) or math.isnan(destination_long) or math.isnan(destination_lat): 
            raise ValueError("Input contains NaN")
        
        departure_position = (departure_long, departure_lat)
        destination_position = (destination_long, destination_lat)
        route = route_service.calculate_route(route_service.calculator_name, departure_position, destination_position, travel_mode, distance_unit)
        if route:
            return {"status": 200, "body": route}
        else:
            raise NotFoundError("Route not found")
    except ValueError as e:
        raise ValueError(f"Invalid input: {str(e)}")

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
    AWS Lambda handler function to process incoming events.

    Args:
        event (dict): Incoming event data.
        context (LambdaContext): Lambda execution context.

    Returns:
        dict: Response from the Lambda function.
    """
    return app.resolve(event, context)

if __name__ == "__main__":
    print(
        app.get_openapi_json_schema(
            title="Geolocation Agent",
            version="1.0.0",
            description="Geolocation services using Amazon Location Services (ESRI)",
            tags=["coordinates", "reverse geocode", "calculate route"]
        )
    )