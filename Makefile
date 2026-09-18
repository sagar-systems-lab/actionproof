.PHONY: verify-phase1 frontend-build backend-test

frontend-build:
	cd frontend && npm install --no-audit --no-fund && npm run build

backend-test:
	cd backend && python -m pytest -q

verify-phase1: frontend-build backend-test
