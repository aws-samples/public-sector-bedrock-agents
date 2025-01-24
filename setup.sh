#!/bin/bash

#############################################################
# Deploys a sample collection of Amazon Bedrock Agents
#############################################################

# 1. Check if Docker service is running
if docker info > /dev/null 2>&1; then
    echo "Docker service is running."
else
    echo "Docker service is not running. Please start the Docker service and try again."
    return 1
fi

# 2. Create a virtual environment
python3 -m venv .venv
echo "Virtual environment created."

# 3. Activate the virtual environment using the full path
CURRENT_DIR=$(pwd)
source ${CURRENT_DIR}/.venv/bin/activate
echo "Virtual environment activated."

# 4. Navigate to the CDK project deployment folder
cd ./deployment/cdk/
echo "Change to CDK directory: $(pwd)"

# 5. Install the required Python packages
pip install -r requirements.txt

# 6. Bootstrap your environment, account, and region to run the CDK project
cdk bootstrap

# 7. Synthesize the project to validate the implementation and produce the CloudFormation template to be deployed
cdk synth

# 8. Check if a stack name is provided as a parameter
if [ -z "$1" ]
then
    # No stack name provided, deploy all stacks
    cdk deploy --all --require-approval never
else
    # Stack name provided, deploy the specified stack
    cdk deploy "$1" --require-approval never
fi

# 9. Change directory back to the top-level directory
cd $CURRENT_DIR
echo "Changed directory back to: $CURRENT_DIR"

#10. Deactivate the virtual environment
# deactivate