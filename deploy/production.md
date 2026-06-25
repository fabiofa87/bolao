# Hospedagem em Producao

Este projeto ja sobe como um conjunto Docker Compose. A opcao mais simples e
barata para o bolao e um VPS com Ubuntu, Docker e um dominio apontando para o
IP do servidor.

## Plataforma recomendada

Use um VPS de 1 GB RAM. O plano basico de 1 GB da DigitalOcean custa cerca de
US$ 6/mes e e suficiente para um bolao pequeno com PostgreSQL, Django, React e
o scheduler. O plano de 512 MB existe, mas fica apertado para build Docker e
PostgreSQL no mesmo servidor.

Render tambem funciona bem, mas exigiria separar servicos e adaptar deploy;
para este projeto, o VPS preserva o `compose.yaml` atual quase sem mudancas.

## 1. Criar o servidor

1. Crie um Droplet/VPS Ubuntu 24.04 LTS com 1 GB RAM.
2. Configure uma chave SSH.
3. Aponte um registro DNS `A` do seu dominio para o IP do servidor, por exemplo:

```text
bolao.seudominio.com -> 203.0.113.10
```

## 2. Preparar o Ubuntu

Conecte por SSH:

```bash
ssh root@IP_DO_SERVIDOR
```

Instale Docker:

```bash
apt update
apt install -y ca-certificates curl git ufw
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Abra apenas SSH, HTTP e HTTPS:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 3. Baixar o projeto

```bash
mkdir -p /opt/bolao
git clone https://github.com/fabiofa87/bolao.git /opt/bolao
cd /opt/bolao
```

## 4. Configurar variaveis

Crie o `.env` de producao:

```bash
cp .env.production.example .env
nano .env
```

Troque pelo seu dominio real:

```text
DOMAIN=bolao.seudominio.com
DJANGO_ALLOWED_HOSTS=bolao.seudominio.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://bolao.seudominio.com
FRONTEND_URL=https://bolao.seudominio.com
```

Gere uma chave segura:

```bash
openssl rand -base64 48
```

Preencha tambem `POSTGRES_PASSWORD` e `FOOTBALL_DATA_API_TOKEN`.

## 5. Subir a aplicacao

```bash
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
docker compose -f compose.yaml -f compose.prod.yaml exec backend python manage.py createsuperuser
docker compose -f compose.yaml -f compose.prod.yaml exec backend python manage.py sync_world_cup
```

Acesse:

```text
https://bolao.seudominio.com
https://bolao.seudominio.com/admin/
```

Caddy emitira o certificado TLS automaticamente.

## Atualizacoes

No servidor:

```bash
cd /opt/bolao
git pull
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
docker compose -f compose.yaml -f compose.prod.yaml exec backend python manage.py migrate
```

## Backup basico

Faca um dump do banco:

```bash
docker compose -f compose.yaml -f compose.prod.yaml exec db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > bolao-$(date +%F).sql
```

Copie esse arquivo para fora do servidor periodicamente.

