#!/usr/bin/env python3
"""Apply an approved LLM release from the single EC2 host, with verified rollback."""

from __future__ import annotations

import argparse
import fcntl
import getpass
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

from evaluations.gpu_llm.release_control import (  # noqa: E402
    ReleaseManifest,
    ReleasePlan,
    ReleaseValidationError,
    assert_not_stale,
    canonical_json,
    create_manifest,
    verify_manifest,
    verify_plan,
)

DEFAULT_COMPOSE_FILE = REPOSITORY / "deployments/single-gpu/compose.yaml"
DEFAULT_ENV_FILE = REPOSITORY / "deployments/single-gpu/.env"
DEFAULT_STATE_FILE = REPOSITORY / ".local/gpu-release/active-release.json"
DEFAULT_API_URL = "http://127.0.0.1:8081/gpu-release/v1"
MODEL_CACHE_VOLUME = "multi-tenant-ai-inference-platform-gpu-model-cache"
TARGET_ENVIRONMENT = "single-l4-lab"
MODEL_ID = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
IMAGE_REFERENCE = re.compile(r"^[A-Za-z0-9._:/-]+@sha256:[0-9a-f]{64}$")

ENVIRONMENT_KEYS = {
    "GPU_MODEL_ID": "model_id",
    "GPU_MODEL_REVISION": "model_revision",
    "GPU_MODEL_ARTIFACT_SHA256": "model_artifact_sha256",
    "GPU_SOURCE_COMMIT": "source_commit",
    "GPU_SERVED_MODEL_NAME": ("runtime_config", "served_model_name"),
    "VLLM_IMAGE": "vllm_image",
    "GPU_DTYPE": ("runtime_config", "dtype"),
    "GPU_MAX_MODEL_LEN": ("runtime_config", "max_model_len"),
    "GPU_MAX_NUM_SEQS": ("runtime_config", "max_num_seqs"),
    "GPU_MAX_BATCHED_TOKENS": ("runtime_config", "max_num_batched_tokens"),
    "GPU_MEMORY_UTILIZATION": ("runtime_config", "gpu_memory_utilization"),
    "GPU_TENSOR_PARALLEL_SIZE": ("runtime_config", "tensor_parallel_size"),
}


class ControllerError(RuntimeError):
    """Raised when a release cannot be safely verified or applied."""


class RejectRedirectHandler(HTTPRedirectHandler):
    """Do not forward the host's release token through an HTTP redirect."""

    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot_path(cache_dir: str | Path, model_id: str, revision: str) -> Path:
    if not MODEL_ID.fullmatch(model_id) or ".." in model_id.split("/"):
        raise ControllerError("model ID must be a namespace/name path")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ControllerError("model revision must be a full commit SHA")
    repo = "models--" + model_id.replace("/", "--")
    return Path(cache_dir) / repo / "snapshots" / revision


def model_snapshot_digest(cache_dir: str | Path, model_id: str, revision: str) -> str:
    """Hash every file visible in a pinned Hub snapshot using stable relative paths."""
    cache_root = Path(cache_dir).resolve(strict=True)
    snapshot = snapshot_path(cache_root, model_id, revision)
    if not snapshot.is_dir():
        raise ControllerError("pinned model snapshot is not present in the cache")

    entries: list[dict[str, int | str]] = []
    for path in sorted(snapshot.rglob("*")):
        if path.is_dir():
            continue
        resolved = path.resolve(strict=True)
        if not resolved.is_file() or not resolved.is_relative_to(cache_root):
            raise ControllerError("model snapshot contains a file outside the cache root")
        entries.append(
            {
                "path": path.relative_to(snapshot).as_posix(),
                "size_bytes": resolved.stat().st_size,
                "sha256": _sha256_file(resolved),
            }
        )
    if not entries:
        raise ControllerError("pinned model snapshot contains no files")
    return hashlib.sha256(canonical_json(entries)).hexdigest()


