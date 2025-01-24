#!/bin/bash

source .env

IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

ENV_VARS="PROJECT_ID=$PROJECT_ID,REGION=$REGION,BIGQUERY_TABLE=$BIGQUERY_TABLE,IMAGE_BASE_URL=$IMAGE_BASE_URL"

if echo "" | gcloud projects list &> /dev/null; then
    echo "Logged in. "
else
    echo "Not logged in"
    gcloud auth login
fi

gcloud config set project $PROJECT_ID

gcloud builds submit --tag $IMAGE

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --set-env-vars $ENV_VARS \
  --allow-unauthenticated

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "Service deployed to: $SERVICE_URL"
