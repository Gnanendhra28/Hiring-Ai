# Staging AWS Minimum-Cost Infrastructure Definition

module "vpc" {
  source      = "../../modules/vpc"
  environment = var.environment
  region      = var.region
}

module "security_groups" {
  source      = "../../modules/security_groups"
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  admin_cidr  = var.admin_cidr
}

module "rds" {
  source                = "../../modules/rds"
  environment           = var.environment
  subnet_ids            = module.vpc.subnet_ids
  rds_security_group_id = module.security_groups.rds_security_group_id
  db_password           = var.db_password
  multi_az              = var.multi_az
}

module "s3" {
  source      = "../../modules/s3"
  environment = var.environment
  region      = var.region
}

module "sqs" {
  source      = "../../modules/sqs"
  environment = var.environment
}

module "ssm" {
  source      = "../../modules/ssm"
  environment = var.environment
}

module "ecr" {
  source      = "../../modules/ecr"
  environment = var.environment
}

module "ec2" {
  source            = "../../modules/ec2"
  environment       = var.environment
  region            = var.region
  subnet_id         = module.vpc.public_subnet_id
  security_group_id = module.security_groups.ec2_security_group_id
}
