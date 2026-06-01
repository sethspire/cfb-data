output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.backfill.id
}

output "public_ip" {
  description = "Public IP of the backfill instance"
  value       = aws_instance.backfill.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i <your-key.pem> ec2-user@${aws_instance.backfill.public_ip}"
}
