"""Regression tests for guarded single-L4 Terraform wrapper scripts."""

from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ACCOUNT = "654654474502"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _fake_cli_bin(tmp_path: Path) -> tuple[Path, Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    aws_log = tmp_path / "aws.log"
    terraform_log = tmp_path / "terraform.log"
    _write_executable(
        bin_dir / "aws",
        "#!/usr/bin/env python3\n"
        "import os, pathlib, sys\n"
        f"pathlib.Path({str(aws_log)!r}).open('a').write(os.getenv('AWS_PROFILE', '<unset>') + ' ' + ' '.join(sys.argv[1:]) + '\\n')\n"
        "args = sys.argv[1:]\n"
        f"if args[:2] == ['sts', 'get-caller-identity']: print({EXPECTED_ACCOUNT!r})\n"
        "elif args[:2] == ['service-quotas', 'get-service-quota']: print('4')\n"
        "elif args[:2] == ['ec2', 'describe-instance-type-offerings']: print('g6.xlarge')\n"
        "elif args[:2] == ['budgets', 'describe-budgets']: print('1')\n"
        "elif args[:2] == ['dynamodb', 'describe-table']: print('ACTIVE')\n"
        "elif args[:2] == ['iam', 'list-roles'] or args[:2] == ['iam', 'list-instance-profiles']: print('0')\n"
        "elif args[:2] == ['scheduler', 'list-schedule-groups']: print('0')\n"
        "else: print('None')\n",
    )
    _write_executable(
        bin_dir / "terraform",
        "#!/usr/bin/env python3\n"
        "import os, pathlib, sys\n"
        f"pathlib.Path({str(terraform_log)!r}).open('a').write(os.getenv('AWS_PROFILE', '<unset>') + ' ' + ' '.join(sys.argv[1:]) + '\\n')\n"
        "for arg in sys.argv[1:]:\n"
        "    if arg.startswith('-out='):\n"
        "        pathlib.Path(arg.split('=', 1)[1]).write_bytes(b'fake saved plan')\n",
    )
    return bin_dir, aws_log, terraform_log


def _subprocess_env(bin_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("AWS_PROFILE", None)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["EXPECTED_AWS_ACCOUNT_ID"] = EXPECTED_ACCOUNT
    env["GPU_EC2_AZ"] = "us-east-1a"
    expiry = datetime.now(UTC) + timedelta(hours=6)
    env["GPU_EC2_EXPIRES_AT"] = expiry.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return env


def test_gpu_ec2_plan_and_apply_share_the_default_profile(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    plan_file = tmp_path / "gpu-ec2.tfplan"
    env = _subprocess_env(bin_dir)
    env["GPU_EC2_PLAN_FILE"] = str(plan_file)

    planned = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-plan.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert planned.returncode == 0, planned.stderr
    assert "ai-platform-pilot-key" in aws_log.read_text(encoding="utf-8")
    plan_profiles = [line.split()[0] for line in terraform_log.read_text(encoding="utf-8").splitlines()]
    assert plan_profiles == ["ai-platform-pilot-key", "ai-platform-pilot-key"]

    env["GPU_EC2_CONFIRM"] = "apply"
    env["GPU_EC2_PLAN_SHA256"] = hashlib.sha256(plan_file.read_bytes()).hexdigest()
    applied = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-apply.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert applied.returncode == 0, applied.stderr
    profiles = [line.split()[0] for line in terraform_log.read_text(encoding="utf-8").splitlines()]
    assert profiles == ["ai-platform-pilot-key"] * 3


def test_clean_verifier_skips_missing_scheduler_group_enumeration(tmp_path: Path) -> None:
    bin_dir, aws_log, _ = _fake_cli_bin(tmp_path)
    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-verify-clean.sh")],
        env=_subprocess_env(bin_dir),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "absent: project one-time expiry schedule (schedule group is absent)" in result.stdout
    assert "scheduler list-schedules" not in aws_log.read_text(encoding="utf-8")
