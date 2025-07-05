terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Fetch default VPC for SG attachment
data "aws_vpc" "default" {
  default = true
}

# Import SSH key pair
resource "aws_key_pair" "hemanshi_key" {
  key_name   = "hemanshi-key"
  public_key = file("/home/ec2-user/.ssh/hemanshi-key.pub")
}

# Security Group to allow SSH and all other inbound traffic
resource "aws_security_group" "app_sg" {
  name        = "app-sg"
  description = "Allow SSH and all inbound traffic"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Allow SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow all inbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Amazon ECR repositories
resource "aws_ecr_repository" "webapp" {
  name = "webapp"
}

resource "aws_ecr_repository" "mysql" {
  name = "mysql"
}

# EC2 instance with 20 GB root volume
resource "aws_instance" "app_server" {
  ami                         = "ami-0c02fb55956c7d316" # Amazon Linux 2
  instance_type               = "t3.large"
  key_name                    = aws_key_pair.hemanshi_key.key_name
  associate_public_ip_address = true
  iam_instance_profile        = "LabInstanceProfile" # Must exist or define this in TF
  vpc_security_group_ids      = [aws_security_group.app_sg.id]

  root_block_device {
    volume_size = 20
    volume_type = "gp2"
  }

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install docker -y
              service docker start
              usermod -aG docker ec2-user
              EOF

  tags = {
    Name = "CLO835AppServer"
  }
}
