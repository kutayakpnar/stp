# STP Banking System - Docker Operations
.PHONY: help build up down logs clean restart shell test

# Default target
help: ## Show this help message
	@echo "STP Banking System - Docker Operations"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	@echo "🔨 Building Docker images..."
	docker-compose build --no-cache

up: ## Start all services
	@echo "🚀 Starting STP Banking System..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "📱 Frontend: http://localhost:3000"
	@echo "📚 Backend API: http://localhost:8000"
	@echo "📖 API Docs: http://localhost:8000/docs"

down: ## Stop all services
	@echo "⏹️  Stopping STP Banking System..."
	docker-compose down

restart: ## Restart all services
	@echo "🔄 Restarting STP Banking System..."
	docker-compose restart

logs: ## Show logs for all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-db: ## Show database logs
	docker-compose logs -f postgres

shell-backend: ## Access backend shell
	docker-compose exec backend bash

shell-frontend: ## Access frontend shell
	docker-compose exec frontend sh

shell-db: ## Access database shell
	docker-compose exec postgres psql -U postgres -d postgres

test: ## Run tests
	@echo "🧪 Running tests..."
	docker-compose exec backend python -m pytest

clean: ## Clean up Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

dev-setup: ## Setup development environment
	@echo "🛠️  Setting up development environment..."
	cp .env.example .env
	@echo "📝 Please edit .env file with your OpenAI API key"
	@echo "🔑 OPENAI_API_KEY=your-api-key-here"

prod-up: ## Start production services with nginx
	@echo "🏭 Starting production environment..."
	docker-compose --profile production up -d

backup-db: ## Backup database
	@echo "💾 Creating database backup..."
	docker-compose exec postgres pg_dump -U postgres postgres > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database (usage: make restore-db BACKUP=backup_file.sql)
	@echo "📥 Restoring database from $(BACKUP)..."
	docker-compose exec -T postgres psql -U postgres -d postgres < $(BACKUP)

status: ## Show service status
	@echo "📊 Service Status:"
	@echo "=================="
	docker-compose ps

health: ## Check service health
	@echo "❤️  Health Check:"
	@echo "================="
	@curl -s http://localhost:3000/health && echo " ✅ Frontend"
	@curl -s http://localhost:8000/health && echo " ✅ Backend" 