def manifest_from_json(value: dict[str, Any]) -> ReleaseManifest:
    try:
        manifest = ReleaseManifest(**value)
        verify_manifest(manifest)
        return manifest
    except (TypeError, ValueError) as error:
        raise ControllerError("release manifest is invalid") from error


def validate_serving_manifest(manifest: ReleaseManifest) -> None:
    """Enforce the single-L4 lab's bounded, shell-safe serving configuration."""
    config = manifest.runtime_config
    if not MODEL_ID.fullmatch(manifest.model_id) or any(
        part in {".", ".."} for part in manifest.model_id.split("/")
    ):
        raise ControllerError("model ID must be a namespace/name path")
    if not IMAGE_REFERENCE.fullmatch(manifest.vllm_image):
        raise ControllerError("vLLM image reference contains unsupported characters or is not pinned")
    alias = config.get("served_model_name")
    if not isinstance(alias, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", alias):
        raise ControllerError("served model name must use simple ASCII identifier characters")
    dtype = config.get("dtype")
    if not isinstance(dtype, str) or dtype not in {"bfloat16", "float16", "float32", "auto"}:
        raise ControllerError("model precision is outside the reviewed runtime options")
    bounds = {
        "max_model_len": (1, 32768),
        "max_num_seqs": (1, 4),
        "max_num_batched_tokens": (1, 32768),
    }
    for name, (minimum, maximum) in bounds.items():
        value = config.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            raise ControllerError(f"{name} is outside the bounded single-L4 lab range")
    memory = config.get("gpu_memory_utilization")
    if isinstance(memory, bool) or not isinstance(memory, (int, float)) or not 0.1 <= memory <= 0.9:
        raise ControllerError("GPU memory utilization must be between 0.1 and 0.9")
    if (
        isinstance(config.get("tensor_parallel_size"), bool)
        or config.get("tensor_parallel_size") != 1
    ):
        raise ControllerError("single-L4 release must use tensor_parallel_size=1")


def approved_plan_from_json(value: dict[str, Any]) -> tuple[ReleasePlan, ReleaseManifest, ReleaseManifest]:
    try:
        plan = ReleasePlan(**value["plan"])
        champion = manifest_from_json(value["champion"])
        candidate = manifest_from_json(value["candidate"])
        validate_serving_manifest(champion)
        validate_serving_manifest(candidate)
        verify_plan(plan)
        if plan.status != "APPROVED" or not plan.approved_by:
            raise ControllerError("release plan has not been independently approved")
        if plan.approved_by == plan.requester:
            raise ControllerError("release requester cannot approve the same plan")
        if plan.environment != TARGET_ENVIRONMENT:
            raise ControllerError("release plan targets a different environment")
        if champion.deployment_alias != "champion" or candidate.deployment_alias != "candidate":
            raise ControllerError("release plan has unexpected deployment aliases")
        if plan.champion_manifest_sha256 != champion.sha256:
            raise ControllerError("plan champion digest does not match its manifest")
        if plan.candidate_manifest_sha256 != candidate.sha256:
            raise ControllerError("plan candidate digest does not match its manifest")
        if (
            plan.candidate_model_id != candidate.model_id
            or plan.candidate_model_revision != candidate.model_revision
            or plan.vllm_image != candidate.vllm_image
            or plan.runtime_config_sha256 != candidate.runtime_config_sha256
            or plan.evaluation_report_sha256 != candidate.evaluation_report_sha256
        ):
            raise ControllerError("release plan fields do not match the candidate manifest")
        assert_not_stale(plan, current_champion=champion, current_candidate=candidate)
        return plan, champion, candidate
    except (KeyError, TypeError, ValueError) as error:
        raise ControllerError("approved plan evidence is incomplete or invalid") from error


def manifest_runtime_config(manifest: ReleaseManifest) -> dict[str, Any]:
    return {
        "model_id": manifest.model_id,
        "model_revision": manifest.model_revision,
        "model_artifact_sha256": manifest.model_artifact_sha256,
        "source_commit": manifest.source_commit,
        "vllm_image": manifest.vllm_image,
        "runtime_config": manifest.runtime_config,
    }


def update_environment(raw: str, manifest: ReleaseManifest) -> str:
    """Update only model-serving keys; keep operator secrets and comments untouched."""
    values = manifest_runtime_config(manifest)
    updates = {
        key: str(values[path] if isinstance(path, str) else values[path[0]][path[1]])
        for key, path in ENVIRONMENT_KEYS.items()
    }
    if any("\n" in value or "\r" in value for value in updates.values()):
        raise ControllerError("release configuration contains a newline")
    lines = raw.splitlines(keepends=True)
    found: set[str] = set()
    for index, line in enumerate(lines):
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=", line)
        if match and match.group(1) in updates:
            key = match.group(1)
            ending = "\n" if line.endswith("\n") else ""
            lines[index] = f"{key}={updates[key]}{ending}"
            found.add(key)
    for key, value in updates.items():
        if key not in found:
            lines.append(f"{key}={value}\n")
    return "".join(lines)


def atomic_write_private(path: Path, content: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        previous_owner = path.stat()
    except FileNotFoundError:
        previous_owner = None
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        if previous_owner is not None and os.geteuid() == 0:
            os.fchown(fd, previous_owner.st_uid, previous_owner.st_gid)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def verify_container_config(inspect: dict[str, Any], manifest: ReleaseManifest) -> None:
    if inspect.get("State", {}).get("Status") != "running":
        raise ControllerError("vLLM container is not running")
    if inspect.get("State", {}).get("Health", {}).get("Status") != "healthy":
        raise ControllerError("vLLM container is not healthy")
    config = inspect.get("Config", {})
    if config.get("Image") != manifest.vllm_image:
        raise ControllerError("running vLLM image does not match the active manifest")
    mounts = inspect.get("Mounts", [])
    if not any(
        mount.get("Type") == "volume"
        and mount.get("Name") == MODEL_CACHE_VOLUME
        and mount.get("Destination") == "/root/.cache/huggingface"
        for mount in mounts
    ):
        raise ControllerError("running vLLM container does not use the verified model-cache volume")
    command = config.get("Cmd") or []
    expected = {
        "--model": manifest.model_id,
        "--revision": manifest.model_revision,
        "--served-model-name": manifest.runtime_config["served_model_name"],
        "--dtype": manifest.runtime_config["dtype"],
        "--max-model-len": str(manifest.runtime_config["max_model_len"]),
        "--max-num-seqs": str(manifest.runtime_config["max_num_seqs"]),
        "--max-num-batched-tokens": str(manifest.runtime_config["max_num_batched_tokens"]),
        "--gpu-memory-utilization": str(manifest.runtime_config["gpu_memory_utilization"]),
        "--tensor-parallel-size": str(manifest.runtime_config["tensor_parallel_size"]),
    }
    actual = {command[index]: command[index + 1] for index in range(len(command) - 1)}
    if any(actual.get(key) != value for key, value in expected.items()):
        raise ControllerError("running vLLM command does not match the active manifest")


def _request_json(url: str, token: str, timeout: float = 15) -> dict[str, Any]:
    request = Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        # Do not forward a bearer token to a redirected host or a downgraded URL.
        opener = build_opener(RejectRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            return json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ControllerError("release API request failed") from error


def fetch_approved_plan(api_url: str, plan_id: str, token: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Fa-f0-9-]{36}", plan_id):
        raise ControllerError("plan ID must be a UUID")
    parsed = urlsplit(api_url)
    if parsed.username or parsed.password or not parsed.hostname:
        raise ControllerError("release API URL is invalid")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    ):
        raise ControllerError("release API must use HTTPS or a local loopback address")
    return _request_json(f"{api_url.rstrip('/')}/plans/{plan_id}", token)


class HostController:
    """Coordinate one vLLM container and keep a recoverable active manifest."""

    def __init__(
        self,
        *,
        repo: Path = REPOSITORY,
        env_file: Path = DEFAULT_ENV_FILE,
        state_file: Path = DEFAULT_STATE_FILE,
        api_url: str = DEFAULT_API_URL,
        command_runner=subprocess.run,
        sleeper=time.sleep,
    ) -> None:
        self.repo = repo
        self.env_file = env_file
        self.state_file = state_file
        self.api_url = api_url.rstrip("/")
        self.run = command_runner
        self.sleep = sleeper

    def _compose(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        return self.run(
            [
                "docker",
                "compose",
                "--env-file",
                str(self.env_file),
                "-f",
                str(self.repo / "deployments/single-gpu/compose.yaml"),
                *args,
            ],
            cwd=self.repo,
            check=check,
            capture_output=True,
            text=True,
        )

    def _container_inspect(self) -> dict[str, Any]:
        container_id = self._compose("ps", "-q", "vllm").stdout.strip()
        if not container_id:
            raise ControllerError("Compose has no vLLM container")
        result = self.run(
            ["docker", "inspect", container_id],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)[0]

    def _snapshot_digest(self, manifest: ReleaseManifest) -> str:
        result = self.run(
            [
                "docker",
                "volume",
                "inspect",
                "--format",
                "{{.Mountpoint}}",
                MODEL_CACHE_VOLUME,
            ],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        )
        cache = Path(result.stdout.strip()) / "hub"
        return model_snapshot_digest(cache, manifest.model_id, manifest.model_revision)

    def _check_http_ready(self, manifest: ReleaseManifest) -> None:
        deadline = time.monotonic() + 300
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                with urlopen("http://127.0.0.1:8000/health", timeout=3) as response:
                    if response.status != 200:
                        raise ControllerError("vLLM health endpoint is not ready")
                with urlopen("http://127.0.0.1:8000/v1/models", timeout=3) as response:
                    models = json.loads(response.read()).get("data", [])
                if not any(
                    model.get("id") == manifest.runtime_config["served_model_name"]
                    for model in models
                ):
                    raise ControllerError("vLLM does not expose the approved served model")
                for port in (8081, 8082):
                    with urlopen(f"http://127.0.0.1:{port}/healthz", timeout=3) as response:
                        if response.status != 200:
                            raise ControllerError(f"gateway replica on port {port} is not ready")
                return
            except (ControllerError, OSError, ValueError) as error:
                last_error = error
                self.sleep(5)
        raise ControllerError("vLLM or gateway readiness timed out") from last_error

    def _read_state(self) -> tuple[dict[str, Any], ReleaseManifest]:
        try:
            record = json.loads(self.state_file.read_text(encoding="utf-8"))
            manifest = manifest_from_json(record["manifest"])
            validate_serving_manifest(manifest)
            if record.get("manifest_sha256") != manifest.sha256:
                raise ControllerError("active release-state digest is invalid")
            return record, manifest
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise ControllerError("active release state is missing or invalid") from error

    def _persist_state(self, manifest: ReleaseManifest, plan_id: str | None) -> None:
        self.state_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.state_file.parent, 0o700)
        record = {
            "schema_version": 1,
            "manifest": asdict(manifest),
            "manifest_sha256": manifest.sha256,
            "last_plan_id": plan_id,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        atomic_write_private(self.state_file, json.dumps(record, sort_keys=True, indent=2).encode())

    def _verify_live(self, manifest: ReleaseManifest) -> None:
        verify_container_config(self._container_inspect(), manifest)
        self._check_http_ready(manifest)
        actual = self._snapshot_digest(manifest)
        if actual != manifest.model_artifact_sha256:
            raise ControllerError("cached model files do not match the active manifest digest")

    def initialize_champion(self, manifest: ReleaseManifest) -> None:
        """Record the initial champion only after checking the live server and files."""
        lock_path = self.state_file.with_suffix(".lock")
        lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(lock_path.parent, 0o700)
        with lock_path.open("a+b") as lock:
            os.chmod(lock_path, 0o600)
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ControllerError("another release operation holds the host lock") from error
            if self.state_file.exists():
                raise ControllerError("active release state already exists; refusing to replace it")
            if manifest.deployment_alias != "champion":
                raise ControllerError("initial active release must use champion alias")
            validate_serving_manifest(manifest)
            self._verify_live(manifest)
            self._persist_state(manifest, plan_id=None)

    def model_digest(self, model_id: str, revision: str) -> str:
        result = self.run(
            [
                "docker",
                "volume",
                "inspect",
                "--format",
                "{{.Mountpoint}}",
                MODEL_CACHE_VOLUME,
            ],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return model_snapshot_digest(Path(result.stdout.strip()) / "hub", model_id, revision)

    def deploy(self, plan_id: str, token: str) -> None:
        lock_path = self.state_file.with_suffix(".lock")
        lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(lock_path.parent, 0o700)
        with lock_path.open("a+b") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self._has_incomplete_transaction():
                raise ControllerError("an earlier deployment is incomplete; run recover first")
            response = fetch_approved_plan(self.api_url, plan_id, token)
            plan, champion, candidate = approved_plan_from_json(response)
            active_record, active = self._read_state()
            if active.sha256 != champion.sha256:
                raise ControllerError("approved plan champion differs from recorded active release")
            assert_not_stale(plan, current_champion=active, current_candidate=candidate)
            self._verify_live(active)
            if self._snapshot_digest(candidate) != candidate.model_artifact_sha256:
                raise ControllerError("candidate model files do not match the approved digest")

            original_env = self.env_file.read_bytes()
            original_text = original_env.decode("utf-8")
            transaction = {
                "plan_id": plan.plan_id,
                "previous_manifest_sha256": active.sha256,
                "candidate_manifest_sha256": candidate.sha256,
                "started_at": datetime.now(UTC).isoformat(),
                "state": "APPLYING",
            }
            journal = self.state_file.parent / f"transaction-{plan.plan_id}.json"
            atomic_write_private(journal, json.dumps(transaction, sort_keys=True).encode())
            try:
                new_env = update_environment(original_text, candidate)
                atomic_write_private(self.env_file, new_env.encode())
                self._compose("config", "--quiet")
                self._compose("up", "-d", "--no-deps", "--force-recreate", "vllm")
                self._wait_container_config(candidate)
                self._compose("up", "-d", "--no-deps", "gateway-1", "gateway-2")
                self._check_http_ready(candidate)
                if self._snapshot_digest(candidate) != candidate.model_artifact_sha256:
                    raise ControllerError("loaded candidate files changed during deployment")
                promoted = replace(candidate, deployment_alias="champion")
                verify_manifest(promoted)
                self._persist_state(promoted, plan_id=plan.plan_id)
                transaction["state"] = "DEPLOYED"
                transaction["finished_at"] = datetime.now(UTC).isoformat()
                atomic_write_private(journal, json.dumps(transaction, sort_keys=True).encode())
            except Exception as deployment_error:
                try:
                    atomic_write_private(self.env_file, original_env)
                    self._compose("up", "-d", "--no-deps", "--force-recreate", "vllm")
                    self._wait_container_config(active)
                    self._compose("up", "-d", "--no-deps", "gateway-1", "gateway-2")
                    self._check_http_ready(active)
                    if self._snapshot_digest(active) != active.model_artifact_sha256:
                        raise ControllerError("restored model files do not match the active digest")
                    self._persist_state(active, plan_id=active_record.get("last_plan_id"))
                    transaction["state"] = "ROLLED_BACK"
                    transaction["finished_at"] = datetime.now(UTC).isoformat()
                    transaction["error_type"] = type(deployment_error).__name__
                    atomic_write_private(journal, json.dumps(transaction, sort_keys=True).encode())
                except Exception as rollback_error:
                    transaction["state"] = "ROLLBACK_FAILED"
                    transaction["finished_at"] = datetime.now(UTC).isoformat()
                    transaction["error_type"] = type(deployment_error).__name__
                    transaction["rollback_error_type"] = type(rollback_error).__name__
                    atomic_write_private(journal, json.dumps(transaction, sort_keys=True).encode())
                    raise ControllerError(
                        "deployment failed and automatic rollback could not be verified; use the recovery runbook"
                    ) from rollback_error
                raise ControllerError("candidate deployment failed; previous champion was restored") from deployment_error

    def _transaction_files(self) -> list[Path]:
        return sorted(self.state_file.parent.glob("transaction-*.json"))

    def _has_incomplete_transaction(self) -> bool:
        for path in self._transaction_files():
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ControllerError("a deployment transaction record is unreadable") from error
            if record.get("state") in {"APPLYING", "ROLLBACK_FAILED"}:
                return True
        return False

    def recover(self) -> None:
        lock_path = self.state_file.with_suffix(".lock")
        lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(lock_path.parent, 0o700)
        with lock_path.open("a+b") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            pending = []
            for path in self._transaction_files():
                record = json.loads(path.read_text(encoding="utf-8"))
                if record.get("state") in {"APPLYING", "ROLLBACK_FAILED"}:
                    pending.append((path, record))
            if not pending:
                raise ControllerError("there is no interrupted deployment to recover")
            if len(pending) != 1:
                raise ControllerError("multiple incomplete transactions need manual review")
            journal, transaction = pending[0]
            _, active = self._read_state()
            atomic_write_private(
                self.env_file,
                update_environment(self.env_file.read_text(encoding="utf-8"), active).encode(),
            )
            self._compose("config", "--quiet")
            self._compose("up", "-d", "--no-deps", "--force-recreate", "vllm")
            self._wait_container_config(active)
            self._compose("up", "-d", "--no-deps", "gateway-1", "gateway-2")
            self._check_http_ready(active)
            if self._snapshot_digest(active) != active.model_artifact_sha256:
                raise ControllerError("recovered model files do not match the active manifest")
            transaction["state"] = "RECOVERED_TO_ACTIVE_RELEASE"
            transaction["finished_at"] = datetime.now(UTC).isoformat()
            atomic_write_private(journal, json.dumps(transaction, sort_keys=True).encode())

    def restore_active(self) -> None:
        """Reload the independently recorded champion after an evaluation-only run."""
        lock_path = self.state_file.with_suffix(".lock")
        lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(lock_path.parent, 0o700)
        with lock_path.open("a+b") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self._has_incomplete_transaction():
                raise ControllerError("an earlier deployment is incomplete; run recover first")
            _, active = self._read_state()
            plan_id = "restore-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            journal = self.state_file.parent / f"transaction-{plan_id}.json"
            transaction = {
                "plan_id": plan_id,
                "previous_manifest_sha256": active.sha256,
                "candidate_manifest_sha256": active.sha256,
                "started_at": datetime.now(UTC).isoformat(),
                "state": "APPLYING",
            }
            atomic_write_private(journal, json.dumps(transaction, sort_keys=True).encode())
            new_env = update_environment(self.env_file.read_text(encoding="utf-8"), active)
            atomic_write_private(self.env_file, new_env.encode())
            self._compose("config", "--quiet")
            self._compose("up", "-d", "--no-deps", "--force-recreate", "vllm")
            self._wait_container_config(active)
            self._compose("up", "-d", "--no-deps", "gateway-1", "gateway-2")
            self._check_http_ready(active)
            if self._snapshot_digest(active) != active.model_artifact_sha256:
                raise ControllerError("active champion files do not match their manifest")
            transaction["state"] = "RESTORED_TO_ACTIVE"
            transaction["finished_at"] = datetime.now(UTC).isoformat()
            atomic_write_private(journal, json.dumps(transaction, sort_keys=True).encode())

    def _wait_container_config(self, manifest: ReleaseManifest) -> None:
        deadline = time.monotonic() + 300
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                verify_container_config(self._container_inspect(), manifest)
                return
            except (ControllerError, subprocess.SubprocessError, json.JSONDecodeError) as error:
                last_error = error
                self.sleep(5)
        raise ControllerError("vLLM container did not reach the approved configuration") from last_error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    apply_parser = commands.add_parser("apply", help="apply one independently approved release")
    apply_parser.add_argument("plan_id", help="approved UUID plan ID from the release API")
    apply_parser.add_argument("--api-url", default=os.getenv("GPU_RELEASE_API_URL", DEFAULT_API_URL))
    initialize_parser = commands.add_parser("initialize", help="verify and record the initial champion")
    initialize_parser.add_argument("manifest_file", type=Path)
    digest_parser = commands.add_parser("model-digest", help="hash every file in a pinned Hub snapshot")
    digest_parser.add_argument("model_id")
    digest_parser.add_argument("revision")
    manifest_parser = commands.add_parser(
        "manifest-from-report", help="create a metadata-only manifest from a sanitized report"
    )
    manifest_parser.add_argument("report_file", type=Path)
    manifest_parser.add_argument("--model-id", required=True)
    manifest_parser.add_argument("--model-revision", required=True)
    manifest_parser.add_argument("--model-license", required=True)
    manifest_parser.add_argument("--model-artifact-sha256", required=True)
    manifest_parser.add_argument("--vllm-image", required=True)
    manifest_parser.add_argument("--runtime-config", type=Path, required=True)
    manifest_parser.add_argument("--source-commit", required=True)
    manifest_parser.add_argument("--alias", choices=("champion", "candidate"), required=True)
    manifest_parser.add_argument("--output", type=Path)
    commands.add_parser("recover", help="restore the last recorded champion after interruption")
    for command_parser in (apply_parser, initialize_parser):
        command_parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
        command_parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    digest_parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    digest_parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    recover_parser = commands.choices["recover"]
    recover_parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    recover_parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    restore_parser = commands.add_parser(
        "restore-active", help="reload the recorded champion after candidate evaluation"
    )
    restore_parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    restore_parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    args = parser.parse_args()
    controller = HostController(
        env_file=args.env_file,
        state_file=args.state_file,
    )
    try:
        if args.command == "apply":
            token = getpass.getpass("Platform admin bearer token: ")
            if not token.strip():
                parser.error("a short-lived platform.admin token is required")
            controller.api_url = args.api_url.rstrip("/")
            controller.deploy(args.plan_id, token.strip())
        elif args.command == "initialize":
            manifest = manifest_from_json(json.loads(args.manifest_file.read_text(encoding="utf-8")))
            controller.initialize_champion(manifest)
        elif args.command == "model-digest":
            print(controller.model_digest(args.model_id, args.revision))
            return 0
        elif args.command == "manifest-from-report":
            manifest = create_manifest(
                args.report_file,
                model_id=args.model_id,
                model_revision=args.model_revision,
                model_license=args.model_license,
                model_artifact_sha256=args.model_artifact_sha256,
                vllm_image=args.vllm_image,
                runtime_config=json.loads(args.runtime_config.read_text(encoding="utf-8")),
                source_commit=args.source_commit,
                deployment_alias=args.alias,
            )
            output = json.dumps(asdict(manifest), sort_keys=True, indent=2).encode()
            if args.output:
                atomic_write_private(args.output, output + b"\n")
            else:
                print(output.decode())
            return 0
        elif args.command == "recover":
            controller.recover()
        else:
            controller.restore_active()
    except (
        ControllerError,
        ReleaseValidationError,
        OSError,
        subprocess.SubprocessError,
        ValueError,
        TypeError,
    ) as error:
        print(f"release was not applied: {error}", file=sys.stderr)
        return 1
    if args.command == "apply":
        print(f"approved release {args.plan_id} passed runtime and gateway readiness checks")
    elif args.command == "initialize":
        print("initial champion passed runtime, artifact, and gateway checks")
    elif args.command == "recover":
        print("active champion was restored and verified")
    else:
        print("recorded champion was restored and verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
