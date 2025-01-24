# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This module provides various date, time, and calendar-related utility functions,
including retrieving the current date and time, calculating age, date differences,
business days, fiscal years, SSL/TLS certificate expiration, and policy expiration checks.

The module also includes an AWS Lambda handler function that leverages the
Bedrock Agent Resolver from AWS Lambda PowerTools to automatically resolve and inject
dependencies into the Lambda function handler.
"""

from datetime import datetime

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

from date_time_utils import DateTimeUtils, BusinessDateTimeUtils, SSLCertificateUtils
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from urllib.parse import quote as escape
from typing import Callable

tracer = Tracer(service="DateTimeAgent")
logger = Logger()
app = BedrockAgentResolver()
datetime_utils = DateTimeUtils()  # Create an instance of DateTimeUtils
business_datetime_utils = BusinessDateTimeUtils()  # Create an instance of BusinessDateTimeUtils
ssl_certificate_utils = SSLCertificateUtils()  # Create an instance of SSLCertificateUtils

@app.get("/dt", description="Returns the current date, time, day of the week, and timezone")
@tracer.capture_method
def get_current_date_time() -> dict:
    """
    Returns a dictionary containing the current date, time, day of the week, and timezone.

    Returns:
        dict: A dictionary with the following keys:
            - 'date' (str): The current date in 'mm/dd/YYYY' format.
            - 'time' (str): The current time in 'HH:MM:SS' 24-hour format.
            - 'day' (Optional[str]): The current day of the week, or None if an error occurs.
            - 'timezone' (str): The current timezone.
    """
    date_time_info = datetime_utils.get_date_time()
    return {"statusCode": 200, "body": str(date_time_info)}

@app.get("/age", description="Calculates the age based on the given birth date")
@tracer.capture_method
def calculate_age(
    birth_date: str = Query(..., description="Birth date in 'YYYY-MM-DD' format")
) -> dict:
    """
    Calculates the age based on the given birth date.

    Args:
        birth_date (str): The birth date in 'YYYY-MM-DD' format.

    Returns:
        dict: A dictionary containing the status code and the calculated age.
    """
    birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
    age = datetime_utils.calculate_age(birth_date_obj)
    return {"statusCode": 200, "body": str(age)}

@app.get("/ddiff", description="Calculates the difference between two dates in days")
@tracer.capture_method
def calculate_date_diff(
    start_date: str = Query(..., description="Start date in 'YYYY-MM-DD' format"),
    end_date: str = Query(..., description="End date in 'YYYY-MM-DD' format")
) -> dict:
    """
    Calculates the difference between two dates in days.

    Args:
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
        dict: A dictionary containing the status code and the date difference in days.
    """
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    date_diff = datetime_utils.date_diff(start_date_obj, end_date_obj)
    return {"statusCode": 200, "body": str(date_diff)}

@app.get("/bdays", description="Calculates the number of business days between two dates")
@tracer.capture_method
def calculate_business_days(
    start_date: str = Query(..., description="Start date in 'YYYY-MM-DD' format"),
    end_date: str = Query(..., description="End date in 'YYYY-MM-DD' format")
) -> dict:
    """
    Calculates the number of business days between two dates.

    Args:
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
        dict: A dictionary containing the status code and the number of business days.
    """
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    business_days = business_datetime_utils.calculate_business_days(start_date_obj, end_date_obj)
    return {"statusCode": 200, "body": str(business_days)}

@app.get("/fy", description="Calculates the fiscal year for a given date")
@tracer.capture_method
def get_fiscal_year(
    date_str: str = Query(..., description="Date in 'YYYY-MM-DD' format"),
    fiscal_year_start_month: int = Query(10, description="Month in which the fiscal year starts (default is 10 for October)")
) -> dict:
    """
    Calculates the fiscal year for a given date based on a specified fiscal year start month.

    Args:
        date_str (str): The date in 'YYYY-MM-DD' format.
        fiscal_year_start_month (int, optional): The month in which the fiscal year starts (default is 10 for October).

    Returns:
        dict: A dictionary containing the status code and the fiscal year.
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    fiscal_year = business_datetime_utils.get_fiscal_year(date_obj, fiscal_year_start_month)
    return {"statusCode": 200, "body": str(fiscal_year)}

