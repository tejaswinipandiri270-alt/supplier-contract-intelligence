# AWS deployment checklist

This repository includes scripts and task-definition examples, but AWS resources must be created in your own account.

1. Create an S3 bucket and upload PDFs with `aws/upload_to_s3.sh`.
2. Create an Amazon OpenSearch Service domain with fine-grained access or IAM-based access. Configure network access so ECS can reach it.
3. Create an ECR repository.
4. Create an ECS cluster using Fargate and an ECS service with a load balancer or reachable networking.
5. Create an ECS task execution role with `AmazonECSTaskExecutionRolePolicy` plus `secretsmanager:GetSecretValue` and `kms:Decrypt` permissions for the selected secret.
6. Create a task role with least-privilege `s3:ListBucket` / `s3:GetObject` permissions for the contract bucket. Add required OpenSearch permissions according to the domain access policy.
7. Store these JSON secret keys in Secrets Manager: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AWS_OPENSEARCH_HOST`, `AWS_OPENSEARCH_USERNAME`, `AWS_OPENSEARCH_PASSWORD`.
8. Set environment variables required by `aws/deploy_ecr_ecs.sh` and run it from a shell with AWS CLI and Docker configured.
9. Run ingestion as a one-off ECS task/job with the same image and permissions, overriding the command to `python -m app.ingest`. Do not rely on the API container to ingest documents automatically.
10. Confirm `/health` and `/query` through the service URL.

Important:
- The included task definition is a starter template, not a complete network/security provisioning stack.
- For managed OpenSearch domains, configure HTTPS and the correct authentication method. The example supports basic auth or AWS SigV4; align this with your domain's access policy.
- The sample task definition uses Secrets Manager JSON-key injection. Ensure the secret is a JSON object and the ECS platform/region supports JSON-key selection.
- Add a load balancer, TLS certificate, security groups and private networking for a production deployment.
- Tear down ECS and OpenSearch resources when not in use to avoid charges.
