#!/usr/bin/env bash
# Genera (una sola vez) el par de llaves SIN passphrase en el volumen compartido /keys,
# las instala para el usuario hadoop y arranca sshd. Nada secreto queda en la imagen.
set -euo pipefail

ssh-keygen -A >/dev/null                      # llaves de host de sshd

if [ ! -f /keys/id_ed25519 ]; then
  ssh-keygen -t ed25519 -N "" -C "hadoop@datamart" -f /keys/id_ed25519 -q
fi
chown hadoop:hadoop /keys/id_ed25519 /keys/id_ed25519.pub
chmod 600 /keys/id_ed25519
chmod 644 /keys/id_ed25519.pub

SSH_DIR=/home/hadoop/.ssh
install -d -m 700 -o hadoop -g hadoop "$SSH_DIR"
install -m 600 -o hadoop -g hadoop /keys/id_ed25519      "$SSH_DIR/id_ed25519"
install -m 644 -o hadoop -g hadoop /keys/id_ed25519.pub  "$SSH_DIR/id_ed25519.pub"
install -m 600 -o hadoop -g hadoop /keys/id_ed25519.pub  "$SSH_DIR/authorized_keys"
printf 'Host *\n  StrictHostKeyChecking accept-new\n' | install -m 600 -o hadoop -g hadoop /dev/stdin "$SSH_DIR/config"

exec "$@"
