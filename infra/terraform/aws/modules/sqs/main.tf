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
  message_retention_seconds  = var.message_retention_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = {
    Name        = "${var.environment}-application-events"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

variable "environment" { type = string }

variable "message_retention_seconds" {
  type    = number
  default = 345600
}

variable "max_receive_count" {
  type    = number
  default = 3
}

output "sqs_queue_url" { value = aws_sqs_queue.events.url }
output "sqs_queue_arn" { value = aws_sqs_queue.events.arn }
output "sqs_dlq_arn" { value = aws_sqs_queue.dlq.arn }
output "queue_name" { value = aws_sqs_queue.events.name }
output "dlq_name" { value = aws_sqs_queue.dlq.name }

