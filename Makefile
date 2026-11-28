.PHONY: install test lint audit run demo load-test bootstrap-local smoke status public-demo demo-local demo-overload demo-routing demo-failure demo-timeout demo-metering demo-observability demo-recovery demo-model-registry demo-release-control demo-capacity demo-operational-evidence demo-remediation demo-agent-tools demo-self-service demo-edge-adapter demo-sandboxed-agent demo-operator-console demo-flagship verify clean-local destroy-local helm-lint terraform-validate cloud-delivery-validate pilot-guardrails-plan pilot-cloud-plan pilot-cloud-apply pilot-cloud-push-image pilot-cloud-bootstrap-runtime pilot-cloud-smoke pilot-cloud-validate pilot-cloud-destroy container-dependencies-validate container-dependencies-audit gpu-ec2-preflight gpu-ec2-validate gpu-compose-config gpu-observability-validate gpu-benchmark-plan gpu-benchmark gpu-evaluation-plan gpu-cuda-plan gpu-cuda-matmul gpu-cuda-vector-add gpu-release-controller-help gpu-ec2-bootstrap-preview-plan gpu-ec2-preview-plan gpu-ec2-plan gpu-ec2-apply gpu-ec2-destroy-plan gpu-ec2-destroy-apply gpu-ec2-verify-clean
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
	PYTHONPATH=.:gateway/src $(PY) -m pytest -q
lint:
	$(PY) -m ruff check gateway/src gateway/tests benchmarks evaluations scripts
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
public-demo:
	./scripts/start-public-demo.sh
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
demo-remediation:
	./scripts/demo-remediation.sh
demo-agent-tools:
	./scripts/demo-agent-tools.sh
demo-self-service:
	./scripts/demo-self-service.sh
demo-edge-adapter:
	./scripts/demo-edge-adapter.sh
demo-sandboxed-agent:
	./scripts/demo-sandboxed-agent.sh
demo-operator-console:
	./scripts/demo-operator-console.sh
demo-flagship:
	./scripts/demo-flagship.sh
verify:
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) audit
	docker compose config --quiet
	$(MAKE) gpu-compose-config
	$(MAKE) gpu-observability-validate
	$(MAKE) gpu-benchmark-plan
	$(MAKE) gpu-evaluation-plan
	$(MAKE) gpu-cuda-plan
clean-local:
	./scripts/clean-local.sh
destroy-local:
	kind delete cluster --name inference-platform-local
helm-lint:
	helm lint platform/helm/inference-platform
terraform-validate:
	terraform -chdir=infrastructure/terraform/bootstrap init -backend=false
	terraform -chdir=infrastructure/terraform/bootstrap validate
	terraform -chdir=infrastructure/terraform/environments/aws init -backend=false
	terraform -chdir=infrastructure/terraform/environments/aws validate
	terraform -chdir=infrastructure/terraform/environments/gpu-ec2 init -backend=false
	terraform -chdir=infrastructure/terraform/environments/gpu-ec2 validate
cloud-delivery-validate:
	./scripts/validate-cloud-delivery-contracts.sh
pilot-cloud-plan:
	./scripts/pilot-cloud-plan.sh
pilot-guardrails-plan:
	./scripts/pilot-guardrails-plan.sh
pilot-cloud-apply:
	./scripts/pilot-cloud-apply.sh
pilot-cloud-push-image:
	./scripts/pilot-cloud-push-image.sh
pilot-cloud-bootstrap-runtime:
	./scripts/pilot-cloud-bootstrap-runtime.sh
pilot-cloud-smoke:
	./scripts/pilot-cloud-smoke.sh
pilot-cloud-validate:
	./scripts/pilot-cloud-validate.sh
pilot-cloud-destroy:
	./scripts/pilot-cloud-destroy.sh
gpu-ec2-preflight:
	./scripts/gpu-ec2-preflight.sh
container-dependencies-validate:
	$(PYTHON) scripts/verify_container_lock.py
container-dependencies-audit:
	$(PY) -m pip_audit -s osv -r requirements-container.lock
gpu-ec2-validate:
	terraform -chdir=infrastructure/terraform/environments/gpu-ec2 init -backend=false
	terraform -chdir=infrastructure/terraform/environments/gpu-ec2 fmt -check -recursive
	terraform -chdir=infrastructure/terraform/environments/gpu-ec2 validate
gpu-compose-config:
	docker compose --env-file deployments/single-gpu/.env.example -f deployments/single-gpu/compose.yaml config --quiet
gpu-observability-validate:
	./scripts/validate-gpu-observability.sh
gpu-benchmark-plan:
	$(PYTHON) benchmarks/gpu_inference/run_vllm_matrix.py --dry-run
gpu-benchmark:
	$(PYTHON) benchmarks/gpu_inference/run_vllm_matrix.py
gpu-evaluation-plan:
	$(PYTHON) evaluations/gpu_llm/run_evaluation.py --dry-run
gpu-cuda-plan:
	$(PYTHON) benchmarks/cuda_performance/torch_matmul.py --dry-run
gpu-cuda-matmul:
	$(PYTHON) benchmarks/cuda_performance/torch_matmul.py
gpu-cuda-vector-add:
	nvcc -O2 -std=c++17 -lineinfo benchmarks/cuda_performance/vector_add.cu -o /tmp/gpu-lab-vector-add
	/tmp/gpu-lab-vector-add
gpu-release-controller-help:
	$(PY) scripts/gpu_release_controller.py --help
gpu-ec2-bootstrap-preview-plan:
	./scripts/gpu-ec2-bootstrap-preview-plan.sh
gpu-ec2-preview-plan:
	./scripts/gpu-ec2-preview-plan.sh
gpu-ec2-plan:
	./scripts/gpu-ec2-plan.sh
gpu-ec2-apply:
	./scripts/gpu-ec2-apply.sh
gpu-ec2-destroy-plan:
	./scripts/gpu-ec2-destroy-plan.sh
gpu-ec2-destroy-apply:
	./scripts/gpu-ec2-destroy-apply.sh
gpu-ec2-verify-clean:
	./scripts/gpu-ec2-verify-clean.sh
