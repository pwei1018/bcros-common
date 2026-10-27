#!/bin/bash
#
# Create Pub/Sub topics and push subscriptions for the BC Notify delivery workers
# (email, Housing email, SMS and Housing SMS) in the Common projects.
#
# Settings are copied from the existing GC Notify subscription in each project:
# push service account/audience, ack deadline, retry backoff, retention, dead-letter
# topic and IAM bindings. Existing topics and subscriptions are left untouched.
#
# Usage:
#   ./create_pubsub_bc_notify.sh [env]          # env: dev | test | sandbox | prod (default: all)
#   DRY_RUN=1 ./create_pubsub_bc_notify.sh dev  # print what would be created
#
# Note: Ensure you are authenticated with gcloud with sufficient permissions.

set -euo pipefail

GCLOUD="${GCLOUD:-gcloud}"
REGION="northamerica-northeast1"
DRY_RUN="${DRY_RUN:-}"

if [ -z "${1:-}" ]; then
  ENVS=("dev" "test" "sandbox" "prod")
else
  ENVS=("$1")
fi

run() {
  if [[ -n "$DRY_RUN" ]]; then
    echo "    [dry-run] $*"
  else
    "$@"
  fi
}

echo "Starting Pub/Sub topic and subscription generation..."

for ENV in "${ENVS[@]}"; do
  PROJECT_ID="c4hnrd-${ENV}"

  echo "=========================================================="
  echo "Processing Project: $PROJECT_ID (Environment: $ENV)"
  echo "=========================================================="

  BASE_URL=$("$GCLOUD" run services describe "notify-delivery-${ENV}" --project="$PROJECT_ID" \
    --region="$REGION" --format="value(status.url)" 2>/dev/null || true)
  if [[ -z "$BASE_URL" ]]; then
    echo "    [Error] Cloud Run service notify-delivery-${ENV} not found. Skipping project."
    continue
  fi
  echo "    notify-delivery URL: $BASE_URL"

  # Reference GC Notify topic to copy configuration and permissions from
  TOPIC_GCNOTIFY="notify-delivery-gcnotify-${ENV}"
  if ! "$GCLOUD" pubsub topics describe "$TOPIC_GCNOTIFY" --project="$PROJECT_ID" &>/dev/null; then
    echo "    [Error] GC Notify topic $TOPIC_GCNOTIFY does not exist. Skipping project."
    continue
  fi

  REF_SUB=$("$GCLOUD" pubsub topics list-subscriptions "$TOPIC_GCNOTIFY" --project="$PROJECT_ID" \
    --format="value(.)" | head -n 1)
  REF_SUB=$(basename "${REF_SUB:-}")
  if [[ -z "$REF_SUB" ]]; then
    echo "    [Error] No subscription found for $TOPIC_GCNOTIFY. Skipping project."
    continue
  fi
  echo "    Reference subscription: $REF_SUB"

  IFS='|' read -r SERVICE_ACCOUNT AUDIENCE ACK_DEADLINE MIN_BACKOFF MAX_BACKOFF RETENTION DLQ_TOPIC MAX_ATTEMPTS < <(
    "$GCLOUD" pubsub subscriptions describe "$REF_SUB" --project="$PROJECT_ID" \
      --format="value[separator='|'](pushConfig.oidcToken.serviceAccountEmail,pushConfig.oidcToken.audience,ackDeadlineSeconds,retryPolicy.minimumBackoff,retryPolicy.maximumBackoff,messageRetentionDuration,deadLetterPolicy.deadLetterTopic,deadLetterPolicy.maxDeliveryAttempts)"
  )
  SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com}"
  echo "    Service account: $SERVICE_ACCOUNT, audience: ${AUDIENCE:-<push endpoint>}, ack: ${ACK_DEADLINE}s," \
    "backoff: ${MIN_BACKOFF:-default}-${MAX_BACKOFF:-default}, retention: ${RETENTION:-default}," \
    "dead-letter: ${DLQ_TOPIC:-none} (${MAX_ATTEMPTS:-n/a} attempts)"

  SUB_FLAGS=(--push-auth-service-account="$SERVICE_ACCOUNT" --expiration-period=never)
  [[ -n "$AUDIENCE" ]] && SUB_FLAGS+=(--push-auth-token-audience="$AUDIENCE")
  [[ -n "$ACK_DEADLINE" ]] && SUB_FLAGS+=(--ack-deadline="$ACK_DEADLINE")
  [[ -n "$MIN_BACKOFF" ]] && SUB_FLAGS+=(--min-retry-delay="$MIN_BACKOFF")
  [[ -n "$MAX_BACKOFF" ]] && SUB_FLAGS+=(--max-retry-delay="$MAX_BACKOFF")
  [[ -n "$RETENTION" ]] && SUB_FLAGS+=(--message-retention-duration="$RETENTION")
  [[ -n "$DLQ_TOPIC" ]] && SUB_FLAGS+=(--dead-letter-topic="$DLQ_TOPIC" --max-delivery-attempts="${MAX_ATTEMPTS:-5}")

  # topic name -> notify-delivery blueprint path (see notify_delivery/resources/__init__.py)
  TOPICS=(
    "notify-delivery-bc-notify-${ENV}"
    "notify-delivery-bc-notify-housing-${ENV}"
    "notify-delivery-bc-notify-sms-${ENV}"
    "notify-delivery-bc-notify-housing-sms-${ENV}"
  )
  PATHS=("/bcnotify" "/bcnotify-housing" "/bcnotify-sms" "/bcnotify-housing-sms")

  for i in "${!TOPICS[@]}"; do
    TOPIC="${TOPICS[$i]}"
    PUSH_ENDPOINT="${BASE_URL}${PATHS[$i]}"

    echo "--> Topic: $TOPIC"
    if "$GCLOUD" pubsub topics describe "$TOPIC" --project="$PROJECT_ID" &>/dev/null; then
      echo "    [Info] Topic already exists."
    else
      run "$GCLOUD" pubsub topics create "$TOPIC" --project="$PROJECT_ID"
      [[ -z "$DRY_RUN" ]] && echo "    [Success] Created topic."
    fi

    # Bindings are added individually; set-iam-policy with the reference policy's etag is rejected.
    while IFS=$'\t' read -r ROLE MEMBER; do
      [[ -z "$ROLE" ]] && continue
      run "$GCLOUD" pubsub topics add-iam-policy-binding "$TOPIC" --project="$PROJECT_ID" \
        --role="$ROLE" --member="$MEMBER" --format=none
    done < <("$GCLOUD" pubsub topics get-iam-policy "$TOPIC_GCNOTIFY" --project="$PROJECT_ID" \
      --flatten="bindings[].members" --format="value[separator='\t'](bindings.role,bindings.members)")

    # Any existing subscription already pushes this topic; a second one would deliver every message twice.
    EXISTING_SUB=$("$GCLOUD" pubsub topics list-subscriptions "$TOPIC" --project="$PROJECT_ID" \
      --format="value(.)" 2>/dev/null | head -n 1 || true)
    if [[ -n "$EXISTING_SUB" ]]; then
      SUBSCRIPTION=$(basename "$EXISTING_SUB")
      CURRENT_ENDPOINT=$("$GCLOUD" pubsub subscriptions describe "$SUBSCRIPTION" --project="$PROJECT_ID" \
        --format="value(pushConfig.pushEndpoint)")
      echo "    [Info] Subscription $SUBSCRIPTION already exists -> $CURRENT_ENDPOINT"
      [[ "$CURRENT_ENDPOINT" != "$PUSH_ENDPOINT" ]] && echo "    [Warning] Expected endpoint $PUSH_ENDPOINT"
    else
      SUBSCRIPTION="${TOPIC}-sub"
      run "$GCLOUD" pubsub subscriptions create "$SUBSCRIPTION" --topic="$TOPIC" --project="$PROJECT_ID" \
        --push-endpoint="$PUSH_ENDPOINT" "${SUB_FLAGS[@]}"
      [[ -z "$DRY_RUN" ]] && echo "    [Success] Created subscription $SUBSCRIPTION -> $PUSH_ENDPOINT"
    fi

    while IFS=$'\t' read -r ROLE MEMBER; do
      [[ -z "$ROLE" ]] && continue
      run "$GCLOUD" pubsub subscriptions add-iam-policy-binding "$SUBSCRIPTION" --project="$PROJECT_ID" \
        --role="$ROLE" --member="$MEMBER" --format=none
    done < <("$GCLOUD" pubsub subscriptions get-iam-policy "$REF_SUB" --project="$PROJECT_ID" \
      --flatten="bindings[].members" --format="value[separator='\t'](bindings.role,bindings.members)")
  done
  echo ""
done

echo "Pub/Sub generation script finished!"
