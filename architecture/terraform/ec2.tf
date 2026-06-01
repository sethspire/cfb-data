data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = [var.ami_owner]

  filter {
    name   = "name"
    values = [var.ami_name_filter]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

resource "aws_instance" "backfill" {
  ami                  = data.aws_ami.amazon_linux.id
  instance_type        = var.instance_type
  iam_instance_profile = aws_iam_instance_profile.backfill.name
  key_name             = var.key_name
  security_groups      = [aws_security_group.backfill_ssh.name]
  user_data            = templatefile("${path.module}/user-data.tftpl", {
    cfbd_api_key = var.cfbd_api_key
    bucket_name  = var.bucket_name
  })
  user_data_replace_on_change = true

  tags = {
    Name = "cfb-data-backfill"
  }
}
