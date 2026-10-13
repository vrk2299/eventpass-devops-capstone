#!/bin/bash
set -euxo pipefail
dnf update -y
dnf install -y docker
systemctl enable --now docker
usermod -aG docker ec2-user
mkdir -p /opt/eventpass/data
chown -R ec2-user:ec2-user /opt/eventpass
