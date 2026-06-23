#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="${APP_NAME:-balancete}"
APP_PORT="${APP_PORT:-8091}"
APP_HOST="${APP_HOST:-0.0.0.0}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_USER="${SERVICE_USER:-${SUDO_USER:-$(id -un)}}"
SERVICE_GROUP="$(id -gn "$SERVICE_USER")"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Este instalador foi feito para Ubuntu/Linux."
  exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "apt-get nao encontrado. Rode este instalador em Ubuntu/Debian."
  exit 1
fi

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

echo "==> Instalando pacotes do sistema"
$SUDO apt-get update
$SUDO apt-get install -y python3 python3-venv python3-pip python3-dev build-essential

echo "==> Verificando porta ${APP_PORT}"
if command -v ss >/dev/null 2>&1 && ss -ltn "( sport = :${APP_PORT} )" | grep -q ":${APP_PORT}"; then
  echo "A porta ${APP_PORT} ja esta em uso. Rode novamente com outra porta, por exemplo:"
  echo "APP_PORT=8092 ./install_ubuntu.sh"
  exit 1
fi

echo "==> Criando pastas de trabalho"
mkdir -p "${APP_DIR}/data" "${APP_DIR}/uploads" "${APP_DIR}/logs"

if [[ ! -f "${APP_DIR}/.env" ]]; then
  echo "==> Criando .env"
  if command -v openssl >/dev/null 2>&1; then
    SECRET_KEY="$(openssl rand -hex 32)"
  else
    SECRET_KEY="$(date +%s%N | sha256sum | awk '{print $1}')"
  fi
  cat > "${APP_DIR}/.env" <<EOF
FLASK_DEBUG=0
APP_HOST=${APP_HOST}
APP_PORT=${APP_PORT}
MAX_CONTENT_LENGTH=33554432
SECRET_KEY=${SECRET_KEY}
EOF
fi

echo "==> Criando ambiente virtual"
python3 -m venv "${APP_DIR}/venv"
"${APP_DIR}/venv/bin/python" -m pip install --upgrade pip wheel
"${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo "==> Ajustando permissoes"
$SUDO chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${APP_DIR}/data" "${APP_DIR}/uploads" "${APP_DIR}/logs" "${APP_DIR}/venv"
if [[ -f "${APP_DIR}/.env" ]]; then
  $SUDO chown "${SERVICE_USER}:${SERVICE_GROUP}" "${APP_DIR}/.env"
  chmod 600 "${APP_DIR}/.env"
fi

echo "==> Criando servico systemd: ${APP_NAME}"
$SUDO tee "${SERVICE_FILE}" >/dev/null <<EOF
[Unit]
Description=Balancete Flask app
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${APP_DIR}
EnvironmentFile=-${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers ${GUNICORN_WORKERS} --bind ${APP_HOST}:${APP_PORT} --timeout 120 --access-logfile ${APP_DIR}/logs/access.log --error-logfile ${APP_DIR}/logs/error.log app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "==> Ativando servico"
$SUDO systemctl daemon-reload
$SUDO systemctl enable "${APP_NAME}"
$SUDO systemctl restart "${APP_NAME}"

if command -v ufw >/dev/null 2>&1 && $SUDO ufw status | grep -qi "Status: active"; then
  echo "==> Liberando porta ${APP_PORT} no UFW"
  $SUDO ufw allow "${APP_PORT}/tcp"
fi

echo
echo "Instalacao concluida."
echo "Servico: ${APP_NAME}"
echo "Diretorio: ${APP_DIR}"
echo "Porta: ${APP_PORT}"
echo
echo "Comandos uteis:"
echo "  sudo systemctl status ${APP_NAME}"
echo "  sudo journalctl -u ${APP_NAME} -f"
echo "  sudo systemctl restart ${APP_NAME}"
echo
echo "Acesse: http://IP_DO_SERVIDOR:${APP_PORT}"
echo "Se a VPS tiver firewall/painel externo, libere a porta ${APP_PORT}/tcp nele tambem."
