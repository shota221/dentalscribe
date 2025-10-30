output "sns_topic_arn" {
  description = "ARN of the SNS topic for CloudWatch alarms"
  value       = aws_sns_topic.cloudwatch_alarms.arn
}

output "alarm_names" {
  description = "List of all CloudWatch alarm names"
  value = [
    aws_cloudwatch_metric_alarm.lambda_errors.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_throttles.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_duration.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_concurrent_executions.alarm_name,
    aws_cloudwatch_metric_alarm.dynamodb_read_throttles.alarm_name,
    aws_cloudwatch_metric_alarm.dynamodb_write_throttles.alarm_name,
    aws_cloudwatch_metric_alarm.sqs_oldest_message_age.alarm_name,
    aws_cloudwatch_metric_alarm.sqs_messages_visible.alarm_name,
    aws_cloudwatch_metric_alarm.dlq_messages.alarm_name,
    aws_cloudwatch_metric_alarm.api_gateway_5xx_errors.alarm_name,
    aws_cloudwatch_metric_alarm.api_gateway_4xx_errors.alarm_name,
    aws_cloudwatch_metric_alarm.api_gateway_latency.alarm_name,
  ]
}
