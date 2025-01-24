# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This module provides a set of functions to interact with AWS Bedrock agents. It allows you to
fetch agent details and invoke agents with specific prompts. The module uses the Boto3 library
to interact with AWS services.
"""

import boto3
from botocore.exceptions import ClientError
import pytest
import uuid
import logging
from time import sleep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

bedrock_agent = boto3.client('bedrock-agent')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

session_id = str(uuid.uuid4())

def get_agent_details(agent_name):
    """
    Fetches the details of a specified agent.

    Args:
        agent_name (str): The name of the agent to fetch details for.

    Returns:
        tuple: A tuple containing the agent ID and agent alias ID.

    Raises:
        AssertionError: If the agent or its alias is not found.
    """
    try:
        response = bedrock_agent.list_agents(maxResults=100)
        agents = response['agentSummaries']

        for agent in agents:
            if agent['agentName'] == agent_name:
                agent_id = agent['agentId']
                alias_response = bedrock_agent.list_agent_aliases(agentId=agent_id)
                aliases = alias_response['agentAliasSummaries']

                if aliases:
                    agent_alias_id = aliases[0]['agentAliasId']
                    return agent_id, agent_alias_id
                else:
                    raise AssertionError("No alias found")
    except ClientError as e:
        raise AssertionError(f"Failed to list or get agent details: {e}")

    logger.error(f"No agent found with name '{agent_name}'")
    raise AssertionError(f"No agent found with name '{agent_name}'")

def invoke_agent(agent_id, agent_alias_id, input_text):
    """
    Invokes an agent with the specified input text.

    Args:
        agent_id (str): The ID of the agent to invoke.
        agent_alias_id (str): The ID of the agent alias to use.
        input_text (str): The input text to send to the agent.

    Returns:
        str: The completion text returned by the agent.
    
    Raises:
        AssertionError: If the agent invocation fails.
    """
    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            endSession=False,
            enableTrace=False, 
            sessionId=session_id,
            inputText=input_text
        )

        completion = ""
        for event in response.get("completion"):
            chunk = event["chunk"]
            completion += chunk["bytes"].decode()

        return completion
    except ClientError as e:
        raise AssertionError(f"Failed to invoke agent: {e}")

# Note: LLM responses are non-deterministic, adjust accordingly.
@pytest.mark.parametrize("agent_name, prompt, expected_results", [
    ("AWSArtifactAgent", "Does AWS have any recent compliance documents related to FedRAMP?", ["FedRAMP Customer Package", "compliance"]),
    ("AWSArtifactAgent", "Provide the names of any compliance documents related to running Canadian cloud workloads.", ["Canadian Centre for Cyber Security", "CCCS"]),
    ("AWSArtifactAgent", "Download the HITRUST Certification Letter.", ["artifact-assets", "HITRUST", "Certification"]),
    ("DateTimeAgent", "Calculate the number of business days between 2026-05-01 and 2026-05-15", ["10", "10.0"]),
    ("DateTimeAgent", "Is Any Company's Investment Policy still valid as of today?", ["expires on 01/01/2022", "expired", "not valid", "no longer valid"]),
    ("DateTimeAgent", "Check if the TLS certificate for amazon.com has expired.", ["valid", "2025-07-27", "not expired"]),
    ("ExampleAgent", "What is the current weather at the KNYC station?", ["temperature", "wind", "barometric"]),    
    ("GeolocationAgent", "Reverse geocode the coordinates (33.979878,-117.401904) to assist in dispatching firefighting crews to a reported brush burn incident.", ["Jurupa", "Crestmore", "92509"]),
    ("GeolocationAgent", "Get the coordinates for the address 950 NW Carkeek Park Rd., Seattle, WA 98177, to assess its proximity to nearby green spaces for natural resource management.", ["47.71156", "-122.36869"]),
    ("GeolocationAgent", "The city is planning a walking parade route in Seattle, WA. The route starts at the Amazon Spheres and ends at the Space Needle, what are the estimated walking and driving times?", ["minutes", "from the Amazon Spheres to the Space Needle"]),
    ("WeatherForecastAgent", "What is the expected rainfall amount for the next 72 hours in Seattle, WA?", ["inches", "rainfall"]),
    ("WeatherForecastAgent", "Forecast the temperature and wind conditions for tomorrow morning to plan pesticide spraying in Nashville, TN.", ["temperature", "wind"]),
    ("WeatherForecastAgent", "Check if there are any severe weather advisories issued for the next 48 hours that may impact road maintenance crews in Herndon, VA.", ["no", "impact"])
])
def test_agent_response(agent_name, prompt, expected_results):
    """
    Tests the response of an agent with a given prompt against expected results.

    Args:
        agent_name (str): The name of the agent to test.
        prompt (str): The prompt to send to the agent.
        expected_results (list): The expected results to check against the agent's response.

    Raises:
        AssertionError: If none of the expected results are found in the agent's response.
    """
    logger.info(f"Testing agent: {agent_name}")

    # Fetching agent details
    agent_id, agent_alias_id = get_agent_details(agent_name)
    logger.info(f"Found agent details for agent: {agent_name} | agentId: {agent_id} | agentAliasId: {agent_alias_id}")

    logger.info(f"Invoking agent with prompt: '{prompt}'")

    # Invoke the agent
    response = invoke_agent(agent_id, agent_alias_id, prompt)
    logger.info(f"Agent response: {response}")

    # Check if any of the expected results are found in the response
    for expected_result in expected_results:
        if expected_result in response:
            assert True
            break
    else:
        assert False, (
            f"None of the expected results {expected_results} found in response for agent {agent_name} with prompt '{prompt}'"
        )

    # Add sleep to prevent exceeding request per minute (rpm) invocation quotas
    # Lowering this value may cause rate-limit issues
    # Invoke the agent
    logger.info(f"Sleeping to avoid exceeding rate limits...")
    sleep(15)