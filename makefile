.PHONY: build-dev build-prod build-alpine scan-security

# Build commands for different environments
build-dev:
	docker build -f Dockerfile.dev -t aks-optimizer:dev .

build-prod:
	docker build -f Dockerfile.prod -t aks-optimizer:prod .

build-alpine:
	docker build -f Dockerfile.alpine -t aks-optimizer:alpine .

build-all: build-dev build-prod build-alpine

# Run commands for different environments
run-dev:
	DOCKERFILE=Dockerfile.dev docker-compose up

run-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

run-alpine:
	DOCKERFILE=Dockerfile.alpine IMAGE_TAG=alpine docker-compose up

# Security scanning
scan-security:
	@chmod +x scan-security.sh
	@./scan-security.sh

scan-prod:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image aks-optimizer:prod

# Update base images to latest secure versions
update-base:
	docker pull python:3.9.18-slim-bookworm
	docker pull python:3.9.18-alpine3.19
	docker pull python:3.9.18

# Clean everything
clean-all:
	docker-compose down -v
	docker rmi aks-optimizer:dev aks-optimizer:prod aks-optimizer:alpine
	docker system prune -f