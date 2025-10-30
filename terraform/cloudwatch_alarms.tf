# SNS Topic for CloudWatch Alarms
resource "aws_sns_topic" "cloudwatch_alarms" {
  name = "${var.app_name}-${var.environment}-cloudwatch-alarms"

  tags = {
    Name        = "${var.app_name}-${var.environment}-cloudwatch-alarms"
    Environment = var.environment
    Application = var.app_name
  }
}

resource "aws_sns_topic_subscription" "cloudwatch_alarms_email" {
  topic_arn = aws_sns_topic.cloudwatch_alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# Lambda Function Errors Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.app_name}-${var.environment}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = var.lambda_error_threshold
  alarm_description   = "Lambda function error rate is too high"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  ok_actions          = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-lambda-errors"
    Environment = var.environment
  }
}

# Lambda Function Throttles Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${var.app_name}-${var.environment}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda function is being throttled"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  ok_actions          = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-lambda-throttles"
    Environment = var.environment
  }
}

# Lambda Function Duration Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.app_name}-${var.environment}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = var.lambda_duration_threshold
  alarm_description   = "Lambda function duration is too high"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  ok_actions          = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-lambda-duration"
    Environment = var.environment
  }
}

# Lambda Concurrent Executions Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_concurrent_executions" {
  alarm_name          = "${var.app_name}-${var.environment}-lambda-concurrent-executions"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ConcurrentExecutions"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Maximum"
  threshold           = 100
  alarm_description   = "Lambda concurrent executions are too high"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  ok_actions          = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-lambda-concurrent-executions"
    Environment = var.environment
  }
}

# DynamoDB Read Throttle Events Alarm
resource "aws_cloudwatch_metric_alarm" "dynamodb_read_throttles" {
  alarm_name          = "${var.app_name}-${var.environment}-dynamodb-read-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ReadThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "DynamoDB read operations are being throttled"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  ok_actions          = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    TableName = var.dynamodb_table_name
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-dynamodb-read-throttles"
    Environment = var.environment
  }
}

# DynamoDB Write Throttle Events Alarm
resource "aws_cloudwatch_metric_alarm" "dynamodb_write_throttles" {
  alarm_name          = "${var.app_name}-${var.environment}-dynamodb-write-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "WriteThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "DynamoDB write operations are being throttled"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  ok_actions          = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    TableName = var.dynamodb_table_name
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-dynamodb-write-throttles"
    Environment = var.environment
  }
}

# SQS Queue - Approximate Age of Oldest Message Alarm
resource "aws_cloudwatch_metric_alarm" "sqs_oldest_message_age" {
  alarm_name          = "${var.app_name}-${var.environment}-sqs-oldest-message-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = var.sqs_age_threshold
  alarm_description   = "SQS messages are not being processed in time"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  ok_actions          = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    QueueName = var.sqs_queue_name
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-sqs-oldest-message-age"
    Environment = var.environment
  }
}

# SQS Queue - Number of Messages Visible Alarm
resource "aws_cloudwatch_metric_alarm" "sqs_messages_visible" {
  alarm_name          = "${var.app_name}-${var.environment}-sqs-messages-visible"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 100
  alarm_description   = "Too many messages are waiting in the SQS queue"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  ok_actions          = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    QueueName = var.sqs_queue_name
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-sqs-messages-visible"
    Environment = var.environment
  }
}

# Dead Letter Queue - Messages Available Alarm
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.app_name}-${var.environment}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = var.dlq_message_threshold
  alarm_description   = "Failed messages detected in Dead Letter Queue"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    QueueName = var.sqs_dlq_name
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-dlq-messages"
    Environment = var.environment
  }
}

# API Gateway 5XX Errors Alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx_errors" {
  alarm_name          = "${var.app_name}-${var.environment}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "API Gateway is returning too many 5XX errors"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  ok_actions          = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    ApiName = "${var.app_name}-${var.environment}"
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-api-5xx-errors"
    Environment = var.environment
  }
}

# API Gateway 4XX Errors Alarm (High rate indicates client errors)
resource "aws_cloudwatch_metric_alarm" "api_gateway_4xx_errors" {
  alarm_name          = "${var.app_name}-${var.environment}-api-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 50
  alarm_description   = "API Gateway is returning too many 4XX errors"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    ApiName = "${var.app_name}-${var.environment}"
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-api-4xx-errors"
    Environment = var.environment
  }
}

# API Gateway Latency Alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_latency" {
  alarm_name          = "${var.app_name}-${var.environment}-api-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Average"
  threshold           = 5000
  alarm_description   = "API Gateway latency is too high"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]

  dimensions = {
    ApiName = "${var.app_name}-${var.environment}"
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-api-latency"
    Environment = var.environment
  }
}
