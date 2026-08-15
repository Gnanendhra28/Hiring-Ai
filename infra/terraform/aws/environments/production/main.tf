# Production AWS Infrastructure Definition

module "vpc" {
  source                 = "../../modules/vpc"
  environment            = var.environment
  region                 = var.region
  vpc_cidr               = var.vpc_cidr
  public_subnet_cidr     = var.public_subnet_cidr
  public_subnet_b_cidr   = var.public_subnet_b_cidr
  create_private_subnets = true
  private_subnet_a_cidr  = var.private_subnet_a_cidr
  private_subnet_b_cidr  = var.private_subnet_b_cidr
}

module "security_groups" {
  source      = "../../modules/security_groups"
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  admin_cidr  = var.admin_cidr
}

module "rds" {
  source                  = "../../modules/rds"
  environment             = var.environment
  subnet_ids              = module.vpc.private_subnet_ids
  rds_security_group_id   = module.security_groups.rds_security_group_id
  db_password             = var.db_password
  multi_az                = var.multi_az
  backup_retention_period = var.backup_retention_period
  deletion_protection     = var.deletion_protection
  skip_final_snapshot     = var.skip_final_snapshot
}

module "s3" {
  source      = "../../modules/s3"
  environment = "prod"
  region      = var.region
}

module "sqs" {
  source                    = "../../modules/sqs"
  environment               = "production"
  message_retention_seconds = 1209600 # 14 days
  max_receive_count         = 5
}

module "ssm" {
  source      = "../../modules/ssm"
  environment = "production"
}

module "ecr" {
  source               = "../../modules/ecr"
  environment          = "prod"
  image_tag_mutability = "IMMUTABLE"
}

module "ec2" {
  source            = "../../modules/ec2"
  environment       = var.environment
  region            = var.region
  subnet_id         = module.vpc.public_subnet_id
  security_group_id = module.security_groups.ec2_security_group_id
}

module "cloudwatch" {
  source          = "../../modules/cloudwatch"
  environment     = var.environment
  region          = var.region
  ec2_instance_id = module.ec2.ec2_instance_id
  rds_instance_id = module.rds.rds_instance_id
  sqs_queue_name  = module.sqs.queue_name
  sqs_dlq_name    = module.sqs.dlq_name
}

