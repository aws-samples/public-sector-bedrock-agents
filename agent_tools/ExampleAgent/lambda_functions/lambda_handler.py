# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This module provides a Lambda handler function to retrieve weather forecast data
for a given weather station using the National Weather Service API.
It utilizes the AWS Lambda Powertools library for logging, tracing, and API integration.
"""

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from weather_api import get_weather_data

# Initialize Powertools for AWS logging and tracing
logger = Logger()
tracer = Tracer(service="ExampleAgent")

# BedrockAgentResolver handles Lambda and Bedrock Agent integration
app = BedrockAgentResolver()

# Define endpoint for Bedrock Agent weather forecast calls
@app.get("/forecast", description="Retrieve current weather forecast at a station.")
@tracer.capture_method
def get_weather(station_id: str = Query(..., description="The id of the weather observation station.")) -> dict:
    # Log API call
    logger.info(f"Retrieving weather data for station: {station_id}")

    # Get weather data from the weather API
    weather_data = get_weather_data(station_id)

    # Log retrieved data
    logger.info(f"Weather for station {station_id}: Temp: {weather_data['temperature']}, Desc: {weather_data['description']}")

    # Add X-Ray annotation for trace filtering
    tracer.put_annotation(key="station_id", value=f"{station_id}")

    return {"statusCode": 200, "body": weather_data['data']}

# Main Lambda handler with logging and tracing
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

if __name__ == "__main__":
    # Print OpenAPI schema for Bedrock Agent configuration
    print(app.get_openapi_json_schema())