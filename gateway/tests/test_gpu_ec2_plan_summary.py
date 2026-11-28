"""Tests for the exact, sanitized GPU Terraform plan review."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.gpu_ec2_plan_summary import EXPECTED_ADDRESSES, TAGGED_ADDRESSES, validate

REPO_ROOT = Path(__file__).resolve().parents[2]
ACCOUNT = "123456789012"
AMI = "ami-0123456789abcdef0"
AZ = "us-east-1a"
EXPIRY = "2026-11-28T18:00:00Z"
TAGS = {
    "Name": "multi-tenant-ai-inference-platform-gpu-ec2",
    "project": "multi-tenant-ai-inference-platform",
    "environment": "gpu-ec2",
    "managed_by": "terraform",
    "owner": "bepoadewale",
    "cost_scope": "gpu-ec2",
    "expires_at": EXPIRY,
    "data_class": "synthetic-only",
}


def _plan() -> dict:
    after_by_address = {
        "aws_vpc.gpu": {
            "cidr_block": "10.74.0.0/16",
            "enable_dns_support": True,
            "enable_dns_hostnames": True,
        },
        "aws_internet_gateway.gpu": {},
        "aws_subnet.gpu": {
            "cidr_block": "10.74.1.0/24",
            "availability_zone": AZ,
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
            "ami": AMI,
            "availability_zone": AZ,
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
            "tags": TAGS,
            "volume_tags": TAGS,
            "subnet_id": None,
            "vpc_security_group_ids": [],
            "user_data": "SENTINEL_PRIVATE_USER_DATA",
        },
        "aws_scheduler_schedule.expiry": {
            "name": "multi-tenant-ai-inference-platform-gpu-ec2",
            "group_name": "multi-tenant-ai-inference-platform-gpu-ec2",
            "schedule_expression": "at(2026-11-28T18:00:00)",
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
    changes = []
    for address in sorted(EXPECTED_ADDRESSES):
        after = after_by_address.get(address, {})
        if address in TAGGED_ADDRESSES:
            after["tags"] = TAGS
        changes.append(
            {
                "address": address,
                "mode": "managed",
                "change": {"actions": ["create"], "after": after},
            }
        )
    return {
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


def _validate(plan: dict) -> list[dict]:
    return validate(
        plan,
        expected_ami=AMI,
        expected_az=AZ,
        expected_expiry=EXPIRY,
    )


def _change(plan: dict, address: str) -> dict:
    return next(item["change"]["after"] for item in plan["resource_changes"] if item["address"] == address)


def _expressions(plan: dict, address: str) -> dict:
    return next(
        item["expressions"]
        for item in plan["configuration"]["root_module"]["resources"]
        if item["address"] == address
    )


def test_accepts_exact_safe_single_l4_plan() -> None:
    changes = _validate(_plan())
    assert len(changes) == 14
    assert {item["address"] for item in changes} == EXPECTED_ADDRESSES


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda plan: plan["resource_changes"].pop(), "exactly the 14"),
        (
            lambda plan: plan["resource_changes"].append(
                {
                    "address": "aws_db_instance.unexpected",
                    "mode": "managed",
                    "change": {"actions": ["create"], "after": {}},
                }
            ),
            "exactly the 14",
        ),
        (
            lambda plan: plan["resource_changes"][0]["change"].update(actions=["delete", "create"]),
            "creates only",
        ),
        (
            lambda plan: _change(plan, "aws_instance.gpu").update(ami="ami-unapproved"),
            "instance settings",
        ),
        (
            lambda plan: _change(plan, "aws_instance.gpu").update(
                associate_public_ip_address=False
            ),
            "instance settings",
        ),
        (
            lambda plan: _change(plan, "aws_instance.gpu")["root_block_device"][0].update(
                encrypted=False
            ),
            "encrypted 100-120 GiB",
        ),
        (
            lambda plan: _change(plan, "aws_instance.gpu").update(instance_type="g6.2xlarge"),
            "instance settings",
        ),
        (
            lambda plan: _change(plan, "aws_instance.gpu")["metadata_options"][0].update(
                http_put_response_hop_limit=2
            ),
            "one-hop metadata",
        ),
        (
            lambda plan: _change(plan, "aws_security_group.gpu").update(
                ingress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}]
            ),
            "inbound",
        ),
        (
            lambda plan: _change(plan, "aws_security_group.gpu")["egress"].append(
                {
                    "protocol": "-1",
                    "from_port": 0,
                    "to_port": 0,
                    "cidr_blocks": ["0.0.0.0/0"],
                }
            ),
            "egress",
        ),
        (
            lambda plan: _change(plan, "aws_instance.gpu").update(
                tags={**TAGS, "owner": "someone-else"}
            ),
            "required project tags",
        ),
        (
            lambda plan: _change(plan, "aws_route_table.gpu").update(
                tags={**TAGS, "cost_scope": "other-project"}
            ),
            "required project tags",
        ),
        (
            lambda plan: _change(plan, "aws_scheduler_schedule.expiry").update(
                schedule_expression="at(2026-11-28T20:00:00)"
            ),
            "exact UTC deadline",
        ),
        (
            lambda plan: _change(plan, "aws_scheduler_schedule.expiry")["target"][0].update(
                arn="arn:aws:scheduler:::aws-sdk:lambda:invoke"
            ),
            "TerminateInstances",
        ),
        (
            lambda plan: _change(plan, "aws_scheduler_schedule.expiry").update(
                group_name="unrelated"
            ),
            "project schedule group",
        ),
    ],
)
def test_rejects_unsafe_plan_mutations(mutation, message: str) -> None:
    plan = deepcopy(_plan())
    mutation(plan)
    with pytest.raises(ValueError, match=message):
        _validate(plan)


@pytest.mark.parametrize(
    "address, expression, references, message",
    [
        (
            "aws_scheduler_schedule.expiry",
            "role_arn",
            ["aws_iam_role.instance.arn", "aws_iam_role.instance"],
            "project-only termination role",
        ),
        (
            "aws_scheduler_schedule.expiry",
            "input",
            ["aws_instance.other.id", "aws_instance.other"],
            "only the project GPU instance",
        ),
        (
            "aws_iam_role_policy.expiry",
            "policy",
            ["aws_instance.other.arn", "aws_instance.other"],
            "only the project GPU instance",
        ),
    ],
)
def test_rejects_expiry_bindings_to_other_resources(
    address: str, expression: str, references: list[str], message: str
) -> None:
    plan = _plan()
    resource = next(
        item
        for item in plan["configuration"]["root_module"]["resources"]
        if item["address"] == address
    )
    target_expression = resource["expressions"]
    if address == "aws_scheduler_schedule.expiry":
        target_expression["target"][0][expression] = {"references": references}
    else:
        target_expression[expression] = {"references": references}

    with pytest.raises(ValueError, match=message):
        _validate(plan)


def test_rejects_schedule_configuration_for_another_action() -> None:
    plan = _plan()
    schedule = next(
        item
        for item in plan["configuration"]["root_module"]["resources"]
        if item["address"] == "aws_scheduler_schedule.expiry"
    )
    schedule["expressions"]["target"][0]["arn"]["constant_value"] = (
        "arn:aws:scheduler:::aws-sdk:lambda:invoke"
    )

    with pytest.raises(ValueError, match="configuration must call EC2 TerminateInstances"):
        _validate(plan)


@pytest.mark.parametrize(
    "address, argument, references, message",
    [
        (
            "aws_subnet.gpu",
            "vpc_id",
            ["aws_vpc.other.id", "aws_vpc.other"],
            "network aws_subnet.gpu.vpc_id",
        ),
        (
            "aws_instance.gpu",
            "subnet_id",
            ["aws_subnet.other.id", "aws_subnet.other"],
            "network aws_instance.gpu.subnet_id",
        ),
        (
            "aws_route_table_association.gpu",
            "route_table_id",
            ["aws_route_table.other.id", "aws_route_table.other"],
            "network aws_route_table_association.gpu.route_table_id",
        ),
    ],
)
def test_rejects_network_bindings_to_other_resources(
    address: str, argument: str, references: list[str], message: str
) -> None:
    plan = _plan()
    _expressions(plan, address)[argument] = {"references": references}

    with pytest.raises(ValueError, match=message):
        _validate(plan)


def test_rejects_subnet_outside_the_reviewed_project_range() -> None:
    plan = _plan()
    _change(plan, "aws_subnet.gpu").update(cidr_block="10.74.2.0/24")

    with pytest.raises(ValueError, match="approved public GPU subnet"):
        _validate(plan)


def test_cli_prints_safe_summary_without_user_data() -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "GPU_EC2_UBUNTU_AMI_ID": AMI,
            "GPU_EC2_AZ": AZ,
            "GPU_EC2_EXPIRES_AT": EXPIRY,
        }
    )
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/gpu_ec2_plan_summary.py")],
        input=json.dumps(_plan()),
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "14 create, 0 update, 0 delete" in result.stdout
    assert "SENTINEL_PRIVATE_USER_DATA" not in result.stdout + result.stderr


def test_rejects_plan_with_unreviewed_instance_inputs_before_summary() -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "GPU_EC2_UBUNTU_AMI_ID": "ami-11111111111111111",
            "GPU_EC2_AZ": AZ,
            "GPU_EC2_EXPIRES_AT": EXPIRY,
        }
    )
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/gpu_ec2_plan_summary.py")],
        input=json.dumps(_plan()),
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )
    assert result.returncode == 2
    assert "instance settings" in result.stderr
    assert "SENTINEL_PRIVATE_USER_DATA" not in result.stdout + result.stderr


def test_rejects_availability_zone_outside_exact_us_east_1_shape() -> None:
    with pytest.raises(ValueError, match="Availability Zone"):
        validate(_plan(), expected_ami=AMI, expected_az="us-east-10a", expected_expiry=EXPIRY)


@pytest.mark.parametrize("plan", [[], {"resource_changes": [None]}])
def test_rejects_malformed_plan_json_shapes(plan) -> None:
    with pytest.raises(ValueError, match="Terraform JSON"):
        validate(plan, expected_ami=AMI, expected_az=AZ, expected_expiry=EXPIRY)
