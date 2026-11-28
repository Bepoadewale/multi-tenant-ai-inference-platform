"""Regression tests for guarded single-L4 Terraform wrapper scripts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ACCOUNT = "654654474502"
PROJECT = "multi-tenant-ai-inference-platform"


def _safe_plan_json(ami: str, az: str, expiry: str) -> str:
    from scripts.gpu_ec2_plan_summary import EXPECTED_ADDRESSES, TAGGED_ADDRESSES

    tags = {
        "Name": f"{PROJECT}-gpu-ec2",
        "project": PROJECT,
        "environment": "gpu-ec2",
        "managed_by": "terraform",
        "owner": "bepoadewale",
        "cost_scope": "gpu-ec2",
        "expires_at": expiry,
        "data_class": "synthetic-only",
    }
    after_by_address = {
        "aws_vpc.gpu": {
            "cidr_block": "10.74.0.0/16",
            "enable_dns_support": True,
            "enable_dns_hostnames": True,
        },
        "aws_internet_gateway.gpu": {},
        "aws_subnet.gpu": {
            "cidr_block": "10.74.1.0/24",
            "availability_zone": az,
            "map_public_ip_on_launch": True,
        },
        "aws_route_table.gpu": {"route": [{"cidr_block": "0.0.0.0/0"}]},
        "aws_route_table_association.gpu": {},
        "aws_security_group.gpu": {
            "ingress": [],
            "egress": [
                {
                    "protocol": "tcp",
                    "from_port": port,
                    "to_port": port,
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": [],
                    "prefix_list_ids": [],
                    "security_groups": [],
                    "self": False,
                }
                for port in (80, 443)
            ],
        },
        "aws_instance.gpu": {
            "instance_type": "g6.xlarge",
            "ami": ami,
            "availability_zone": az,
            "associate_public_ip_address": True,
            "instance_initiated_shutdown_behavior": "terminate",
            "root_block_device": [
                {
                    "volume_type": "gp3",
                    "volume_size": 100,
                    "encrypted": True,
                    "delete_on_termination": True,
                }
            ],
            "metadata_options": [
                {
                    "http_endpoint": "enabled",
                    "http_tokens": "required",
                    "http_put_response_hop_limit": 1,
                }
            ],
            "tags": tags,
            "volume_tags": tags,
            "subnet_id": None,
            "vpc_security_group_ids": [],
            "user_data": "SENTINEL_PRIVATE_USER_DATA",
        },
        "aws_scheduler_schedule.expiry": {
            "name": f"{PROJECT}-gpu-ec2",
            "group_name": f"{PROJECT}-gpu-ec2",
            "schedule_expression": f"at({expiry[:19]})",
            "schedule_expression_timezone": "UTC",
            "state": "ENABLED",
            "flexible_time_window": [{"mode": "OFF"}],
            "target": [
                {"arn": "arn:aws:scheduler:::aws-sdk:ec2:terminateInstances"}
            ],
        },
        "aws_iam_role_policy_attachment.ssm_core": {
            "policy_arn": "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
        },
    }
    changes = [
        {
            "address": address,
            "mode": "managed",
            "change": {
                "actions": ["create"],
                "after": {
                    **after_by_address.get(address, {}),
                    **({"tags": tags} if address in TAGGED_ADDRESSES else {}),
                },
            },
        }
        for address in sorted(EXPECTED_ADDRESSES)
    ]
    return json.dumps(
        {
            "resource_changes": changes,
            "configuration": {
                "root_module": {
                    "resources": [
                        {
                            "address": "aws_internet_gateway.gpu",
                            "mode": "managed",
                            "expressions": {
                                "vpc_id": {"references": ["aws_vpc.gpu.id", "aws_vpc.gpu"]}
                            },
                        },
                        {
                            "address": "aws_subnet.gpu",
                            "mode": "managed",
                            "expressions": {
                                "vpc_id": {"references": ["aws_vpc.gpu.id", "aws_vpc.gpu"]}
                            },
                        },
                        {
                            "address": "aws_route_table.gpu",
                            "mode": "managed",
                            "expressions": {
                                "vpc_id": {"references": ["aws_vpc.gpu.id", "aws_vpc.gpu"]},
                                "route": [
                                    {
                                        "cidr_block": {"constant_value": "0.0.0.0/0"},
                                        "gateway_id": {
                                            "references": [
                                                "aws_internet_gateway.gpu.id",
                                                "aws_internet_gateway.gpu",
                                            ]
                                        },
                                    }
                                ],
                            },
                        },
                        {
                            "address": "aws_route_table_association.gpu",
                            "mode": "managed",
                            "expressions": {
                                "subnet_id": {
                                    "references": ["aws_subnet.gpu.id", "aws_subnet.gpu"]
                                },
                                "route_table_id": {
                                    "references": [
                                        "aws_route_table.gpu.id",
                                        "aws_route_table.gpu",
                                    ]
                                },
                            },
                        },
                        {
                            "address": "aws_security_group.gpu",
                            "mode": "managed",
                            "expressions": {
                                "vpc_id": {"references": ["aws_vpc.gpu.id", "aws_vpc.gpu"]}
                            },
                        },
                        {
                            "address": "aws_instance.gpu",
                            "mode": "managed",
                            "expressions": {
                                "subnet_id": {
                                    "references": ["aws_subnet.gpu.id", "aws_subnet.gpu"]
                                },
                                "vpc_security_group_ids": {
                                    "references": [
                                        "aws_security_group.gpu.id",
                                        "aws_security_group.gpu",
                                    ]
                                },
                            },
                        },
                        {
                            "address": "aws_scheduler_schedule.expiry",
                            "mode": "managed",
                            "expressions": {
                                "target": [
                                    {
                                        "arn": {
                                            "constant_value": "arn:aws:scheduler:::aws-sdk:ec2:terminateInstances"
                                        },
                                        "role_arn": {
                                            "references": [
                                                "aws_iam_role.expiry.arn",
                                                "aws_iam_role.expiry",
                                            ]
                                        },
                                        "input": {
                                            "references": [
                                                "aws_instance.gpu.id",
                                                "aws_instance.gpu",
                                            ]
                                        },
                                    }
                                ]
                            },
                        },
                        {
                            "address": "aws_iam_role_policy.expiry",
                            "mode": "managed",
                            "expressions": {
                                "role": {
                                    "references": [
                                        "aws_iam_role.expiry.id",
                                        "aws_iam_role.expiry",
                                    ]
                                },
                                "policy": {
                                    "references": [
                                        "aws_instance.gpu.arn",
                                        "aws_instance.gpu",
                                    ]
                                },
                            },
                        },
                    ]
                }
            },
        }
    )


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
        f"if args[:2] == ['sts', 'get-caller-identity']: print(os.getenv('FAKE_AWS_ACCOUNT', {EXPECTED_ACCOUNT!r}))\n"
        "elif args[:2] == ['ec2', 'describe-images']: print(os.getenv('FAKE_AMI_METADATA', '099720109477 ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20261120 x86_64 available'))\n"
        "elif args[:2] == ['service-quotas', 'get-service-quota']: print(os.getenv('FAKE_AWS_QUOTA', '4'))\n"
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
        "args = sys.argv[1:]\n"
        "if 'show' in args and '-json' in args: print(os.environ['FAKE_TERRAFORM_PLAN_JSON'])\n"
        "for arg in args:\n"
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
    env["GPU_EC2_UBUNTU_AMI_ID"] = "ami-0a951420c495183dc"
    expiry = datetime.now(UTC) + timedelta(hours=6)
    env["GPU_EC2_EXPIRES_AT"] = expiry.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    env["FAKE_TERRAFORM_PLAN_JSON"] = _safe_plan_json(
        env["GPU_EC2_UBUNTU_AMI_ID"], env["GPU_EC2_AZ"], env["GPU_EC2_EXPIRES_AT"]
    )
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
    assert "describe-images --image-ids ami-0a951420c495183dc" in aws_log.read_text(encoding="utf-8")
    plan_calls = terraform_log.read_text(encoding="utf-8").splitlines()
    plan_profiles = [line.split()[0] for line in plan_calls]
    assert plan_profiles == ["ai-platform-pilot-key"] * 3
    assert "backend-config=dynamodb_table=multi-tenant-ai-inference-platform-pilot-terraform-locks" in plan_calls[0]
    assert "backend-config=use_lockfile=true" in plan_calls[0]
    assert any("ubuntu_ami_id=ami-0a951420c495183dc" in line for line in terraform_log.read_text(encoding="utf-8").splitlines())
    assert "14 create, 0 update, 0 delete" in planned.stdout
    assert "SENTINEL_PRIVATE_USER_DATA" not in planned.stdout + planned.stderr

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
    assert profiles == ["ai-platform-pilot-key"] * 5
    assert terraform_log.read_text(encoding="utf-8").count(" show -json ") == 2
    assert "SENTINEL_PRIVATE_USER_DATA" not in applied.stdout + applied.stderr


def test_apply_rejects_unsafe_saved_plan_after_checksum_and_preflight(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    plan_file = tmp_path / "gpu-ec2.tfplan"
    plan_file.write_bytes(b"fake saved plan")
    env = _subprocess_env(bin_dir)
    env["GPU_EC2_CONFIRM"] = "apply"
    env["GPU_EC2_PLAN_FILE"] = str(plan_file)
    env["GPU_EC2_PLAN_SHA256"] = hashlib.sha256(plan_file.read_bytes()).hexdigest()
    plan = json.loads(env["FAKE_TERRAFORM_PLAN_JSON"])
    next(
        item["change"]["after"]
        for item in plan["resource_changes"]
        if item["address"] == "aws_instance.gpu"
    )["instance_type"] = "g6.2xlarge"
    env["FAKE_TERRAFORM_PLAN_JSON"] = json.dumps(plan)

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-apply.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "single-L4 instance settings" in result.stderr
    calls = terraform_log.read_text(encoding="utf-8").splitlines()
    assert any(" show -json " in call for call in calls)
    assert not any(" apply " in call for call in calls)
    assert "SENTINEL_PRIVATE_USER_DATA" not in result.stdout + result.stderr


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
    assert "outside this verifier's scope" in result.stdout
    assert "scheduler list-schedules" not in aws_log.read_text(encoding="utf-8")


def test_preflight_stops_before_other_aws_calls_for_wrong_account(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    env = _subprocess_env(bin_dir)
    env["FAKE_AWS_ACCOUNT"] = "000000000000"

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-preflight.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "authenticated account does not match" in result.stderr
    assert len(aws_log.read_text(encoding="utf-8").splitlines()) == 1
    assert not terraform_log.exists()


def test_preflight_stops_before_type_lookup_when_quota_is_too_small(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    env = _subprocess_env(bin_dir)
    env["FAKE_AWS_QUOTA"] = "0"

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-preflight.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "quota is 0 vCPUs; 4 are required" in result.stderr
    calls = aws_log.read_text(encoding="utf-8").splitlines()
    assert len(calls) == 3
    assert "service-quotas get-service-quota" in calls[2]
    assert not terraform_log.exists()


@pytest.mark.parametrize(
    "metadata",
    [
        "000000000000 ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20261120 x86_64 available",
        "099720109477 ubuntu/images/hvm-ssd-gp2/ubuntu-noble-24.04-amd64-server-20261120 x86_64 available",
        "099720109477 ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20261120 arm64 available",
        "099720109477 ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20261120 x86_64 deregistered",
    ],
    ids=["wrong-owner", "wrong-name", "wrong-architecture", "unavailable"],
)
def test_preflight_rejects_untrusted_or_unusable_ami(tmp_path: Path, metadata: str) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    env = _subprocess_env(bin_dir)
    env["FAKE_AMI_METADATA"] = metadata

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-preflight.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "AMI must be an available Canonical Ubuntu 24.04 amd64 server image" in result.stderr
    calls = aws_log.read_text(encoding="utf-8").splitlines()
    assert len(calls) == 2
    assert "ec2 describe-images" in calls[1]
    assert not terraform_log.exists()


def test_apply_without_explicit_confirmation_never_calls_aws_or_terraform(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    env = _subprocess_env(bin_dir)

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-apply.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "refusing apply" in result.stderr
    assert not aws_log.exists()
    assert not terraform_log.exists()


def test_apply_rejects_a_changed_plan_before_aws_preflight(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    plan_file = tmp_path / "changed.tfplan"
    plan_file.write_bytes(b"plan that differs from reviewed bytes")
    env = _subprocess_env(bin_dir)
    env["GPU_EC2_CONFIRM"] = "apply"
    env["GPU_EC2_PLAN_FILE"] = str(plan_file)
    env["GPU_EC2_PLAN_SHA256"] = "not-the-plan-digest"

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-apply.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "saved plan checksum does not match" in result.stderr
    assert not aws_log.exists()
    assert not terraform_log.exists()


def test_destroy_apply_requires_explicit_confirmation_before_aws(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    env = _subprocess_env(bin_dir)

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-destroy-apply.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "refusing destroy" in result.stderr
    assert not aws_log.exists()
    assert not terraform_log.exists()


def test_destroy_apply_rejects_a_changed_plan_before_aws(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    plan_file = tmp_path / "changed-destroy.tfplan"
    plan_file.write_bytes(b"destroy plan differs from reviewed bytes")
    env = _subprocess_env(bin_dir)
    env["GPU_EC2_CONFIRM"] = "destroy"
    env["GPU_EC2_DESTROY_PLAN_FILE"] = str(plan_file)
    env["GPU_EC2_DESTROY_PLAN_SHA256"] = "not-the-plan-digest"

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-destroy-apply.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "saved-plan checksum does not match" in result.stderr
    assert not aws_log.exists()
    assert not terraform_log.exists()


def test_destroy_apply_checks_account_before_terraform(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    plan_file = tmp_path / "destroy.tfplan"
    plan_file.write_bytes(b"reviewed destroy plan")
    env = _subprocess_env(bin_dir)
    env["GPU_EC2_CONFIRM"] = "destroy"
    env["GPU_EC2_DESTROY_PLAN_FILE"] = str(plan_file)
    env["GPU_EC2_DESTROY_PLAN_SHA256"] = hashlib.sha256(plan_file.read_bytes()).hexdigest()
    env["FAKE_AWS_ACCOUNT"] = "000000000000"

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-destroy-apply.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "authenticated account does not match" in result.stderr
    assert len(aws_log.read_text(encoding="utf-8").splitlines()) == 1
    assert not terraform_log.exists()


def test_destroy_plan_uses_only_the_destroy_operation(tmp_path: Path) -> None:
    bin_dir, aws_log, terraform_log = _fake_cli_bin(tmp_path)
    plan_file = tmp_path / "destroy.tfplan"
    env = _subprocess_env(bin_dir)
    env["GPU_EC2_DESTROY_PLAN_FILE"] = str(plan_file)

    result = subprocess.run(
        [str(REPO_ROOT / "scripts/gpu-ec2-destroy-plan.sh")],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert plan_file.read_bytes() == b"fake saved plan"
    terraform_calls = terraform_log.read_text(encoding="utf-8").splitlines()
    assert len(terraform_calls) == 2
    assert "backend-config=dynamodb_table=multi-tenant-ai-inference-platform-pilot-terraform-locks" in terraform_calls[0]
    assert "backend-config=use_lockfile=true" in terraform_calls[0]
    assert "plan -destroy" in terraform_calls[1]
    assert terraform_calls[1].split()[0] == "ai-platform-pilot-key"
    assert "ubuntu_ami_id=ami-0a951420c495183dc" in terraform_calls[1]
