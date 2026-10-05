# Sandbox VM

Local Vagrant (VirtualBox) VM with Docker and `act` for trying the stack and the CI workflows.

```bash
cd infra/sandbox
vagrant up
vagrant ssh
cd ~/resume-review/deployments/docker && docker compose up --build   # once deployments/docker exists
```

The repository root is synced to `/home/vagrant/resume-review`. Ports 8000/8001 are forwarded to
`127.0.0.1` only. Provisioning verifies Docker's apt key fingerprint and the sha256 of the `act` download.
