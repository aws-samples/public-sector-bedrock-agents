# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This module defines the DateTimeAgentStack class for deploying an AWS CDK stack
that sets up a date, time, and calendar utility agent using AWS Bedrock and Lambda PowerTools.
"""

import os
from aws_cdk import (
    Aws,
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    Duration,
    CfnOutput
)
from aws_cdk.aws_lambda import Runtime, LayerVersion, Tracing
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from cdklabs.generative_ai_cdk_constructs import (
    bedrock
)
from cdklabs.generative_ai_cdk_constructs.bedrock import (
    ActionGroupExecutor,
    Agent,
    AgentActionGroup,
    ApiSchema,
    BedrockFoundationModel,
    ChunkingStrategy,
    KnowledgeBase,
    Guardrail
)
from constructs import Construct

class DateTimeAgentStack(Stack):
    """
    A stack for deploying the DateTime Agent using AWS CDK.
    
    :param scope: The scope in which to define this stack.
    :param construct_id: The ID of the construct.
    :param kwargs: Additional keyword arguments passed to the Stack constructor.
    """
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Create Bedrock KnowledgeBase to retrieve sample policy documents
        policy_knowledge_base = KnowledgeBase(
            self,
            'PolicyDocumentsKB',
            name="PublicSectorPolicyDocuments",
            description="This knowledge base contains Any Company's policy documents",
            embeddings_model=BedrockFoundationModel.COHERE_EMBED_MULTILINGUAL_V3,
            instruction="This knowledge base contains sample policy documents for the purpose of answering questions about the documents.",
        )
        
        # Create S3 bucket to load sample policy documents
        # amazonq-ignore-next-line
        policy_documents_bucket = s3.Bucket(self, 'PolicyDocumentsBucket', enforce_ssl=True)

        # Upload text files from the policy_documents directory to the S3 bucket
        s3_deployment.BucketDeployment(
            self,
            "DeployTextFiles",
            sources=[s3_deployment.Source.asset(os.path.join(current_dir, "..", "..", "assets", "DateTimeAgent", "policy_documents"))],
            destination_bucket=policy_documents_bucket,
        )

        # Add the S3 data source
        kb_data_source = policy_knowledge_base.add_s3_data_source(
            data_source_name="PolicyDocumentsDataSource",
            bucket=policy_documents_bucket,
            chunking_strategy=ChunkingStrategy.SEMANTIC,
            parsing_strategy=bedrock.ParsingStategy.foundation_model(
                parsing_model=BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_SONNET_V1_0.as_i_model(self)
            )
        )

        # Read the instruction file
        with open(os.path.join(current_dir, "..", "..", "..", "agent_tools", "DateTimeAgent", "instructions", "instructions.txt"), 'r', encoding="utf-8") as file:
            instruction = file.read()

        # Create a Bedrock Agent
        agent = Agent(
            self,
            "DateTimeAgent",
            name="DateTimeAgent",
            description="Provides various date, time, and calendar-related utility functions.",
            foundation_model=BedrockFoundationModel.AMAZON_NOVA_LITE_V1,
            instruction=instruction,
            should_prepare_agent=True,
        )
        
        # Add the KnowledgeBase to the Agent
        agent.add_knowledge_base(policy_knowledge_base)

        # Create a Python Lambda function
        lambda_function = PythonFunction(
            self,
            "DateTimeAgentFunction",
            runtime=Runtime.PYTHON_3_12,
            entry=os.path.join(current_dir, "..", "..", "..", "agent_tools", "DateTimeAgent", "lambda_functions"),
            index="lambda_handler.py",
            handler="lambda_handler",
            timeout=Duration.seconds(30),  # Set the default timeout to 30 seconds
            tracing=Tracing.ACTIVE  # Activate X-Ray tracing
        )

        # Add the AWS Lambda PowerTools layer to the Lambda function
        lambda_function.add_layers(
            LayerVersion.from_layer_version_arn(
                self, "LambdaPowertoolsPythonLayer", f"arn:aws:lambda:{Aws.REGION}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:4"
            )
        )     

        # Create an action group executor using the Lambda function
        executor_group = ActionGroupExecutor(lambda_=lambda_function)

        # Create an action group for the Bedrock Agent
        action_group = AgentActionGroup(
            self,
            "DateTimeAG",
            action_group_name="DateTimeAG",
            description="Provides various date, time, and calendar-related utility functions.",
            action_group_executor=executor_group,
            action_group_state="ENABLED",
            api_schema=ApiSchema.from_asset(os.path.join(current_dir, "..", "..", "..", "agent_tools", "DateTimeAgent", "schema", "openapi_schema.json")),
        )
        agent.add_action_group(action_group)

        # Add an Amazon Bedrock Guardrail
        guardrail = Guardrail(self, 
                              "DateTimeGR",
                              name='DateTimeGR',
                              description="DateTime Agent Guardrails.")

        # Add Amazon Bedrock Guardrail policies
        guardrail.add_contextual_grounding_filter(
            type=bedrock.ContextualGroundingFilterType.GROUNDING,
            threshold=0.95)       

        # Add the Amazon Bedrock Guardrail to the Agent
        agent.add_guardrail(guardrail)              

        # Output the KNOWLEDGE_BASE_ID and DATA_SOURCE_ID
        CfnOutput(self, "AgentID", value=agent.agent_id)
        CfnOutput(self, "AgentVersion", value=agent.agentversion)
        CfnOutput(self, "KnowledgeBaseID", value=policy_knowledge_base.knowledge_base_id)
        CfnOutput(self, "DataSourceID", value=kb_data_source.data_source_id)            