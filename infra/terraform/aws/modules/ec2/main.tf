data "aws_ami" "ubuntu_arm64" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/*ubuntu-*24.04*arm64*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_iam_role" "runtime_role" {
  name = "HiringAIRuntimeRole-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.runtime_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_caller_identity" "current" {}

locals {
  s3_env = var.environment == "production" ? "prod" : var.environment
}

resource "aws_iam_role_policy" "runtime_policy" {
  name = "HiringAIRuntimePolicy-${var.environment}"
  role = aws_iam_role.runtime_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::sthiring-documents-${local.s3_env}-${var.region}",
          "arn:aws:s3:::sthiring-documents-${local.s3_env}-${var.region}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          "arn:aws:sqs:${var.region}:${data.aws_caller_identity.current.account_id}:${var.environment}-application-events",
          "arn:aws:sqs:${var.region}:${data.aws_caller_identity.current.account_id}:${var.environment}-application-events-dlq"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/hiring-ai/${var.environment}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}


resource "aws_iam_instance_profile" "instance_profile" {
  name = "HiringAIInstanceProfile-${var.environment}"
  role = aws_iam_role.runtime_role.name
}

resource "aws_instance" "ec2_host" {
  ami                    = data.aws_ami.ubuntu_arm64.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  iam_instance_profile   = aws_iam_instance_profile.instance_profile.name

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y snapd docker.io docker-compose-v2
              snap install amazon-ssm-agent --classic
              systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
              systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service
              systemctl enable docker
              systemctl start docker
              usermod -aG docker ubuntu
              EOF

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name        = "ec2-hiring-host-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "security_group_id" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "t4g.small"
}

output "ec2_instance_id" {
  value = aws_instance.ec2_host.id
}

output "ec2_public_ip" {
  value = aws_instance.ec2_host.public_ip
}
