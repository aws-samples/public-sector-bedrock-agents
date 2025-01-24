# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This module provides a set of functions to interact with AWS Artifact reports. It allows you to
list reports, get the total number of report pages, retrieve a specific report, and search for
reports based on keywords. The module uses the ArtifactUtils class from the
aws_artifact_agent_tool package.

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

from artifact_utils import ArtifactUtils

tracer = Tracer(service="AWSArtifactAgent")
logger = Logger()
app = BedrockAgentResolver()
artifact_utils = ArtifactUtils()

@app.get("/rp", description="Lists AWS Artifact reports using pagination")
@tracer.capture_method
def list_reports(
    page_size: str = Query("5", description="Maximum number of reports to return per page. Default and maximum value is 5."),
    page_number: Optional[str] = Query("1", description="Page number to return. Default is 1.")
) -> dict:
    """
    Lists AWS Artifact reports using pagination.

    Args:
        page_size (str): Maximum number of reports to return per page. Default and maximum value is 5.
        page_number (Optional[str]): Page number to return. Default is 1.

    Returns:
        dict: A dictionary containing the status code and the list of reports.
    """
    page_size_int = int(page_size)
    page_number_int = int(page_number)
    reports = artifact_utils.list_reports(page_size_int, page_number_int)
    return {"statusCode": 200, "body": reports}

@app.get("/rp/pg", description="Returns the total number of report pages")
@tracer.capture_method
def get_pages(
    page_size: Optional[str] = Query("5", description="Maximum number of reports per page. Default and maximum value is 5.")
) -> dict:
    """
    Returns the total number of report pages.

    Args:
        page_size (Optional[str]): Maximum number of reports per page. Default and maximum value is 5.

    Returns:
        dict: A dictionary containing the status code and the total number of report pages.
    """
    page_size_int = int(page_size)
    total_pages = artifact_utils.get_total_report_pages(page_size_int)
    return {"statusCode": 200, "body": str(total_pages)}

@app.get("/rp/url", description="Returns a URL to download the report document, not the document itself. The returned URL will contain X-AMZ-* querystrings for authenticated access.")
@tracer.capture_method
def get_url(
    report_id: str = Query(..., description="The ID of the report."),
    report_version: str = Query(..., description="The version of the report.")
) -> dict:
    """
    Returns a URL to download the report document, not the document itself. The returned URL will contain X-AMZ-* querystrings for authenticated access.

    Args:
        report_id (str): The ID of the report.
        report_version (str): The version of the report.

    Returns:
        dict: A dictionary containing the status code and the presigned URL of the report.
    """
    version = int(report_version)
    report_url = artifact_utils.get_report_url(report_id, version)
    return {"statusCode": 200, "body": report_url}

@app.get("/rp/srch", description="Search for reports based on keywords")
@tracer.capture_method
def search(
    search_keywords: str = Query(..., description="Keywords to search for in report names and descriptions."),
    max_results: Optional[str] = Query("5", description="Maximum number of results to return. Default and maximum value is 5.")
) -> dict:
    """
    Search for reports based on keywords.

    Args:
        search_keywords (str): Keywords to search for in report names and descriptions.
        max_results (Optional[str]): Maximum number of results to return. Default and maximum value is 5.

    Returns:
        dict: A dictionary containing the status code and the search results.
    """
    max_results_int = int(max_results)
    search_results = artifact_utils.search_reports(unescape(search_keywords), max_results_int)
    return {"statusCode": 200, "body": search_results}

@app.get("/cd", description="Get the current date and time. Example: /current-date")
@tracer.capture_method
def get_current_date() -> dict:
    """
    Get the current date and time.

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
            title="AWS Artifact Agent",
            version="1.0.0",
            description="This API provides functionality to query AWS Artifact content and download documents",
            tags=["AWS Artifact", "security reports", "compliance reports", "certifications", "accreditations"]
        )
    )