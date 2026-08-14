resource "aws_security_group" "ec2_sg" {
  name        = "hiring-ec2-sg-${var.environment}"
  description = "Security group for Hiring AI EC2 host"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "hiring-ec2-sg-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "hiring-rds-sg-${var.environment}"
  description = "Security group for Hiring AI RDS PostgreSQL (restricted to EC2)"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "hiring-rds-sg-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "admin_cidr" {
  type    = string
  default = "127.0.0.1/32"
}

output "ec2_security_group_id" {
  value = aws_security_group.ec2_sg.id
}

output "rds_security_group_id" {
  value = aws_security_group.rds_sg.id
}
