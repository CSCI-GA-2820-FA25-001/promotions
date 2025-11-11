# These can be overridden with env vars.
K8S_DEPLOYMENT ?= k8s/deployment.yaml
DEFAULT_DEPLOYMENT_IMAGE := $(strip $(shell python3 -c "from pathlib import Path; text = Path('$(K8S_DEPLOYMENT)').read_text().splitlines() if Path('$(K8S_DEPLOYMENT)').exists() else []; print(next((line.split(':',1)[1].strip() for line in text if line.strip().startswith('image:')), ''), end='')" 2>/dev/null))
DEFAULT_REGISTRY := cluster-registry:5000
DEFAULT_IMAGE_NAME := promotions
DEFAULT_IMAGE_TAG := 1.0

ifneq ($(DEFAULT_DEPLOYMENT_IMAGE),)
DEFAULT_REGISTRY := $(firstword $(subst /, ,$(DEFAULT_DEPLOYMENT_IMAGE)))
DEFAULT_REPOSITORY := $(word 2,$(subst /, ,$(DEFAULT_DEPLOYMENT_IMAGE)))
DEFAULT_IMAGE_NAME := $(firstword $(subst :, ,$(DEFAULT_REPOSITORY)))
DEFAULT_IMAGE_TAG := $(word 2,$(subst :, ,$(DEFAULT_REPOSITORY)))
endif

REGISTRY ?= $(DEFAULT_REGISTRY)
IMAGE_NAME ?= $(DEFAULT_IMAGE_NAME)
IMAGE_TAG ?= $(if $(DEFAULT_IMAGE_TAG),$(DEFAULT_IMAGE_TAG),1.0)
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
REGISTRY_HOST := $(firstword $(subst :, ,$(REGISTRY)))
REGISTRY_PORT_RAW := $(word 2,$(subst :, ,$(REGISTRY)))
REGISTRY_PORT := $(if $(REGISTRY_PORT_RAW),$(REGISTRY_PORT_RAW),5000)
PLATFORM ?= "linux/amd64,linux/arm64"
CLUSTER ?= nyu-devops

.SILENT:

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: all
all: help

##@ Development

.PHONY: clean
clean:	## Removes all dangling build cache
	$(info Removing all dangling build cache..)
	-docker rmi $(IMAGE)
	docker image prune -f
	docker buildx prune -f

.PHONY: install
install: ## Install Python dependencies
	$(info Installing dependencies...)
	sudo pipenv install --system --dev

.PHONY: lint
lint: ## Run the linter
	$(info Running linting...)
	-flake8 service tests --count --select=E9,F63,F7,F82 --show-source --statistics
	-flake8 service tests --count --max-complexity=10 --max-line-length=127 --statistics
	-pylint service tests --max-line-length=127

.PHONY: test
test: ## Run the unit tests
	$(info Running tests...)
	export RETRY_COUNT=1; pytest --pspec --cov=service --cov-fail-under=95 --disable-warnings

.PHONY: run
run: ## Run the service
	$(info Starting service...)
	honcho start

.PHONY: secret
secret: ## Generate a secret hex key
	$(info Generating a new secret key...)
	python3 -c 'import secrets; print(secrets.token_hex())'

##@ Kubernetes

.PHONY: cluster
cluster: ## Create a K3D Kubernetes cluster with load balancer and registry
	$(info Creating Kubernetes cluster $(CLUSTER) with a registry and 2 worker nodes...)
	k3d cluster create $(CLUSTER) --agents 2 --registry-create $(REGISTRY_HOST):0.0.0.0:$(REGISTRY_PORT) --port '8080:80@loadbalancer'

.PHONY: cluster-rm
cluster-rm: ## Remove a K3D Kubernetes cluster
	$(info Removing Kubernetes cluster...)
	k3d cluster delete $(CLUSTER)

.PHONY: deploy
deploy: ## Deploy the service on local Kubernetes
	$(info Deploying service locally with image $(IMAGE)...)
	kubectl apply -R -f k8s/
	kubectl set image deployment/promotions promotions=$(IMAGE)

.PHONY: verify
verify: ## Verify the deployment and test the health endpoint
	$(info Verifying deployment...)
	kubectl get ingress
	@echo "\n=== Checking Pods ==="
	kubectl get pods
	@echo "\n=== Testing Health Endpoint ==="
	@echo "Testing: curl -H 'Host: promotions.localdev.me' http://localhost:8080/health"
	@curl -s -H "Host: promotions.localdev.me" http://localhost:8080/health | python3 -m json.tool || echo "Health check failed"
	@echo "\n=== Verification Complete ==="

############################################################
# COMMANDS FOR BUILDING THE IMAGE
############################################################

##@ Image Build and Push

.PHONY: init
init: export DOCKER_BUILDKIT=1
init:	## Creates the buildx instance
	$(info Initializing Builder...)
	-docker buildx create --use --name=qemu
	docker buildx inspect --bootstrap

.PHONY: build
build:	## Build the project container image for local platform
	$(info Building $(IMAGE)...)
	docker build --rm --pull -f Dockerfile --tag $(IMAGE) .

.PHONY: push
push:	## Push the image to the container registry
	$(info Pushing $(IMAGE)...)
	docker push $(IMAGE)

.PHONY: buildx
buildx:	## Build multi-platform image with buildx
	$(info Building multi-platform image $(IMAGE) for $(PLATFORM)...)
	docker buildx build --file Dockerfile --pull --platform=$(PLATFORM) --tag $(IMAGE) --push .

.PHONY: remove
remove:	## Stop and remove the buildx builder
	$(info Stopping and removing the builder image...)
	docker buildx stop
	docker buildx rm
