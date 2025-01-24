###############################################################################
#
# Title         : Generate OpenAPI schema for agent tools
# Description   : This script generates OpenAPI schema for each agent tool
#                 subdirectory that ends with "Agent". It iterates over the
#                 subdirectories of the parent directory, changes to the
#                 "lambda_functions" subdirectory of each "Agent" directory,
#                 runs the "lambda_handler.py" script to generate the schema,
#                 and then moves back to the parent directory.
# Version       : 1.0
# Usage         : ./generate_schema.sh
# Notes         : Make sure to run this script from the /scripts directory
#
###############################################################################

# List of directories to exclude
directory_exclusion=("AWSArtifactAgent")

# Change to the agent_tools directory
cd ../agent_tools

# Get the current directory
current_dir=$(pwd)
echo "Current directory: $current_dir"

# Iterate over subdirectories
for dir in */; do

    # Remove the trailing slash from the directory name
    dir_name="${dir%/}"

    # Check if the directory name ends with "Agent" and is not in the exclusion list
    if [[ $dir_name == *"Agent" && ! " ${directory_exclusion[@]} " =~ " ${dir_name} " ]]; then
        echo "Generating schema for $dir_name"

        # Change to the subdirectory
        cd "$current_dir/$dir_name/lambda_functions"

        # Run the command
        python3 lambda_handler.py > ../schema/openapi_schema.json

        # Change back to the current directory
        cd "$current_dir"
    fi
done