@app.get("/fyr", description="Calculates the start and end dates of the fiscal year for a given date")
@tracer.capture_method
def get_fiscal_year_range(
    date_str: str = Query(..., description="Date in 'YYYY-MM-DD' format"),
    fiscal_year_start_month: int = Query(10, description="Month in which the fiscal year starts (default is 10 for October)")
) -> dict:
    """
    Calculates the start and end dates of the fiscal year for a given date based on a specified fiscal year start month.

    Args:
        date_str (str): The date in 'YYYY-MM-DD' format.
        fiscal_year_start_month (int, optional): The month in which the fiscal year starts (default is 10 for October).

    Returns:
        dict: A dictionary containing the status code and the start and end dates of the fiscal year.
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    start_date, end_date = business_datetime_utils.get_fiscal_year_range(date_obj, fiscal_year_start_month)
    fiscal_year_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    return {"statusCode": 200, "body": fiscal_year_range}

@app.get("/nbday", description="Calculates the next business day after the given date")
@tracer.capture_method
def get_next_business_day(
    date_str: str = Query(..., description="Date in 'YYYY-MM-DD' format")
) -> dict:
    """
    Calculates the next business day after the given date.

    Args:
        date_str (str): The date in 'YYYY-MM-DD' format.

    Returns:
        dict: A dictionary containing the status code and the next business day.
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    next_business_day = business_datetime_utils.get_next_business_day(date_obj)
    return {"statusCode": 200, "body": next_business_day.strftime("%Y-%m-%d")}

@app.get("/pdl", description="Checks if a policy has expired based on the given expiration date")
@tracer.capture_method
def check_policy_deadline(
    policy_name: str = Query(..., description="Name of the policy"),
    expiry_date: str = Query(..., description="Expiration date in 'YYYY-MM-DD HH:MM:SS' format")
) -> dict:
    """
    Checks if a policy within Bedrock KB has expired based on the given expiration date. This class is just a wrapper to
        datetime_utils.get_date_time() to help keep the inference/response consistent across
        different LLMs.

    Args:
        policy_name (str): The name of the policy.
        expiry_date (str): The expiration date in 'YYYY-MM-DD HH:MM:SS' format.

    Returns:
        dict: A dictionary containing the status code and a message indicating if the policy has expired or not.
    """
    current_datetime = datetime_utils.get_date_time()
    expiry_datetime = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
    if current_datetime >= expiry_datetime:
        return {"statusCode": 200, "body": f"The {policy_name} policy has expired on {expiry_date}"}
    else:
        return {"statusCode": 200, "body": f"The {policy_name} policy is still valid and will expire on {expiry_date}"}

@app.get("/ssl", description="Checks if an SSL/TLS certificate has expired for a given hostname")
@tracer.capture_method
def check_ssl_cert_deadline(
    hostname: str = Query(..., description="Hostname for which to check the SSL/TLS certificate"),
    port: int = Query(443, description="Port number for the SSL/TLS connection (default is 443 for HTTPS)")
) -> dict:
    """
    Checks if an SSL/TLS certificate has expired for a given hostname.

    Args:
        hostname (str): The hostname for which to check the SSL/TLS certificate.
        port (int, optional): The port number for the SSL/TLS connection (default is 443 for HTTPS).

    Returns:
        dict: A dictionary containing the status code and a message indicating if the SSL/TLS certificate has expired or not.
    """
    expiry_date = ssl_certificate_utils.get_ssl_cert_expiry(hostname, port)
    current_datetime = datetime.now()
    expiry_datetime = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
    if current_datetime >= expiry_datetime:
        return {"statusCode": 200, "body": f"The SSL/TLS certificate for {hostname} has expired on {expiry_date}"}
    else:
        return {"statusCode": 200, "body": f"The SSL/TLS certificate for {hostname} is still valid and will expire on {expiry_date}"}

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
            title="Date and Time Utilities API",
            version="1.0.0",
            description="This API provides various date and time utility functions, including current date, time, day, timezone, age calculation, date difference, business day calculation, fiscal year calculation, holiday checks, and SSL/TLS certificate expiration checks.",
            tags=["date", "time", "utilities"]
        )
    )