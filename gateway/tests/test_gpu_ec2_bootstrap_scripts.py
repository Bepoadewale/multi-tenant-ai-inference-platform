"""Tests for the private, saved-plan Terraform bootstrap workflow."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from scripts.gpu_ec2_bootstrap_plan_summary import validate

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ACCOUNT = "123456789012"
RECIPIENT = "billing@example.com"
ADDRESSES = [
    "aws_budgets_budget.monthly_pilot",
    "aws_dynamodb_table.terraform_locks",
    "aws_s3_bucket.terraform_state",
    "aws_s3_bucket_ownership_controls.terraform_state",
    "aws_s3_bucket_public_access_block.terraform_state",
    "aws_s3_bucket_server_side_encryption_configuration.terraform_state",
    "aws_s3_bucket_versioning.terraform_state",
]


def _resource(address: str, after: dict[str, object]) -> dict[str, object]:
    return {
        "address": address,
        "mode": "managed",
        "change": {"actions": ["create"], "after": after},
    }


def _plan(email: str = RECIPIENT) -> dict[str, object]:
    notifications = [
        {
            "notification_type": "ACTUAL",
            "comparison_operator": "GREATER_THAN",
            "threshold_type": "PERCENTAGE",
            "threshold": threshold,
            "subscriber_email_addresses": [email],
        }
        for threshold in (50, 80, 100)
    ]
    after = {
        "aws_budgets_budget.monthly_pilot": {
            "name": "multi-tenant-ai-inference-platform-pilot-monthly-cost",
            "budget_type": "COST",
            "limit_amount": "10",
            "limit_unit": "USD",
            "time_unit": "MONTHLY",
            "notification": notifications,
        },
        "aws_dynamodb_table.terraform_locks": {
            "name": "multi-tenant-ai-inference-platform-pilot-terraform-locks",
            "billing_mode": "PAY_PER_REQUEST",
            "hash_key": "LockID",
        },
        "aws_s3_bucket.terraform_state": {
            "bucket": f"multi-tenant-ai-inference-platform-tfstate-{EXPECTED_ACCOUNT}",
            "force_destroy": False,
            "tags": {"project": "multi-tenant-ai-inference-platform", "environment": "pilot"},
        },
        "aws_s3_bucket_ownership_controls.terraform_state": {
            "rule": [{"object_ownership": "BucketOwnerEnforced"}]
        },
        "aws_s3_bucket_public_access_block.terraform_state": {
            "block_public_acls": True,
            "block_public_policy": True,
            "ignore_public_acls": True,
            "restrict_public_buckets": True,
        },
        "aws_s3_bucket_server_side_encryption_configuration.terraform_state": {
            "rule": [
                {"apply_server_side_encryption_by_default": [{"sse_algorithm": "AES256"}]}
            ]
        },
        "aws_s3_bucket_versioning.terraform_state": {
            "versioning_configuration": [{"status": "Enabled"}]
        },
    }
    return {"resource_changes": [_resource(address, after[address]) for address in ADDRESSES]}


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _fake_tools(tmp_path: Path) -> tuple[Path, Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    aws_log = tmp_path / "aws.log"
    terraform_log = tmp_path / "terraform.log"
    _write_executable(
        bin_dir / "aws",
        "#!/usr/bin/env python3\n"
        "import os, pathlib, sys\n"
        f"pathlib.Path({str(aws_log)!r}).open('a').write(' '.join(sys.argv[1:]) + '\\n')\n"
        "args=sys.argv[1:]\n"
        f"if args[:2] == ['sts','get-caller-identity']: print(os.getenv('FAKE_ACCOUNT',{EXPECTED_ACCOUNT!r}))\n"
        "elif args[:2] == ['s3api','list-buckets']: print(os.getenv('FAKE_BUCKET_COUNT','0'))\n"
        "elif args[:2] == ['dynamodb','describe-table']: print('ResourceNotFoundException',file=sys.stderr); sys.exit(1)\n"
        "elif args[:2] == ['budgets','describe-budgets']: print('0')\n"
        "else: print('None')\n",
    )
    _write_executable(
        bin_dir / "terraform",
        "#!/usr/bin/env python3\n"
        "import json, os, pathlib, sys\n"
        f"pathlib.Path({str(terraform_log)!r}).open('a').write(' '.join(sys.argv[1:]) + '\\n')\n"
        "args=sys.argv[1:]\n"
        "if 'plan' in args:\n"
        "  out=next(v.split('=',1)[1] for v in args if v.startswith('-out='))\n"
        "  pathlib.Path(out).write_bytes(b'private fake plan')\n"
        "elif 'show' in args and '-json' in args: print(os.environ['FAKE_PLAN_JSON'])\n"
        "elif args[-2:] == ['state','list']:\n"
        f"  print('\\n'.join({ADDRESSES!r}))\n"
        "elif 'apply' in args:\n"
        "  pathlib.Path(os.environ['FAKE_STATE_PATH']).write_text('fake state')\n",
    )
    return bin_dir, aws_log, terraform_log


def _env(tmp_path: Path, bin_dir: Path, email: str = RECIPIENT) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["EXPECTED_AWS_ACCOUNT_ID"] = EXPECTED_ACCOUNT
    env["GPU_EC2_BOOTSTRAP_BUDGET_EMAIL"] = email
    env["GPU_EC2_BOOTSTRAP_RUN_ID"] = "20261128T120000Z"
    env["GPU_EC2_BOOTSTRAP_ARTIFACT_DIR"] = str(tmp_path / "private")
    env["FAKE_PLAN_JSON"] = json.dumps(_plan(email))
    env["FAKE_STATE_PATH"] = str(tmp_path / "private" / "gpu-ec2-bootstrap-20261128T120000Z" / "terraform.tfstate")
    return env


def test_bootstrap_plan_and_apply_keep_recipient_private(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_tools(tmp_path)
    env = _env(tmp_path, bin_dir)

    planned = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-bootstrap-plan.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert planned.returncode == 0, planned.stderr
    assert "7 create, 0 update, 0 delete" in planned.stdout
    assert "recipient hidden" in planned.stdout
    assert RECIPIENT not in planned.stdout + planned.stderr
    digest = re.search(r"Plan SHA-256: ([0-9a-f]{64})", planned.stdout)
    assert digest

    env["GPU_EC2_BOOTSTRAP_CONFIRM"] = "apply"
    env["GPU_EC2_BOOTSTRAP_PLAN_SHA256"] = digest.group(1)
    applied = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-bootstrap-apply.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert applied.returncode == 0, applied.stderr
    assert "local state remains private" in applied.stdout
    assert RECIPIENT not in applied.stdout + applied.stderr
    assert "apply" in terraform_log.read_text(encoding="utf-8")
    assert "recipient" not in aws_log.read_text(encoding="utf-8").lower()


def test_bootstrap_plan_rejects_placeholder_before_aws_or_terraform(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_tools(tmp_path)
    env = _env(tmp_path, bin_dir, "operator@example.invalid")

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-bootstrap-plan.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "usable email address" in result.stderr
    assert not aws_log.exists()
    assert not terraform_log.exists()


def test_bootstrap_apply_requires_confirmation_before_aws_or_terraform(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_tools(tmp_path)
    env = _env(tmp_path, bin_dir)

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-bootstrap-apply.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "refusing apply" in result.stderr
    assert not aws_log.exists()
    assert not terraform_log.exists()


def test_bootstrap_apply_rejects_a_wrong_digest_before_aws(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_tools(tmp_path)
    env = _env(tmp_path, bin_dir)
    workspace = Path(env["GPU_EC2_BOOTSTRAP_ARTIFACT_DIR"]) / "gpu-ec2-bootstrap-20261128T120000Z"
    workspace.mkdir(parents=True)
    plan_file = Path(env["GPU_EC2_BOOTSTRAP_ARTIFACT_DIR"]) / "gpu-ec2-bootstrap-20261128T120000Z.tfplan"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_bytes(b"a different plan")
    env["GPU_EC2_BOOTSTRAP_CONFIRM"] = "apply"
    env["GPU_EC2_BOOTSTRAP_PLAN_SHA256"] = "0" * 64

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-bootstrap-apply.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "SHA-256 does not match" in result.stderr
    assert not aws_log.exists()
    assert not terraform_log.exists()


def test_bootstrap_plan_refuses_existing_bucket_before_terraform(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_tools(tmp_path)
    env = _env(tmp_path, bin_dir)
    env["FAKE_BUCKET_COUNT"] = "1"

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-bootstrap-plan.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "bucket already exists" in result.stderr
    assert not terraform_log.exists()
    assert "s3api list-buckets" in aws_log.read_text(encoding="utf-8")


def test_bootstrap_plan_summary_rejects_unexpected_actions_and_resources() -> None:
    extra = _plan()
    extra["resource_changes"].append(_resource("aws_instance.unexpected", {}))
    with pytest.raises(ValueError, match="exactly the seven"):
        validate(extra, EXPECTED_ACCOUNT)

    changed = _plan()
    changed["resource_changes"][0]["change"]["actions"] = ["update"]
    with pytest.raises(ValueError, match="creates only"):
        validate(changed, EXPECTED_ACCOUNT)
