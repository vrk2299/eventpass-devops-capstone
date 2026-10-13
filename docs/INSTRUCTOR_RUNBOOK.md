# EventPass instructor runbook

## Before class

- Confirm AWS CLI identity and selected region. Check the account's budget and free-tier eligibility; no AWS usage is guaranteed to be free.
- Confirm Terraform, Docker Desktop, Git, and OpenSSH client are installed on the instructor machine.
- Have an EC2 key pair private key ready. Never put it in the repository or share it with students.
- Set your current public IP as `/32`; for a Jenkins deployment, use the Jenkins agent's public IP instead (or add a separate ingress rule for it).
- Keep the first run focused: provision the EC2 host before class if you only have four hours, while still letting students inspect the plan and resources.
- Ensure the GitHub webhook can reach Jenkins, or run the pipeline manually during class.

## Initial deployment checklist

1. Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and enter the AWS region, existing EC2 key pair name, and instructor IP CIDR.
2. Run `terraform init`, `terraform plan`, and `terraform apply` from `terraform/`.
3. Wait for cloud-init; inspect EC2 system log or connect over SSH if it takes longer than expected.
4. Run `scripts/deploy.ps1` from PowerShell using the Terraform IP output and matching PEM file.
5. Visit the app and `/health`; make a booking and verify it appears in `/admin`.
6. Check EC2 metrics in CloudWatch. Basic EC2 metrics appear automatically; detailed OS/container metrics need an agent and are intentionally not required in this minimal lab.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| SSH times out | The current client IP matches `instructor_ip_cidr`; route table has a default route to the internet gateway; instance has a public IP. |
| `Permission denied (publickey)` | Correct key pair name and matching private key; username is `ec2-user`. |
| Deploy script says Docker is unavailable | User data may still be running. Wait a minute, reconnect, and check `sudo cloud-init status --long`. |
| Site does not load | Check instance status checks, security group port 80, then `sudo docker ps` and `sudo docker logs eventpass` over SSH. |
| Health check fails | Inspect `sudo docker logs eventpass`; confirm container is listening on port 8000 and host mapping is port 80. |
| Ticket count resets | Ensure the Docker command mounts `/opt/eventpass/data:/data`; do not remove that folder when replacing the container. |
| Jenkins SSH blocked | Add the Jenkins agent's public IP as a `/32` ingress source before apply; do not expose port 22 to everyone. |

## After class

Keep the Terraform state file with the live infrastructure, and protect it because it records resource details. When the lab is finished, run `terraform destroy` and confirm the expected resources are being removed. Verify the EC2 instance is terminated in the console. This project uses no NAT gateway, load balancer, RDS, or paid logging service by default.

## Teaching boundaries

This app demonstrates deployment flow and ticket inventory, not a production ticket marketplace. Checkout is a mock flow. The organizer page is unauthenticated and should only be used for a controlled teaching demonstration. Never collect real payments, credentials, or attendee personal information.
