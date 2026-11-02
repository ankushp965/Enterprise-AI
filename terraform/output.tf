output "ec2_instance_id" {
  description = "The ID of the provisioned EC2 instance"
  value       = aws_instance.app_server.id
}

output "ec2_public_ip" {
  description = "The public IPv4 address of the EC2 instance"
  value       = aws_instance.app_server.public_ip
}

output "ec2_public_dns" {
  description = "The public DNS name of the EC2 instance"
  value       = aws_instance.app_server.public_dns
}

output "application_url" {
  description = "Web URL to access the Enterprise AI Policy Assistant via Nginx"
  value       = "http://${aws_instance.app_server.public_ip}"
}

output "phoenix_observability_url" {
  description = "URL to access the Arize Phoenix Observability dashboard"
  value       = "http://${aws_instance.app_server.public_ip}/phoenix/"
}

output "ssh_login_command" {
  description = "Command to SSH into the EC2 instance"
  value       = "ssh -i <your-key.pem> ubuntu@${aws_instance.app_server.public_ip}"
}