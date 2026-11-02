variable "aws_region" {
  description = "AWS region for deployment (Default: Mumbai)"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project identifier for resource naming and tagging"
  type        = string
  default     = "enterprise-ai"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for the dedicated VPCs"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet where EC2 lives"
  type        = string
  default     = "10.0.1.0/24"
}

variable "instance_type" {
  description = "EC2 instance type (t3.medium is ideal since LLM is offloaded to OpenRoute)"
  type        = string
  default     = "c7i-flex.large"
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for ssh access (Restrict to your IP in production)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "key_name" {
  description = "Name of existing AWS EC2 Key Pair for SSH access"
  type        = string
  default     = "argo-cd"
}