# Deploy em Ubuntu

Este projeto roda como um app Flask servido pelo Gunicorn e mantido pelo systemd.

## Instalacao inicial

No servidor Ubuntu:

```bash
git clone -b Prod <URL_DO_REPOSITORIO> balancete
cd balancete
chmod +x install_ubuntu.sh
./install_ubuntu.sh
```

Por padrao o servico usa a porta `8091`, escolhida para evitar conflito com as portas ja usadas no servidor.

Para usar outra porta:

```bash
APP_PORT=8092 ./install_ubuntu.sh
```

Depois da instalacao, acesse:

```text
http://IP_DO_SERVIDOR:8091
```

Se a VPS tiver firewall no painel do provedor, libere a porta escolhida em TCP.

## Atualizar o codigo

```bash
cd balancete
git pull
./install_ubuntu.sh
```

## Comandos uteis

```bash
sudo systemctl status balancete
sudo journalctl -u balancete -f
sudo systemctl restart balancete
```

## Arquivos gerados

O app grava uploads temporarios em `uploads/` e resultados em `data/`.
