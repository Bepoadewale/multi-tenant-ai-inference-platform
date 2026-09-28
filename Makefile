.PHONY: install test lint audit run demo load-test bootstrap-local smoke status demo-local demo-overload demo-routing demo-failure demo-timeout demo-metering demo-observability demo-recovery demo-model-registry demo-release-control demo-capacity demo-operational-evidence verify clean-local destroy-local helm-lint terraform-validate
PYTHON ?= python3.12
VENV := .venv
PY := $(VENV)/bin/python

install:
	command -v $(PYTHON) >/dev/null || { echo "Python 3.12 is required; install it with brew install python@3.12"; exit 1; }
	@if [ -x "$(PY)" ] && ! $(PY) -c 'import sys; assert sys.version_info[:2] == (3, 12)' >/dev/null 2>&1; then \
		echo "Recreating project-local virtual environment with Python 3.12"; rm -rf $(VENV); \
	fi
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e '.[dev]'
	$(PY) scripts/create_model.py --output models/tiny-intent-classifier.onnx
	$(PY) scripts/create_model.py --output models/tiny-intent-classifier-v2.onnx --candidate
test:
	PYTHONPATH=gateway/src $(PY) -m pytest -q
lint:
	$(PY) -m ruff check gateway/src gateway/tests benchmarks scripts
audit:
	@for attempt in 1 2 3; do \
		$(PY) -m pip_audit -s osv --skip-editable && exit 0; \
		if [ "$$attempt" -eq 3 ]; then exit 1; fi; \
		echo "pip-audit registry request failed; retrying ($$attempt/3)"; sleep 5; \
	done
run:
	PYTHONPATH=gateway/src $(VENV)/bin/uvicorn inference_gateway.api.main:app --port 8080 --reload
demo:
	PYTHONPATH=gateway/src $(PY) examples/demo.py
load-test:
	PYTHONPATH=gateway/src $(PY) benchmarks/load_test.py
bootstrap-local:
	./scripts/bootstrap-local.sh
smoke:
	./scripts/smoke.sh
status:
	./scripts/status.sh
demo-local:
	./scripts/demo-local.sh
demo-overload:
	./scripts/demo-overload.sh
demo-routing:
	./scripts/demo-routing.sh
demo-failure:
	./scripts/demo-backend-failure.sh
demo-timeout:
	./scripts/demo-timeout.sh
demo-metering:
	./scripts/demo-metering.sh
demo-observability:
	./scripts/demo-observability.sh
demo-recovery:
	./scripts/demo-recovery.sh
demo-model-registry:
	./scripts/demo-model-registry.sh
demo-release-control:
	./scripts/demo-release-control.sh
demo-capacity:
	./scripts/demo-capacity.sh
demo-operational-evidence:
	./scripts/demo-operational-evidence.sh
verify:
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) audit
	docker compose config --quiet
clean-local:
	./scripts/clean-local.sh
destroy-local:
	kind delete cluster --name inference-platform-local
helm-lint:
	helm lint platform/helm/inference-platform
terraform-validate:
	terraform -chdir=infrastructure/terraform/environments/aws init -backend=false
	terraform -chdir=infrastructure/terraform/environments/aws validate
