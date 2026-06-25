# Bolão da Copa 2026

> Produção: veja [`deploy/production.md`](deploy/production.md) para hospedar em um VPS com HTTPS automático.

Aplicação privada de palpites para a Copa do Mundo de 2026, com Django Admin,
API REST, React e sincronização automática dos jogos.

## Subir com Docker

1. Copie `.env.example` para `.env` e troque as senhas e a chave do Django.
2. Crie uma chave gratuita em [football-data.org](https://www.football-data.org/)
   e preencha `FOOTBALL_DATA_API_TOKEN`.
3. Execute:

```bash
docker compose up --build -d
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py sync_world_cup
```

A aplicação fica em `http://localhost:8080` e o Admin em
`http://localhost:8080/admin/`.

## Primeiro uso

1. Entre no Admin.
2. Confira as regras em **Regras de pontuação**.
3. Em **Convites**, clique em **Emitir convite** e envie o link por WhatsApp.
4. Em **Ajustes de pontuação**, use **Importar CSV** para trazer o saldo atual.

O CSV deve usar o formato:

```csv
nome,email,pontos
Ana,ana@example.com,25
Bruno,bruno@example.com,18
```

Reimportar o mesmo e-mail atualiza o saldo inicial, sem criar pontuação duplicada.

## Desenvolvimento local

Backend:

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Testes

```bash
docker compose run --rm backend pytest
cd frontend
npm test
npm run build
```

O teste ponta a ponta usa uma aplicação já disponível em
`http://localhost:8080`:

```bash
npm run test:e2e
```

## Operação

- `python manage.py sync_world_cup`: sincroniza agenda e resultados.
- `python manage.py recalculate_points`: recalcula todos os palpites.
- O serviço `scheduler` executa a sincronização a cada dez minutos.
- Uma partida marcada como **ajuste manual** não é alterada pelo provedor.
- Em mata-mata, a pontuação ignora a disputa de pênaltis.
