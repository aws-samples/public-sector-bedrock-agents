#!/bin/bash

# Example Usage: ./start_ingestion_jobs.sh DateTimeAgent

# Function to get Agent ID by Agent Name
get_agent_id() {
    local agent_name="$1"
    local agent_id=$(aws bedrock-agent list-agents --query "agentSummaries[?agentName=='$agent_name'].agentId" --output text)
    echo "$agent_id"
}

# Function to get Agent Version by Agent ID
get_agent_version() {
    local agent_id="$1"
    local agent_version=$(aws bedrock-agent list-agent-versions --agent-id "$agent_id" --query "agentVersionSummaries[0].agentVersion" --output text)
    echo "$agent_version"
}

# Function to get Knowledge Base ID by Agent ID and Agent Version
get_knowledge_base_id() {
    local agent_id="$1"
    local agent_version="$2"
    local knowledge_base_id=$(aws bedrock-agent list-agent-knowledge-bases --agent-id "$agent_id" --agent-version "$agent_version" --query "agentKnowledgeBaseSummaries[0].knowledgeBaseId" --output text)
    echo "$knowledge_base_id"
}

# Function to start ingestion jobs for all data sources in a knowledge base
start_ingestion_jobs() {
    local knowledge_base_id="$1"
    local data_sources=$(aws bedrock-agent list-data-sources --knowledge-base-id "$knowledge_base_id" --query "dataSourceSummaries[].dataSourceId" --output text)

    for data_source_id in $data_sources; do
        echo "Starting ingestion job for data source $data_source_id in knowledge base $knowledge_base_id"
        aws bedrock-agent start-ingestion-job --knowledge-base-id "$knowledge_base_id" --data-source-id "$data_source_id"
    done

    echo "Ingestion jobs started for all data sources in knowledge base $knowledge_base_id"
}

# Driver function to execute the script logic
main() {
    local agent_name="$1"

    if [ -z "$agent_name" ]; then
        echo "Usage: $0 <agent_name>"
        exit 1
    fi

    local agent_id=$(get_agent_id "$agent_name")
    if [ -z "$agent_id" ]; then
        echo "Agent with name $agent_name not found."
        exit 1
    else
        echo "Agent ID for $agent_name is $agent_id"

        local agent_version=$(get_agent_version "$agent_id")
        if [ -z "$agent_version" ]; then
            echo "No versions found for agent $agent_name."
            exit 1
        else
            echo "Agent Version for $agent_name is $agent_version"

            local knowledge_base_id=$(get_knowledge_base_id "$agent_id" "$agent_version")
            if [ -z "$knowledge_base_id" ]; then
                echo "No knowledge bases found for agent $agent_name."
                exit 1
            else
                echo "Knowledge Base ID for $agent_name is $knowledge_base_id"
                start_ingestion_jobs "$knowledge_base_id"
            fi
        fi
    fi
}

# Call the main function with the provided agent name
main "$1"