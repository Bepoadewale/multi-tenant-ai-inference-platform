"""Execute two fixed, inspectable fixture tasks in a hardened disposable container.

The controller is a trusted local platform service and alone receives Docker API
access. Task containers never receive the socket, a host bind mount, network access,
or an arbitrary command supplied by an agent.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

import docker
from docker.errors import DockerException
from docker.types import Mount

SANDBOX_IMAGE = "inference-agent-sandbox:local"
LABELS = {
    "com.bepoadewale.project": "multi-tenant-ai-inference-platform",
    "inference.platform.resource": "sandbox",
}

COMMANDS = {
    "fixture_patch": [
        "sh",
        "-ec",
        "test ! -e /var/run/docker.sock; python -m unittest -q; "
        "printf '\\n# bounded agent patch\\n' >> app.py; python -m unittest -q",
    ],
    "containment_probe": [
        "sh",
        "-ec",
        "test ! -e /var/run/docker.sock; "
        "if wget -T 2 -qO- http://example.com >/dev/null 2>&1; then exit 42; fi; "
        "echo network-exfiltration-blocked",
    ],
}


@dataclass(frozen=True)
class SandboxResult:
    exit_code: int
    stdout: str
    patch_sha256: str
    hardening: dict[str, object]


class HardenedSandboxExecutor:
    """Docker SDK adapter that owns only labelled, short-lived sandbox resources."""

    def __init__(self, client: docker.DockerClient | None = None) -> None:
        self.client = client or docker.from_env()

    @staticmethod
    def _name(prefix: str) -> str:
        return f"inference-platform-{prefix}-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _hardening() -> dict[str, object]:
        return {
            "user": "65532:65532",
            "read_only_rootfs": True,
            "cap_drop": ["ALL"],
            "no_new_privileges": True,
            "network_mode": "none",
            "pids_limit": 32,
            "memory_limit": "128m",
            "cpu_limit": "0.5",
            "docker_socket_mounted": False,
            "host_bind_mounted": False,
        }

    def _container_kwargs(self, volume: str, command: list[str]) -> dict:
        return {
            "image": SANDBOX_IMAGE,
            "command": command,
            "name": self._name("sandbox"),
            "network_mode": "none",
            "read_only": True,
            "cap_drop": ["ALL"],
            "security_opt": ["no-new-privileges"],
            "pids_limit": 32,
            "mem_limit": "128m",
            "nano_cpus": 500_000_000,
            "tmpfs": {"/tmp": "rw,noexec,nosuid,size=16m"},
            "user": "65532:65532",
            "working_dir": "/workspace",
            "mounts": [Mount(target="/workspace", source=volume, type="volume", no_copy=True)],
            "labels": LABELS,
        }

    def execute(self, task_kind: str) -> SandboxResult:
        command = COMMANDS[task_kind]
        volume_name = self._name("workspace")
        volume = self.client.volumes.create(name=volume_name, labels=LABELS)
        containers = []
        try:
            # Docker creates named volumes as root. This trusted, one-shot setup
            # container changes ownership only; agent input never reaches it.
            self.client.containers.run(
                "alpine:3.21",
                ["chown", "65532:65532", "/workspace"],
                remove=True,
                network_mode="none",
                mounts=[Mount(target="/workspace", source=volume_name, type="volume", no_copy=True)],
            )
            initializer = self.client.containers.create(
                **self._container_kwargs(
                    volume_name,
                    ["git", "clone", "--no-local", "/opt/fixture-repo", "/workspace"],
                )
            )
            containers.append(initializer)
            initializer.start()
            init_result = initializer.wait(timeout=15)
            if int(init_result["StatusCode"]) != 0:
                raise RuntimeError("sandbox fixture clone failed")

            task = self.client.containers.create(**self._container_kwargs(volume_name, command))
            containers.append(task)
            task.start()
            result = task.wait(timeout=20)
            output = task.logs(stdout=True, stderr=True).decode(errors="replace")[:16_384]

            collector = self.client.containers.create(
                **self._container_kwargs(volume_name, ["git", "diff", "--no-ext-diff"])
            )
            containers.append(collector)
            collector.start()
            collector.wait(timeout=15)
            patch = collector.logs(stdout=True, stderr=True)
            return SandboxResult(
                exit_code=int(result["StatusCode"]),
                stdout=output,
                patch_sha256=hashlib.sha256(patch).hexdigest(),
                hardening=self._hardening(),
            )
        except DockerException as error:
            raise RuntimeError("sandbox Docker API operation failed") from error
        finally:
            for container in containers:
                try:
                    container.remove(force=True)
                except DockerException:
                    pass
            try:
                volume.remove(force=True)
            except DockerException:
                pass
