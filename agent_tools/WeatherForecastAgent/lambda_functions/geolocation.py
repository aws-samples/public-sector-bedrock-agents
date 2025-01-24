# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger
logger = Logger()

class PlaceIndexService:
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
        existing_indexes = self.list_place_indexes()
        if self.index_name in existing_indexes:
            logger.warning(f"Place index '{self.index_name}' already exists.")
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
                logger.warning(f"Place index '{self.index_name}' already exists.")
            else:
                logger.error(f"Unexpected error: {e}")

    def get_point_coordinates(self, location_description):
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
        except (IndexError, KeyError):
            logger.error(f"Error retrieving point coordinates for {location_description}")