variable "aws_region" {
  description = "AWS region for the classroom deployment"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "Choose a small type available in your account and region"
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "Existing EC2 key pair name, used for initial deployment"
  type        = string
}

variable "instructor_ip_cidr" {
  description = "Your current public IPv4 address followed by /32"
  type        = string
}
