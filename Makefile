.PHONY: up down logs seed test migrate backend frontend fresh

up:
	docker compose up --build

down:
	docker compose down

fresh:
	docker compose down -v && docker compose up --build

logs:
	docker compose logs -f backend

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m scripts.seed

test:
	docker compose exec backend pytest -q

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev
