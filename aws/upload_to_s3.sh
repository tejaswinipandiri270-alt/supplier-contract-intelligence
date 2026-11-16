#!/usr/bin/env bash
set -euo pipefail
: "${AWS_REGION:=eu-west-2}"
: "${S3_BUCKET:?Set S3_BUCKET first}"
aws s3 sync ./data/contracts "s3://${S3_BUCKET}/supplier-contracts/" --region "${AWS_REGION}" --exclude "*.json"
echo "PDF contracts uploaded."
