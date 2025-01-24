# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This module defines the GeolocationAgentStack class for deploying an AWS CDK stack.
It sets up an AWS Lambda function, integrates it with AWS IAM for geolocation service access,
adds the Lambda PowerTools layer, and configures an Anthropic Bedrock Agent with an action group
to interact with geolocation services.
"""

import os
from aws_cdk import Aws, Stack, Duration
from aws_cdk.aws_lambda import Runtime, LayerVersion, Tracing
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from aws_cdk.aws_iam import PolicyStatement, Effect
from cdklabs.generative_ai_cdk_constructs import bedrock
from cdklabs.generative_ai_cdk_constructs.bedrock import (
    ActionGroupExecutor,
    Agent,
    AgentActionGroup,
    ApiSchema,
    BedrockFoundationModel,
    Guardrail  
)
from constructs import Construct

class GeolocationAgentStack(Stack):
    """
    Stack to deploy the Geolocation Agent Lambda function and associated resources.
    
    :param scope: The scope in which to define this stack.
    :param construct_id: The ID of the stack.
    :param kwargs: Additional keyword arguments to pass to the Stack parent class.
    """
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the current directory path
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Create a Python Lambda function
        lambda_function = PythonFunction(
            self,
            "GeolocationAgentFunction",
            runtime=Runtime.PYTHON_3_12,
            entry=os.path.join(current_dir, "..", "..", "..", "agent_tools", "GeolocationAgent", "lambda_functions"),
            index="lambda_handler.py",
            handler="lambda_handler",
            timeout=Duration.seconds(30),  # Set the default timeout to 30 seconds
            tracing=Tracing.ACTIVE  # Activate X-Ray tracing
        )

        # Define an IAM policy statement to allow the Lambda function to access geolocation services
        geo_policy_statement = PolicyStatement(
            effect=Effect.ALLOW,
            sid="GeolocationAgentFunctionPolicy",
            actions=[
                "geo:CreateRouteCalculator",
                "geo:CalculateRoute",
                "geo:ListRouteCalculators",
                "geo:CreatePlaceIndex",
                "geo:ListPlaceIndexes",
                "geo:SearchPlaceIndexForPosition",
                "geo:SearchPlaceIndexForText"],
            resources=["*"]
        )

        # Add the policy statement to the Lambda function's execution role
        lambda_function.add_to_role_policy(geo_policy_statement)

        # Add the AWS Lambda PowerTools layer to the Lambda function
        lambda_function.add_layers(
            LayerVersion.from_layer_version_arn(
                self, "LambdaPowertoolsPythonLayer", f"arn:aws:lambda:{Aws.REGION}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:4"
            )
        )

        # Read the instruction file
        with open(os.path.join(current_dir, "..", "..", "..", "agent_tools", "GeolocationAgent", "instructions", "instructions.txt"), 'r', encoding="utf-8") as file:
            instruction = file.read()

        # Create a Bedrock Agent 
        agent = Agent(
            self,
            "GeolocationAgent",
            name="GeolocationAgent",
            description="Provides a set of functions to interact with geolocation services.",
            foundation_model=BedrockFoundationModel.AMAZON_NOVA_LITE_V1,
            instruction=instruction,
            should_prepare_agent=True
        )

        # Create an action group executor using the Lambda function
        executor_group = ActionGroupExecutor(lambda_=lambda_function)

        # Create an action group for the Bedrock Agent
        action_group = AgentActionGroup(
            self,
            "GeolocationAG",
            action_group_name="GeolocationAG",
            description="Provides a set of functions to interact with geolocation services.",
            action_group_executor=executor_group,
            action_group_state="ENABLED",
            api_schema=ApiSchema.from_asset(os.path.join(current_dir, "..", "..", "..", "agent_tools", "GeolocationAgent", "schema", "openapi_schema.json")),
        )
        agent.add_action_group(action_group)

        # Add an Amazon Bedrock Guardrail
        guardrail = Guardrail(self, 
                              "GeolocationGR",
                              name='GeolocationGR',
                              description="Geolocation Agent Guardrails.")

        # Add Amazon Bedrock Guardrail policies
        guardrail.add_contextual_grounding_filter(
            type=bedrock.ContextualGroundingFilterType.GROUNDING,
            threshold=0.95)    

        # Add the Amazon Bedrock Guardrail to the Agent
        agent.add_guardrail(guardrail)              