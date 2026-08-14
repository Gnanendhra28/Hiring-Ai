output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "Staging VPC ID"
}

output "public_subnet_id" {
  value       = module.vpc.public_subnet_id
  description = "Staging Public Subnet ID"
}

output "ec2_security_group_id" {
  value       = module.security_groups.ec2_security_group_id
  description = "EC2 Host Security Group ID"
}

output "rds_security_group_id" {
  value       = module.security_groups.rds_security_group_id
  description = "RDS Security Group ID"
}

output "rds_endpoint" {
  value       = module.rds.rds_endpoint
  description = "Staging RDS PostgreSQL Endpoint"
}

output "s3_bucket_name" {
  value       = module.s3.s3_bucket_name
  description = "Staging Candidate Documents S3 Bucket Name"
}

output "sqs_queue_url" {
  value       = module.sqs.sqs_queue_url
  description = "Staging Application Events SQS Queue URL"
}

output "ecr_backend_url" {
  value       = module.ecr.ecr_backend_url
  description = "ECR Backend Repository URL"
}

output "ecr_frontend_url" {
  value       = module.ecr.ecr_frontend_url
  description = "ECR Frontend Repository URL"
}

output "ecr_worker_url" {
  value       = module.ecr.ecr_worker_url
  description = "ECR Worker Repository URL"
}

output "ec2_instance_id" {
  value       = module.ec2.ec2_instance_id
  description = "Staging EC2 Host Instance ID"
}

output "ec2_public_ip" {
  value       = module.ec2.ec2_public_ip
  description = "Staging EC2 Host Public IP Address"
}
