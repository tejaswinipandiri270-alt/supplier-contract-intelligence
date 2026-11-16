#!/usr/bin/env bash
# Run after creating the S3 bucket, OpenSearch domain, Secrets Manager secret and ECS IAM roles.
set -euo pipefail
: "${AWS_REGION:=eu-west-2}"
: "${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
: "${ECR_REPOSITORY:=supplier-contract-api}"
: "${ECS_CLUSTER:=supplier-contract-cluster}"
: "${ECS_SERVICE:=supplier-contract-service}"
: "${TASK_FAMILY:=supplier-contract-task}"
: "${SUBNET_IDS:?Set comma-separated SUBNET_IDS}"
: "${SECURITY_GROUP_ID:?Set SECURITY_GROUP_ID}"
: "${TASK_EXECUTION_ROLE_ARN:?Set TASK_EXECUTION_ROLE_ARN}"
: "${TASK_ROLE_ARN:?Set TASK_ROLE_ARN}"
: "${CONTAINER_SECRETS_ARN:?Set Secrets Manager secret ARN}"

IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest"
aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" >/dev/null 2>&1 ||   aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
docker build -t "$ECR_REPOSITORY:latest" .
docker tag "$ECR_REPOSITORY:latest" "$IMAGE"
docker push "$IMAGE"

aws ecs describe-clusters --clusters "$ECS_CLUSTER" --region "$AWS_REGION" >/dev/null
cat > /tmp/task-def.json <<EOF
{
  "family": "${TASK_FAMILY}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "3072",
  "executionRoleArn": "${TASK_EXECUTION_ROLE_ARN}",
  "taskRoleArn": "${TASK_ROLE_ARN}",
  "containerDefinitions": [{
    "name": "api",
    "image": "${IMAGE}",
    "essential": true,
    "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
    "environment": [
      {"name":"APP_ENV","value":"aws"},
      {"name":"AWS_REGION","value":"${AWS_REGION}"},
      {"name":"USE_S3","value":"true"},
      {"name":"S3_PREFIX","value":"supplier-contracts/"},
      {"name":"OPENSEARCH_INDEX","value":"supplier-contract-chunks"}
    ],
    "secrets": [
      {"name":"AZURE_OPENAI_ENDPOINT","valueFrom":"${CONTAINER_SECRETS_ARN}:AZURE_OPENAI_ENDPOINT::"},
      {"name":"AZURE_OPENAI_API_KEY","valueFrom":"${CONTAINER_SECRETS_ARN}:AZURE_OPENAI_API_KEY::"},
      {"name":"AZURE_OPENAI_CHAT_DEPLOYMENT","valueFrom":"${CONTAINER_SECRETS_ARN}:AZURE_OPENAI_CHAT_DEPLOYMENT::"},
      {"name":"AWS_OPENSEARCH_HOST","valueFrom":"${CONTAINER_SECRETS_ARN}:AWS_OPENSEARCH_HOST::"},
      {"name":"AWS_OPENSEARCH_USERNAME","valueFrom":"${CONTAINER_SECRETS_ARN}:AWS_OPENSEARCH_USERNAME::"},
      {"name":"AWS_OPENSEARCH_PASSWORD","valueFrom":"${CONTAINER_SECRETS_ARN}:AWS_OPENSEARCH_PASSWORD::"}
    ],
    "logConfiguration":{"logDriver":"awslogs","options":{
      "awslogs-group":"/ecs/supplier-contract-api",
      "awslogs-region":"${AWS_REGION}",
      "awslogs-stream-prefix":"ecs"
    }}
  }]
}
EOF
aws ecs register-task-definition --cli-input-json file:///tmp/task-def.json --region "$AWS_REGION"
aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --task-definition "$TASK_FAMILY" --force-new-deployment --region "$AWS_REGION"
echo "Deployment submitted. Check ECS service events and task health."
