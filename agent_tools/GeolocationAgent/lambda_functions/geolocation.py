# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger
logger = Logger()

class PlaceIndexService:
    """
    A class to manage AWS Location Service Place Index operations.

    Attributes:
        client (boto3.client): AWS Location Service client.
        index_name (str): Name of the Place Index.
        data_source (str): Data source for the Place Index.
        description (str): Description of the Place Index.
        intended_use (str): Intended use of the Place Index.
    """

    def __init__(self, index_name='SamplePlaceIndex', data_source='Esri', description='Sample Place Index', intended_use='SingleUse'):
        self.client = boto3.client('location')
        self.index_name = index_name
        self.data_source = data_source
        self.description = description
        self.intended_use = intended_use
        self.create_place_index()

    def list_place_indexes(self):
        try:
            response = self.client.list_place_indexes()
            return [index['IndexName'] for index in response['Entries']]
        except ClientError as e:
            logger.error(f"Error listing place indexes: {e}")
            return []

    def create_place_index(self):
        """
        Creates a new Place Index or logs a warning if it already exists.
        """
        existing_indexes = self.list_place_indexes()
        if self.index_name in existing_indexes:
            #logger.warning(f"Place index '{self.index_name}' already exists.")
            return

        try:
            response = self.client.create_place_index(
                IndexName=self.index_name,
                DataSource=self.data_source,
                Description=self.description,
                DataSourceConfiguration={
                    'IntendedUse': self.intended_use
                }
            )
            logger.info("Place index created successfully.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                #logger.info(f"Place index '{self.index_name}' already exists.")
                pass                
            else:
                logger.error(f"Unexpected error: {e}")

    def search_place_index_for_text(self, location_description):
        """
        Searches the Place Index for a given location description and returns the first result.

        Args:
            location_description (str): The location description to search for.

        Returns:
            dict: The first search result, or None if no results are found.
        """
        try:
            response = self.client.search_place_index_for_text(
                IndexName=self.index_name,
                Text=location_description,
                MaxResults=1
            )
            if response['Results']:
                place = response['Results'][0]['Place']
                logger.info(f"Found place: {place['Label']}")
                return place
            else:
                logger.warning(f"No place found for '{location_description}'")
                return None
        except ClientError as e:
            logger.error(f"Error searching place index for text: {e}")
            return None

    def get_point_coordinates(self, location_description):
        """
        Retrieves the point coordinates for a given location description.

        Args:
            location_description (str): The location description to search for.

        Returns:
            dict: A dictionary containing the latitude and longitude coordinates, or None if an error occurs.
        """
        try:
            response = self.client.search_place_index_for_text(
                IndexName=self.index_name,
                Text=location_description,
                MaxResults=1
            )
            point_coordinates = response['Results'][0]['Place']['Geometry']['Point']
            result = {
                "Latitude": point_coordinates[1],
                "Longitude": point_coordinates[0]
            }
            logger.info(f"Point coordinates: {result}")
            return result
        except ClientError as e:
            logger.error(f"Error searching place index: {e}")
            return None
        except (IndexError, KeyError):
            logger.error(f"Error retrieving point coordinates for {location_description}")
            return None

    def reverse_geocode(self, coordinates):
        """
        Performs reverse geocoding to retrieve the address for a given set of coordinates.

        Args:
            coordinates (list): A list containing the latitude and longitude coordinates.

        Returns:
            dict: A dictionary containing the address, or None if an error occurs or no address is found.
        """
        try:
            response = self.client.search_place_index_for_position(
                IndexName=self.index_name,
                Position=coordinates,
                MaxResults=1
            )
            if response['Results']:
                place = response['Results'][0]['Place']
                address = {"address": f"{place['Label']}"}
                logger.info(f"Reverse geocoded address: {address}")
                return address
            else:
                logger.warning("No address found for the given coordinates.")
                return None
        except ClientError as e:
            logger.error(f"Error reverse geocoding coordinates: {e}")
            return None


class RouteService:
    """
    A class to manage AWS Location Service Route Calculator operations.

    Attributes:
        client (boto3.client): AWS Location Service client.
        calculator_name (str): Name of the Route Calculator.
        data_source (str): Data source for the Route Calculator.
        pricing_plan (str): Pricing plan for the Route Calculator.
        description (str): Description of the Route Calculator.
    """

    def __init__(self, calculator_name='SampleRouteCalculator', data_source='Esri', pricing_plan='RequestBasedUsage', description=None):
        self.client = boto3.client('location')
        self.calculator_name = calculator_name
        self.data_source = data_source
        self.pricing_plan = pricing_plan
        self.description = description
        self.create_route_calculator()

    def list_route_calculators(self):
        try:
            response = self.client.list_route_calculators()
            return [calculator['CalculatorName'] for calculator in response['Entries']]
        except ClientError as e:
            logger.error(f"Error listing route calculators: {e}")
            return []

    def create_route_calculator(self):
        """
        Creates a new Route Calculator or logs a warning if it already exists.
        """
        existing_calculators = self.list_route_calculators()
        if self.calculator_name in existing_calculators:
            #logger.info(f"Route calculator '{self.calculator_name}' already exists.")
            return

        try:
            response = self.client.create_route_calculator(
                CalculatorName=self.calculator_name,
                DataSource=self.data_source,
                PricingPlan=self.pricing_plan,
                Description=self.description
            )
            logger.info(f"Route calculator '{self.calculator_name}' created successfully.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                #logger.warning(f"Route calculator '{self.calculator_name}' already exists.")
                pass                
            else:
                logger.error(f"Error creating route calculator: {e}")

    def calculate_route(self, calculator_name, departure_position, destination_position, travel_mode='Car', distance_unit='Miles'):
        """
        Calculates the route between two positions.

        Args:
            calculator_name (str): Name of the Route Calculator to use.
            departure_position (list): A list containing the latitude and longitude of the departure position.
            destination_position (list): A list containing the latitude and longitude of the destination position.
            travel_mode (str): The travel mode (e.g., 'Car', 'Truck', 'Walking').
            distance_unit (str): The unit for distance (e.g., 'Miles', 'Kilometers').

        Returns:
            dict: A dictionary containing the route legs, or None if an error occurs.
        """
        try:
            response = self.client.calculate_route(
                CalculatorName=calculator_name,
                DeparturePosition=departure_position,
                DestinationPosition=destination_position,
                TravelMode=travel_mode,
                DistanceUnit=distance_unit
            )
            logger.info(f"Route calculated successfully.")
            logger.info(f"Route legs: {response['Legs']}")
            route_summary = self.summarize_route(response, False)
            return route_summary
        except ClientError as e:
            logger.error(f"Error calculating route: {e}")
            return None

    def format_duration(self, seconds):
        """
        Formats a duration in seconds into a human-readable string.

        Args:
            seconds (int): The duration in seconds.

        Returns:
            str: A string representing the duration in hours, minutes, and seconds.
        """
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

    def summarize_route(self, route_response, print_leg_details=False):
        """
        Returns a summary of the route as a semi-structured JSON object.
        Optionally includes leg and step details.

        Args:
            route_response (dict): The response from the calculate_route API call.
            print_leg_details (bool): Whether to include leg and step details.

        Returns:
            dict: A semi-structured JSON object containing the route summary and optionally leg and step details.
        """
        summary = route_response['Summary']
        legs = route_response['Legs']
        place_index_service = PlaceIndexService()

        # Create the route summary dictionary
        route_summary = {
            'DataSource': summary['DataSource'],
            'TotalDistance': {
                'Value': summary['Distance'],
                'Unit': summary['DistanceUnit']
            },
            'TotalDuration': self.format_duration(summary['DurationSeconds'])
        }

        # Create a list to store leg details
        leg_details = []

        # Add leg details if requested
        if print_leg_details:
            for i, leg in enumerate(legs, start=1):
                leg_start_position = place_index_service.reverse_geocode(leg['StartPosition'])
                leg_end_position = place_index_service.reverse_geocode(leg['EndPosition'])

                leg_detail = {
                    'LegNumber': i,
                    'Start': leg_start_position,
                    'End': leg_end_position,
                    'Distance': {
                        'Value': leg['Distance'],
                        'Unit': 'mi'
                    },
                    'Duration': self.format_duration(leg['DurationSeconds'])
                }

                # Create a list to store step details
                step_details = []

                # Add step details
                for j, step in enumerate(leg['Steps'], start=1):
                    step_start_position = place_index_service.reverse_geocode(step['StartPosition'])
                    step_end_position = place_index_service.reverse_geocode(step['EndPosition'])

                    step_detail = {
                        'StepNumber': j,
                        'Start': step_start_position,
                        'End': step_end_position,
                        'Distance': {
                            'Value': step['Distance'],
                            'Unit': 'mi'
                        },
                        'Duration': self.format_duration(step['DurationSeconds'])
                    }
                    step_details.append(step_detail)

                leg_detail['Steps'] = step_details
                leg_details.append(leg_detail)

        # Add leg details to the route summary
        route_summary['Legs'] = leg_details

        return route_summary