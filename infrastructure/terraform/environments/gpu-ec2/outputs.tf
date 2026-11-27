output "instance_id" {
  value       = aws_instance.gpu.id
  description = "The one project-owned L4 instance."
}

output "instance_type" {
  value       = aws_instance.gpu.instance_type
  description = "Selected single-L4 instance size."
}

output "ubuntu_ami_id" {
  value       = data.aws_ami.ubuntu.id
  description = "Exact Canonical Ubuntu 24.04 image ID resolved by this plan."
}

output "availability_zone" {
  value       = aws_instance.gpu.availability_zone
  description = "Availability zone selected for the lab."
}

output "expiry_utc" {
  value       = var.expires_at
  description = "The guest timer and EventBridge Scheduler termination deadline."
}

output "public_ip" {
  value       = aws_instance.gpu.public_ip
  description = "Outbound address for SSM and downloads; no inbound rules are configured."
}
