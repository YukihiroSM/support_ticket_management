#!/bin/bash
echo "Creating SQS queues"

awslocal sqs create-queue \
  --queue-name ticket-processing-dlq \
  --region us-east-1

DLQ_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/ticket-processing-dlq \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

# Main queue with DLQ redrive policy
awslocal sqs create-queue \
  --queue-name ticket-processing \
  --region us-east-1 \
  --attributes "{
    \"VisibilityTimeout\": \"60\",
    \"MessageRetentionPeriod\": \"345600\",
    \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
  }"

echo "Queues created."