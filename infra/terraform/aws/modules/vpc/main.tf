resource "aws_vpc" "vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "vpc-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
    ManagedBy   = "Terraform"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id

  tags = {
    Name        = "igw-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = "${var.region}a"

  tags = {
    Name        = "subnet-public-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

resource "aws_subnet" "public_subnet_b" {
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = var.public_subnet_b_cidr
  map_public_ip_on_launch = true
  availability_zone       = "${var.region}b"

  tags = {
    Name        = "subnet-public-b-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name        = "rt-public-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_assoc_b" {
  subnet_id      = aws_subnet.public_subnet_b.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_subnet" "private_subnet_a" {
  count                   = var.create_private_subnets ? 1 : 0
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = var.private_subnet_a_cidr
  map_public_ip_on_launch = false
  availability_zone       = "${var.region}a"

  tags = {
    Name        = "subnet-private-a-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
    Type        = "Private"
  }
}

resource "aws_subnet" "private_subnet_b" {
  count                   = var.create_private_subnets ? 1 : 0
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = var.private_subnet_b_cidr
  map_public_ip_on_launch = false
  availability_zone       = "${var.region}b"

  tags = {
    Name        = "subnet-private-b-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
    Type        = "Private"
  }
}

resource "aws_route_table" "private_rt" {
  count  = var.create_private_subnets ? 1 : 0
  vpc_id = aws_vpc.vpc.id

  tags = {
    Name        = "rt-private-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

resource "aws_route_table_association" "private_assoc_a" {
  count          = var.create_private_subnets ? 1 : 0
  subnet_id      = aws_subnet.private_subnet_a[0].id
  route_table_id = aws_route_table.private_rt[0].id
}

resource "aws_route_table_association" "private_assoc_b" {
  count          = var.create_private_subnets ? 1 : 0
  subnet_id      = aws_subnet.private_subnet_b[0].id
  route_table_id = aws_route_table.private_rt[0].id
}

variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "public_subnet_b_cidr" {
  type    = string
  default = "10.0.2.0/24"
}

variable "create_private_subnets" {
  type        = bool
  default     = false
  description = "Create dedicated private subnets for database tier"
}

variable "private_subnet_a_cidr" {
  type        = string
  default     = "10.0.10.0/24"
  description = "Dedicated Private Subnet A CIDR block for RDS"
}

variable "private_subnet_b_cidr" {
  type        = string
  default     = "10.0.20.0/24"
  description = "Dedicated Private Subnet B CIDR block for RDS"
}

output "vpc_id" {
  value = aws_vpc.vpc.id
}

output "public_subnet_id" {
  value = aws_subnet.public_subnet.id
}

output "subnet_ids" {
  value = [aws_subnet.public_subnet.id, aws_subnet.public_subnet_b.id]
}

output "private_subnet_ids" {
  value = var.create_private_subnets ? [aws_subnet.private_subnet_a[0].id, aws_subnet.private_subnet_b[0].id] : [aws_subnet.public_subnet.id, aws_subnet.public_subnet_b.id]
}
