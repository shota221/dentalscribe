variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "environment" {
  description = "Environment name (dev, stg, prod)"
  type        = string
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "dentalscribe"
}

variable "lambda_function_name" {
  description = "Lambda function name deployed by Chalice"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for jobs"
  type        = string
}

variable "sqs_queue_name" {
  description = "SQS queue name for job processing"
  type        = string
}

variable "sqs_dlq_name" {
  description = "SQS Dead Letter Queue name"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name for voice files"
  type        = string
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
}

variable "lambda_error_threshold" {
  description = "Lambda error rate threshold (percentage)"
  type        = number
  default     = 5
}

variable "lambda_duration_threshold" {
  description = "Lambda duration threshold (milliseconds)"
  type        = number
  default     = 30000
}

variable "sqs_age_threshold" {
  description = "SQS message age threshold (seconds)"
  type        = number
  default     = 600
}

variable "dlq_message_threshold" {
  description = "DLQ message count threshold"
  type        = number
  default     = 1
}
