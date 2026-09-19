#!/bin/bash
# MA2 Backend — GCP Infrastructure Setup
# Run this once to set up the GCP project for Cloud Run + Cloud SQL
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - A GCP project created
#   - Billing enabled on the project
#
# Usage:
#   chmod +x gcp-setup.sh
#   ./gcp-setup.sh <PROJECT_ID> <REGION>

set -euo pipefail

PROJECT_ID="${1:?Usage: ./gcp-setup.sh <PROJECT_ID> <REGION>}"
REGION="${2:?Usage: ./gcp-setup.sh <PROJECT_ID> <REGION>}"

SERVICE_NAME="ma2-backend"
DB_INSTANCE="ma2-db"
DB_NAME="ma2"
DB_USER="ma2-app"
DB_PASSWORD=$(openssl rand -base64 24)
SA_NAME="ma2-backend-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== MA2 GCP Setup ==="
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "--- Enabling APIs ---"
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com

# Create service account with least-privilege
echo "--- Creating Service Account ---"
gcloud iam service-accounts create "$SA_NAME" \
    --display-name="MA2 Backend Service Account" \
    --description="Least-privilege SA for MA2 Cloud Run backend" \
    2>/dev/null || echo "Service account already exists"

# Grant roles (least privilege)
for ROLE in \
    roles/cloudsql.client \
    roles/secretmanager.secretAccessor \
    roles/logging.logWriter \
    roles/monitoring.metricWriter \
    roles/aiplatform.user; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="$ROLE" \
        --quiet
done

# Create Cloud SQL instance
echo "--- Creating Cloud SQL Instance ---"
gcloud sql instances create "$DB_INSTANCE" \
    --database-version=POSTGRES_16 \
    --tier=db-f1-micro \
    --region="$REGION" \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --availability-type=zonal \
    --require-ssl \
    2>/dev/null || echo "SQL instance already exists"

# Create database
gcloud sql databases create "$DB_NAME" \
    --instance="$DB_INSTANCE" \
    2>/dev/null || echo "Database already exists"

# Create database user
gcloud sql users create "$DB_USER" \
    --instance="$DB_INSTANCE" \
    --password="$DB_PASSWORD" \
    2>/dev/null || echo "User already exists, updating password"

gcloud sql users set-password "$DB_USER" \
    --instance="$DB_INSTANCE" \
    --password="$DB_PASSWORD"

# Get Cloud SQL connection name
CLOUD_SQL_CONNECTION=$(gcloud sql instances describe "$DB_INSTANCE" --format="value(connectionName)")

# Store Cloud SQL password in Secret Manager
echo "--- Storing Secrets ---"

echo -n "$DB_PASSWORD" | gcloud secrets create cloud-sql-password \
    --data-file=- \
    --replication-policy=automatic \
    2>/dev/null || echo "Secret exists, creating new version"

echo -n "$DB_PASSWORD" | gcloud secrets versions add cloud-sql-password --data-file=-

gcloud secrets add-iam-policy-binding cloud-sql-password \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Cloud SQL Instance:    $DB_INSTANCE"
echo "Cloud SQL Connection:  $CLOUD_SQL_CONNECTION"
echo "Database:              $DB_NAME"
echo "DB User:               $DB_USER"
echo "DB Password:           (stored in Secret Manager as 'cloud-sql-password')"
echo "Service Account:       $SA_EMAIL"
echo ""
echo "--- Next Steps ---"
echo ""
echo "1. Deploy with Cloud Build:"
echo "   cd backend"
echo "   gcloud builds submit \\"
echo "     --config=cloudbuild.yaml \\"
echo "     --substitutions=_REGION=$REGION,_SERVICE_NAME=$SERVICE_NAME,_CLOUD_SQL_INSTANCE=$CLOUD_SQL_CONNECTION,_SERVICE_ACCOUNT=$SA_EMAIL"
echo ""
echo "2. Set CORS origins to your Vercel domain:"
echo "   gcloud run services update $SERVICE_NAME \\"
echo "     --region=$REGION \\"
echo "     --update-env-vars='CORS_ORIGINS=[\"https://your-app.vercel.app\"]'"
echo ""
echo "3. Get the Cloud Run URL:"
echo "   gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)'"
echo ""
echo "4. Set the Cloud Run URL as BACKEND_URL in your Vercel project settings."
echo "   (Vercel rewrites /api/* to Cloud Run — no CORS needed.)"
echo ""
echo "5. Vertex AI uses the service account's IAM role (aiplatform.user) — no API key needed."
echo "   Model: gemini-2.0-flash, Location: $REGION"
