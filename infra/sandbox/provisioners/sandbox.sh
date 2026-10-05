#!/usr/bin/env bash
# Idempotent sandbox provisioning: Docker Engine (official repo, key fingerprint verified) + act.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

DOCKER_KEY_FPR="9DC858229FC7DD38854AE2D88D81803C0EBFCD88"
ACT_VERSION="v0.2.89"

hostnamectl set-hostname sandbox
apt-get update -y
apt-get install -y ca-certificates curl gnupg git

# --- Docker Engine -----------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /tmp/docker.asc
  # Refuse to continue if the downloaded key is not Docker's published key.
  gpg --show-keys --with-colons /tmp/docker.asc | grep -q "^fpr:::::::::${DOCKER_KEY_FPR}:" \
    || { echo "Docker GPG key fingerprint mismatch" >&2; exit 1; }
  install -m 0644 /tmp/docker.asc /etc/apt/keyrings/docker.asc
  rm -f /tmp/docker.asc

  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
usermod -aG docker vagrant
systemctl enable --now docker

# --- act (run GitHub Actions locally), pinned and checksum-verified ------------
if ! command -v act >/dev/null 2>&1; then
  arch="$(uname -m)"   # x86_64 | aarch64 -> arm64
  [ "$arch" = "aarch64" ] && arch="arm64"
  tmp="$(mktemp -d)"
  tarball="act_Linux_${arch}.tar.gz"
  base="https://github.com/nektos/act/releases/download/${ACT_VERSION}"
  curl -fsSL "${base}/${tarball}" -o "${tmp}/${tarball}"
  curl -fsSL "${base}/checksums.txt" -o "${tmp}/checksums.txt"
  (cd "$tmp" && grep " ${tarball}\$" checksums.txt | sha256sum -c -)
  tar xf "${tmp}/${tarball}" -C /usr/local/bin act
  rm -rf "$tmp"
fi
act --version

echo "Sandbox ready. Repo is at /home/vagrant/resume-review"
