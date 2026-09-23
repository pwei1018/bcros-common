#!/bin/bash
# 
# Script to generate Pub/Sub topics and subscriptions for BC Notify and BC Notify Housing Service.
# This script iterates through the Common projects for dev, test, sandbox, and prod.
# It dynamically copies the service account and IAM permissions from the existing GC Notify pub/sub setup.
#
# Usage:
#   chmod +x create_pubsub_bc_notify.sh
#   ./create_pubsub_bc_notify.sh [env]
#
# Note: Ensure you are authenticated with gcloud with sufficient permissions.

set -e

if [ -z "$1" ]; then
  # Define the common GCP environments
  ENVS=(
    "dev"
    "test"
    "sandbox"
    "prod"
  )
else
  ENVS=( "$1" )
fi

echo "Starting Pub/Sub topic and subscription generation..."

for ENV in "${ENVS[@]}"; do
    PROJECT_ID="c4hnrd-${ENV}"
    
    echo "=========================================================="
    echo "Processing Project: $PROJECT_ID (Environment: $ENV)"
    echo "=========================================================="
    
    # Map the correct Cloud Run base URL based on the environment suffix
    if [[ "$ENV" == "dev" ]]; then
        BASE_URL="https://notify-delivery-dev.a.run.app"
    elif [[ "$ENV" == "test" ]]; then
        BASE_URL="https://notify-delivery-test.a.run.app"
    elif [[ "$ENV" == "sandbox" ]]; then
        BASE_URL="https://notify-delivery-sandbox.a.run.app"
    elif [[ "$ENV" == "prod" ]]; then
        BASE_URL="https://notify-delivery-prod.a.run.app"
    else
        echo "Unknown environment $ENV. Skipping."
        continue
    fi

    # Reference GC Notify Topic to copy configurations and permissions from
    TOPIC_GCNOTIFY="notify-delivery-gcnotify-${ENV}"

    # Topics to create
    TOPIC_BC_NOTIFY="notify-delivery-bc-notify-${ENV}"
    TOPIC_BC_NOTIFY_HOUSING="notify-delivery-bc-notify-housing-${ENV}"

    # 1. Fetch GC Notify subscription and its settings to replicate
    echo "--> Fetching reference GC Notify configuration..."
    
    # Check if GC Notify Topic exists
    if ! /opt/homebrew/bin/gcloud pubsub topics describe "$TOPIC_GCNOTIFY" --project="$PROJECT_ID" &>/dev/null; then
        echo "    [Error] GC Notify topic $TOPIC_GCNOTIFY does not exist in $PROJECT_ID. Cannot copy settings. Skipping project."
        continue
    fi

    # Extract the first subscription attached to the GC Notify Topic
    GCNOTIFY_SUB=$(/opt/homebrew/bin/gcloud pubsub topics list-subscriptions "$TOPIC_GCNOTIFY" --project="$PROJECT_ID" --format="value(.)" | head -n 1)
    # The returned value is often the full path, extract just the name
    GCNOTIFY_SUB_NAME=$(basename "$GCNOTIFY_SUB")

    if [[ -z "$GCNOTIFY_SUB_NAME" ]]; then
        echo "    [Error] Could not find any subscriptions for GC Notify topic. Cannot copy service account. Skipping project."
        continue
    fi
    
    echo "    Found reference subscription: $GCNOTIFY_SUB_NAME"

    # Extract Service Account and Audience from the GC Notify subscription
    SERVICE_ACCOUNT=$(/opt/homebrew/bin/gcloud pubsub subscriptions describe "$GCNOTIFY_SUB_NAME" --project="$PROJECT_ID" --format="value(pushConfig.oidcToken.serviceAccountEmail)")
    AUDIENCE=$(/opt/homebrew/bin/gcloud pubsub subscriptions describe "$GCNOTIFY_SUB_NAME" --project="$PROJECT_ID" --format="value(pushConfig.oidcToken.audience)")
    
    if [[ -z "$SERVICE_ACCOUNT" ]]; then
        echo "    [Warning] Service account not found in pushConfig of $GCNOTIFY_SUB_NAME. Defaulting to pubsub-invoker."
        SERVICE_ACCOUNT="pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com"
        AUDIENCE="https://pubsub.googleapis.com/google.pubsub.v1.Subscriber"
    else
        echo "    Using Service Account: $SERVICE_ACCOUNT"
        echo "    Using Audience: $AUDIENCE"
    fi

    # Download IAM policies of GC Notify to replicate permissions
    /opt/homebrew/bin/gcloud pubsub topics get-iam-policy "$TOPIC_GCNOTIFY" --project="$PROJECT_ID" --format=json > /tmp/topic_policy.json
    /opt/homebrew/bin/gcloud pubsub subscriptions get-iam-policy "$GCNOTIFY_SUB_NAME" --project="$PROJECT_ID" --format=json > /tmp/sub_policy.json

    # Define the endpoints according to notify-delivery blueprints
    ENDPOINT_BC_NOTIFY="${BASE_URL}/bc-notify/"
    ENDPOINT_BC_NOTIFY_HOUSING="${BASE_URL}/bc-notify-housing/"

    TOPICS=("$TOPIC_BC_NOTIFY" "$TOPIC_BC_NOTIFY_HOUSING")
    ENDPOINTS=("$ENDPOINT_BC_NOTIFY" "$ENDPOINT_BC_NOTIFY_HOUSING")

    for i in "${!TOPICS[@]}"; do
        TOPIC="${TOPICS[$i]}"
        PUSH_ENDPOINT="${ENDPOINTS[$i]}"
        SUBSCRIPTION="${TOPIC}-sub"
        
        echo "--> Creating topic: $TOPIC"
        if ! /opt/homebrew/bin/gcloud pubsub topics create "$TOPIC" --project="$PROJECT_ID" 2>/dev/null; then
            echo "    [Info] Topic $TOPIC may already exist or creation failed."
        else
            echo "    [Success] Created topic $TOPIC."
        fi

        echo "--> Applying IAM permissions to topic: $TOPIC"
        /opt/homebrew/bin/gcloud pubsub topics set-iam-policy "$TOPIC" /tmp/topic_policy.json --project="$PROJECT_ID" 2>/dev/null || echo "    [Warning] Failed to set IAM policy on topic."

        echo "--> Creating push subscription: $SUBSCRIPTION"
        if ! /opt/homebrew/bin/gcloud pubsub subscriptions create "$SUBSCRIPTION" \
            --topic="$TOPIC" \
            --project="$PROJECT_ID" \
            --push-endpoint="$PUSH_ENDPOINT" \
            --push-auth-service-account="$SERVICE_ACCOUNT" \
            --push-auth-token-audience="$AUDIENCE" \
            --min-retry-delay=10s \
            --max-retry-delay=600s \
            --message-retention-duration=7d 2>/dev/null; then
            echo "    [Info] Subscription $SUBSCRIPTION may already exist or creation failed."
        else
            echo "    [Success] Created subscription $SUBSCRIPTION."
        fi
        echo "    Endpoint: $PUSH_ENDPOINT"

        echo "--> Applying IAM permissions to subscription: $SUBSCRIPTION"
        /opt/homebrew/bin/gcloud pubsub subscriptions set-iam-policy "$SUBSCRIPTION" /tmp/sub_policy.json --project="$PROJECT_ID" 2>/dev/null || echo "    [Warning] Failed to set IAM policy on subscription."
    done
    echo ""
done

# Cleanup temporary policy files
rm -f /tmp/topic_policy.json /tmp/sub_policy.json

echo "Pub/Sub generation script finished!"
