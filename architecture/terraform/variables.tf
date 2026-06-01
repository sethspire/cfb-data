variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "S3 bucket name for the project"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ssh_allowed_ip" {
  description = "CIDR block allowed to SSH into the instance (e.g. 203.0.113.0/32 for a single IP)"
  type        = string
}

variable "key_name" {
  description = "Name of an existing EC2 key pair to use for SSH"
  type        = string
}

variable "ami_owner" {
  description = "Owner of the AMI (amazon for official Amazon Linux)"
  type        = string
  default     = "amazon"
}

variable "ami_name_filter" {
  description = "Name filter for the AMI"
  type        = string
  default     = "al2023-ami-*-kernel-6.1-x86_64"
}

variable "cfbd_api_key" {
  description = "CollegeFootballData.com API key"
  type        = string
  sensitive   = true
}
