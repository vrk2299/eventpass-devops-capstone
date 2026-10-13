output "app_url" {
  description = "Open the app after cloud-init finishes (usually 2-3 minutes)"
  value       = "http://${aws_instance.app.public_ip}"
}

output "instance_public_ip" { value = aws_instance.app.public_ip }
