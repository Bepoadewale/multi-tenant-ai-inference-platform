.PHONY: install test lint run demo load-test bootstrap-local destroy-local helm-lint terraform-validate
install:
	python3 -m pip install -e '.[dev]'
test:
	PYTHONPATH=gateway/src python3 -m pytest -q
lint:
	python3 -m ruff check gateway/src gateway/tests benchmarks
run:
	PYTHONPATH=gateway/src uvicorn inference_gateway.api.main:app --port 8080 --reload
demo:
	PYTHONPATH=gateway/src python3 examples/demo.py
load-test:
	PYTHONPATH=gateway/src python3 benchmarks/load_test.py
bootstrap-local:
	./scripts/bootstrap-local.sh
destroy-local:
	kind delete cluster --name inference-platform-local
helm-lint:
	helm lint platform/helm/inference-platform
terraform-validate:
	terraform -chdir=infrastructure/terraform/environments/aws init -backend=false
	terraform -chdir=infrastructure/terraform/environments/aws validate
