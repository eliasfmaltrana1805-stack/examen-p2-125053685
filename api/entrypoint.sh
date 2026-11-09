#!/bin/sh
# Prepara el cliente SSH del contenedor api para entrar a hadoop sin contrasena.
set -e
mkdir -p /root/.ssh && chmod 700 /root/.ssh
if [ -f /keys/id_ed25519 ]; then
  cp /keys/id_ed25519 /root/.ssh/id_ed25519 && chmod 600 /root/.ssh/id_ed25519
  printf 'Host hadoop\n  User hadoop\n  IdentityFile /root/.ssh/id_ed25519\n  StrictHostKeyChecking accept-new\n  UserKnownHostsFile /dev/null\n  LogLevel ERROR\n' > /root/.ssh/config
  chmod 600 /root/.ssh/config
fi
exec "$@"
