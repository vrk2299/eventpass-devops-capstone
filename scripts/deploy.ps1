param(
    [Parameter(Mandatory=$true)][string]$HostIp,
    [Parameter(Mandatory=$true)][string]$KeyPath
)
$ErrorActionPreference = 'Stop'
$KeyPath = (Resolve-Path -LiteralPath $KeyPath).Path
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$remote = "ec2-user@$HostIp"
Write-Host 'Copying the app to the EC2 instance...'
scp -i $KeyPath -o StrictHostKeyChecking=accept-new -r (Join-Path $repo 'app') (Join-Path $repo 'Dockerfile') "${remote}:/opt/eventpass/"
ssh -i $KeyPath -o StrictHostKeyChecking=accept-new $remote 'sudo chown -R 1000:1000 /opt/eventpass/data && sudo docker build -t eventpass:classroom /opt/eventpass && (sudo docker rm -f eventpass 2>/dev/null || true) && sudo docker run -d --name eventpass --restart unless-stopped -p 80:8000 -v /opt/eventpass/data:/data eventpass:classroom'
Write-Host "Deployment command finished. Open http://$HostIp and allow a few minutes for the app to start."
