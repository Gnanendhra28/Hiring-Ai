output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "Production VPC ID"
}

output "public_subnet_id" {
  value       = module.vpc.public_subnet_id
  description = "Production Public Subnet A ID"
}

output "subnet_ids" {
  value       = module.vpc.subnet_ids
  description = "Production Subnet IDs list"
}

output "ec2_security_group_id" {
  value       = module.security_groups.ec2_security_group_id
  description = "Production EC2 Security Group ID"
}

output "rds_security_group_id" {
  value       = module.security_groups.rds_security_group_id
  description = "Production RDS Security Group ID"
}

output "rds_endpoint" {
  value       = module.rds.rds_endpoint
  description = "Production RDS PostgreSQL Endpoint"
}

output "s3_bucket_name" {
  value       = module.s3.s3_bucket_name
  description = "Production Candidate Documents S3 Bucket Name"
}

output "sqs_queue_url" {
  value       = module.sqs.sqs_queue_url
  description = "Production Application Events SQS Queue URL"
}

output "sqs_dlq_arn" {
  value       = module.sqs.sqs_dlq_arn
  description = "Production Dead-Letter Queue ARN"
}

output "ecr_backend_url" {
  value       = module.ecr.ecr_backend_url
  description = "Production ECR Backend Repository URL"
}

output "ecr_frontend_url" {
  value       = module.ecr.ecr_frontend_url
  description = "Production ECR Frontend Repository URL"
}

output "ecr_worker_url" {
  value       = module.ecr.ecr_worker_url
  description = "Production ECR Worker Repository URL"
}

output "ec2_instance_id" {
  value       = module.ec2.ec2_instance_id
  description = "Production EC2 Host Instance ID"
}

output "ec2_public_ip" {
  value       = module.ec2.ec2_public_ip
  description = "Production EC2 Host Public IP Address"
}
