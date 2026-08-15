# CloudWatch Log Groups & Alarms Module

variable "environment" { type = string }
variable "region" { type = string }
variable "ec2_instance_id" { type = string }
variable "rds_instance_id" { type = string }
variable "sqs_queue_name" { type = string }
variable "sqs_dlq_name" { type = string }

# Log Groups
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/hiring-ai/${var.environment}/backend"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Service     = "backend"
  }
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/hiring-ai/${var.environment}/worker"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Service     = "worker"
  }
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/hiring-ai/${var.environment}/frontend"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Service     = "frontend"
  }
}

resource "aws_cloudwatch_log_group" "caddy" {
  name              = "/hiring-ai/${var.environment}/caddy"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Service     = "caddy"
  }
}

# EC2 CPU Alarm (HIGH)
resource "aws_cloudwatch_metric_alarm" "ec2_cpu_high" {
  alarm_name          = "ec2-cpu-utilization-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "EC2 host CPU utilization exceeds 80%"

  dimensions = {
    InstanceId = var.ec2_instance_id
  }
}

# RDS CPU Alarm (HIGH)
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "rds-cpu-utilization-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS PostgreSQL database CPU utilization exceeds 80%"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }
}

# RDS Free Storage Alarm (CRITICAL)
resource "aws_cloudwatch_metric_alarm" "rds_storage_low" {
  alarm_name          = "rds-free-storage-crit-${var.environment}"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120 # 5 GB in bytes
  alarm_description   = "RDS PostgreSQL free storage space is below 5 GB"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }
}

# RDS Connection Pool Capacity Alarm (HIGH)
resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  alarm_name          = "rds-database-connections-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 16 # 80% of 20 max app connections
  alarm_description   = "RDS PostgreSQL database active connections exceed 80% of application limit"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }
}

# SQS DLQ Depth Alarm (CRITICAL)
resource "aws_cloudwatch_metric_alarm" "sqs_dlq_depth_crit" {
  alarm_name          = "sqs-dlq-messages-visible-crit-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Dead-letter queue contains unhandled failed event messages"

  dimensions = {
    QueueName = var.sqs_dlq_name
  }
}

# SQS Oldest Message Age Alarm (HIGH)
resource "aws_cloudwatch_metric_alarm" "sqs_oldest_message_age_high" {
  alarm_name          = "sqs-oldest-message-age-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 300 # 5 minutes
  alarm_description   = "SQS application event queue age of oldest message exceeds 5 minutes"

  dimensions = {
    QueueName = var.sqs_queue_name
  }
}

output "log_group_backend" { value = aws_cloudwatch_log_group.backend.name }
output "log_group_worker" { value = aws_cloudwatch_log_group.worker.name }
output "log_group_frontend" { value = aws_cloudwatch_log_group.frontend.name }
output "log_group_caddy" { value = aws_cloudwatch_log_group.caddy.name }
