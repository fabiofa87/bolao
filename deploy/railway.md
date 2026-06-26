# Deploy no Railway

Este projeto pode rodar no Railway com quatro servicos:

- `Postgres`
- `bolao-backend`
- `bolao-worker`
- `bolao` ou `bolao-frontend`

## Importante

Voce colou tokens e senhas no chat. Rotacione estes valores no Railway:

- `FOOTBALL_DATA_API_TOKEN`
- `POSTGRES_PASSWORD`
- `DJANGO_SECRET_KEY`

## Backend

Use o root directory `backend` ou a Dockerfile `backend/Dockerfile`.

Variaveis:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
DJANGO_SECRET_KEY=<gere uma chave longa nova>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=bolao-production-aef5.up.railway.app,bolao-production-a245.up.railway.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://bolao-production-aef5.up.railway.app,https://bolao-production-a245.up.railway.app
DJANGO_SECURE_COOKIES=1
DJANGO_SESSION_COOKIE_SAMESITE=None
DJANGO_CSRF_COOKIE_SAMESITE=None
DJANGO_SECURE_SSL_REDIRECT=0
DJANGO_SECURE_HSTS_SECONDS=0
FRONTEND_URL=https://bolao-production-aef5.up.railway.app
FOOTBALL_DATA_API_TOKEN=<token novo>
```

O frontend chama a API por `/api`, no mesmo dominio publico do site, e o Nginx
encaminha internamente para o backend. Assim o cookie de sessao fica como
first-party para o navegador, o que evita falhas em Safari/iPhone, Androids com
protecao de rastreamento e navegadores embutidos em apps.
O app tambem tem fallback automatico para chamar o backend direto se `/api`
falhar por erro de rede; por isso, mantenha os cookies com `SameSite=None`
enquanto esse fallback estiver ativo.

Start command:

```text
deixe vazio
```

A Dockerfile do backend executa `start.sh`, que roda migrations,
`collectstatic` e depois mantem o Gunicorn online na porta `$PORT`.

Se voce definir um start command manual no Railway, use exatamente:

```bash
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60
```

Se o servico aparecer como `Completed`, ele esta terminando em vez de ficar
online. Nesse caso, remova o start command customizado ou use o comando acima.

Checklist do backend:

```text
Root Directory: backend
Dockerfile: backend/Dockerfile
Start Command: vazio
Public Networking: ligado
```

## Frontend

Use o root directory `frontend` ou a Dockerfile `frontend/Dockerfile`.

Variaveis:

```text
BACKEND_SCHEME=https
BACKEND_URL=bolao-production-a245.up.railway.app
FORWARDED_PROTO=https
```

Atencao: a variavel correta e `BACKEND_SCHEME`, nao `BACKEND_SCHEMA`.
Nao cadastre `PORT` manualmente no Railway; a plataforma injeta essa variavel.
Nao coloque aspas nos valores das variaveis.

O frontend tambem gera `/config.js` em runtime. Com as variaveis acima, o React
chama a API pelo proprio dominio do frontend:

```text
https://bolao-production-aef5.up.railway.app/api
```

O `BACKEND_URL` continua sendo usado pelo Nginx para encaminhar `/api/`,
`/admin/` e `/static/` ao backend. Nao defina `API_BASE_URL` no Railway, a menos
que voce queira forcar propositalmente outro dominio de API.
No proxy, o Nginx envia `Host: BACKEND_URL` para o Railway rotear a requisicao
ao servico correto, mas preserva o dominio publico original em
`X-Forwarded-Host`.

Com essas variaveis, o Nginx do frontend encaminha:

- `/api/` para o backend
- `/admin/` redireciona para o Django Admin no backend
- `/static/` para os arquivos estaticos do Django Admin

Checklist do frontend:

```text
Root Directory: frontend
Dockerfile: frontend/Dockerfile
Public Networking: ligado
BACKEND_SCHEME=https
BACKEND_URL=<dominio publico do backend, sem https://>
FORWARDED_PROTO=https
```

## Worker

Use o mesmo servico/build do backend, mas com start command:

```bash
python manage.py run_scheduler
```

Variaveis:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
DJANGO_SECRET_KEY=<mesma chave do backend>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=bolao-production-aef5.up.railway.app,bolao-production-a245.up.railway.app
FOOTBALL_DATA_API_TOKEN=<token novo>
```

Checklist do worker:

```text
Root Directory: backend
Dockerfile: backend/Dockerfile
Start Command: python manage.py run_scheduler
Public Networking: desligado
```

## Acesso

Depois do deploy, acesse:

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
