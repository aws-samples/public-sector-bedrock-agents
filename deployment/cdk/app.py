# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

#!/usr/bin/env python3

from aws_cdk import App

from main_stack import MainStack

app = App()

MainStack(app, "public-sector-llm-agent-tools")

app.synth()
