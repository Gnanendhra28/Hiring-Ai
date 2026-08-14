resource "aws_sqs_queue" "dlq" {
  name                      = "${var.environment}-application-events-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Name        = "${var.environment}-application-events-dlq"
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "events" {
  name                       = "${var.environment}-application-events"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 345600 # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name        = "${var.environment}-application-events"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

variable "environment" { type = string }

output "sqs_queue_url" { value = aws_sqs_queue.events.url }
output "sqs_queue_arn" { value = aws_sqs_queue.events.arn }
output "sqs_dlq_arn" { value = aws_sqs_queue.dlq.arn }
