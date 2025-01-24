# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import Stack
from constructs import Construct

from agent_stacks.AWSArtifactAgentStack import AWSArtifactAgentStack
from agent_stacks.DateTimeAgentStack import DateTimeAgentStack
from agent_stacks.GeolocationAgentStack import GeolocationAgentStack
from agent_stacks.WeatherForecastAgentStack import WeatherForecastAgentStack
from agent_stacks.ExampleAgentStack import ExampleAgentStack

class MainStack(Stack):
    """
    This class defines the main stack for the public sector LLM agent tools.
    It creates instances of various agent stacks.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Initializes the MainStack.

        Args:
            scope (Construct): The scope in which this construct is defined.
            construct_id (str): The unique identifier for this construct.
            **kwargs: Additional keyword arguments to pass to the Stack constructor.
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create instances of agent stacks
        aws_artifact_agent_stack = AWSArtifactAgentStack(self, "AWSArtifactAgentStack")
        datetime_agent_stack = DateTimeAgentStack(self, "DateTimeAgentStack")
        geolocation_agent_stack = GeolocationAgentStack(self, "GeolocationAgentStack")
        weather_forecast_agent_stack = WeatherForecastAgentStack(self, "WeatherForecastAgentStack")
        example_agent_stack = ExampleAgentStack(self, "ExampleAgentStack")