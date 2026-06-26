# Deploy no Railway

Este projeto pode rodar no Railway com quatro serviços:

- `Postgres`
- `bolao-backend`
- `bolao-worker`
- `bolao` ou `bolao-frontend`

## Importante

Se voce colou tokens ou senhas em chat, rotacione:

- `FOOTBALL_DATA_API_TOKEN`
- `POSTGRES_PASSWORD`
- `DJANGO_SECRET_KEY`

## Backend

Use o diretório raiz `backend` ou a Dockerfile `backend/Dockerfile`.

Variáveis:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
DJANGO_SECRET_KEY=<gere uma chave longa nova>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=bolao-production-aef5.up.railway.app,bolao-production-a245.up.railway.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://bolao-production-aef5.up.railway.app,https://bolao-production-a245.up.railway.app
DJANGO_SECURE_COOKIES=1
DJANGO_SECURE_SSL_REDIRECT=0
DJANGO_SECURE_HSTS_SECONDS=0
FRONTEND_URL=https://bolao-production-aef5.up.railway.app
FOOTBALL_DATA_API_TOKEN=<token novo>
```

Comando de start, se o Railway pedir:

```bash
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60
```

## Frontend

Use o diretório raiz `frontend` ou a Dockerfile `frontend/Dockerfile`.

Variáveis:

```text
PORT=${{PORT}}
BACKEND_SCHEME=https
BACKEND_URL=bolao-production-a245.up.railway.app
FORWARDED_PROTO=https
```

Atencao: a variavel correta e `BACKEND_SCHEME`, nao `BACKEND_SCHEMA`.

Com essas variáveis, o Nginx do frontend encaminha:

- `/api/` para o backend
- `/admin/` para o Django Admin
- `/static/` para os arquivos estaticos do Django Admin

## Worker

Use o mesmo serviço/build do backend, mas com start command:

```bash
python manage.py run_scheduler
```

Variáveis:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
DJANGO_SECRET_KEY=<mesma chave do backend>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=bolao-production-aef5.up.railway.app,bolao-production-a245.up.railway.app
FOOTBALL_DATA_API_TOKEN=<token novo>
```

## Acesso

Depois do deploy:

```text
https://bolao-production-aef5.up.railway.app/
https://bolao-production-aef5.up.railway.app/admin/
```

Se `/admin/` falhar, teste o backend direto:

```text
https://bolao-production-a245.up.railway.app/admin/
```

Se o backend direto abre mas o frontend nao, o problema esta nas variaveis
`BACKEND_SCHEME`, `BACKEND_URL` ou `FORWARDED_PROTO` do frontend.

