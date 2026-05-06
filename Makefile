# VeloBid Makefile
# Quick commands for the multi-tenant Hermes stack.

# ─── Stack Management ───────────────────────────────────────────

.PHONY: up down restart ps logs

up:      ## Start all services
	docker compose up -d

down:    ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

ps:      ## Show container status
	docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

logs:    ## Tail logs from both containers
	docker compose logs --tail=50 -f

# ─── Build ───────────────────────────────────────────────────────

.PHONY: build build-velobid build-hermes

build: build-velobid build-hermes  ## Rebuild all images

build-velobid:
	docker compose build velobid
	docker compose up -d velobid

build-hermes:
	docker compose build hermes
	docker compose rm -sf hermes
	docker compose create hermes
	docker compose start hermes

# ─── Frontend ────────────────────────────────────────────────────

.PHONY: frontend-build frontend-deploy

frontend-build:  ## Build React frontend
	cd frontend && npm run build

frontend-deploy: frontend-build  ## Build + deploy frontend to container
	rm -f api/static/assets/index-*.js api/static/assets/index-*.css
	cp frontend/dist/assets/* api/static/assets/
	cp frontend/dist/index.html api/static/
	docker compose restart velobid

# ─── Profiles ────────────────────────────────────────────────────

.PHONY: profile-create profile-list profile-soul

profile-create:  ## Create a bidder profile (id= name= trades=)
	@[ "$(id)" ] && [ "$(name)" ] || (echo "Usage: make profile-create id=acme_hvac name='Acme HVAC' trades='hvac,sheet_metal'" && exit 1)
	curl -s -X POST http://localhost:8000/api/v1/admin/bidders/$(id)/profile \
		-H "Content-Type: application/json" \
		-d '{"company_name":"$(name)","trades":["$(subst $(comma),","$(trades))"]}'

profile-list:  ## List profiles inside Hermes container
	docker exec hermes ls /root/.hermes/profiles/

profile-soul:  ## Show profile SOUL.md (id=)
	@[ "$(id)" ] || (echo "Usage: make profile-soul id=acme_hvac" && exit 1)
	docker exec hermes cat /root/.hermes/profiles/bidder-$(id)/SOUL.md

# ─── Health ──────────────────────────────────────────────────────

.PHONY: health health-hermes

health: health-velobid health-hermes  ## Check all health endpoints

health-velobid:
	@curl -s -o /dev/null -w "VeloBid: HTTP %{http_code}\n" http://localhost:8000/api/v1/meta

health-hermes:
	@curl -s -o /dev/null -w "Hermes:  HTTP %{http_code}\n" \
		-H "Authorization: Bearer velobid-internal" http://localhost:8644/v1/models
	@docker exec hermes curl -s -o /dev/null -w "Admin:   HTTP %{http_code}\n" http://127.0.0.1:8640/admin/health

# ─── Test ────────────────────────────────────────────────────────

.PHONY: test

test:  ## End-to-end smoke test
	@echo "=== VeloBid Smoke Test ==="
	@echo "1. Health check..."
	curl -s -o /dev/null -w "   HTTP %{http_code}\n" http://localhost:8000/api/v1/meta
	@echo "2. Hermes API..."
	curl -s -o /dev/null -w "   HTTP %{http_code}\n" \
		-H "Authorization: Bearer velobid-internal" http://localhost:8644/v1/models
	@echo "3. Admin server..."
	curl -s http://localhost:8644/admin/health
	@echo ""
	@echo "4. Chat echo test..."
	curl -s --max-time 30 -X POST http://localhost:8000/api/v1/agent/hermes-chat \
		-H "Content-Type: application/json" \
		-d '{"messages":[{"role":"user","content":"Say only: OK"}],"bidder_id":"acme_hvac"}' \
		| grep -o '"content":"[^"]*"' | tr -d '\n'
	@echo ""
	@echo "=== Done ==="

# ─── K8s ─────────────────────────────────────────────────────────

.PHONY: k8s-apply k8s-delete

k8s-apply:  ## Deploy manifests to k3s (requires cluster)
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/config.yaml
	kubectl apply -f k8s/storage.yaml
	kubectl apply -f k8s/velobid.yaml
	kubectl apply -f k8s/hermes.yaml
	kubectl apply -f k8s/ingress.yaml

k8s-delete:  ## Remove K8s deployment
	kubectl delete -f k8s/

# ─── Utility ─────────────────────────────────────────────────────

.PHONY: clean data-size

clean:  ## Prune unused Docker images
	docker image prune -f
	docker builder prune -f

data-size:  ## Show shared volume usage
	@echo "Shared volume:"
	docker run --rm -v shared_data:/data alpine du -sh /data 2>/dev/null || echo "  (not accessible)"
	@echo "Hermes data:"
	docker run --rm -v hermes_data:/data alpine du -sh /data 2>/dev/null || echo "  (not accessible)"
