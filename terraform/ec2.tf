# 1. Dynamically lookup the latest official Ubuntu 22.04 LTS AMI in the selected region
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical official AWS account ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# 2. EC2 Instance Resource
resource "aws_instance" "app_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  key_name = var.key_name != "" ? var.key_name : null

  # Execute automated bootstrap script on first boot
  user_data = file("${path.module}/scripts/user_data.sh")

  # 30 GB gp3 encrypted root disk
  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name = "${var.project_name}-root-disk"
    }
  }

  tags = {
    Name = "${var.project_name}-server"
  }
}