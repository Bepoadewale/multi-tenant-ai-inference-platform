"""Reject unsafe GPU plans and print a small, non-sensitive review summary."""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

PROJECT = "multi-tenant-ai-inference-platform"
EXPECTED_ADDRESSES = {
    "aws_vpc.gpu",
    "aws_internet_gateway.gpu",
    "aws_subnet.gpu",
    "aws_route_table.gpu",
    "aws_route_table_association.gpu",
    "aws_security_group.gpu",
    "aws_iam_role.instance",
    "aws_iam_role_policy_attachment.ssm_core",
    "aws_iam_instance_profile.gpu",
    "aws_instance.gpu",
    "aws_scheduler_schedule_group.gpu",
    "aws_iam_role.expiry",
    "aws_iam_role_policy.expiry",
    "aws_scheduler_schedule.expiry",
}
TAGGED_ADDRESSES = {
    "aws_vpc.gpu",
    "aws_internet_gateway.gpu",
    "aws_subnet.gpu",
    "aws_route_table.gpu",
    "aws_security_group.gpu",
    "aws_iam_role.instance",
    "aws_iam_instance_profile.gpu",
    "aws_instance.gpu",
    "aws_scheduler_schedule_group.gpu",
    "aws_iam_role.expiry",
}


def _nested(after: dict[str, Any], key: str) -> dict[str, Any]:
    value = after.get(key)
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    return value if isinstance(value, dict) else {}


def validate(
    plan: dict[str, Any],
    *,
    expected_ami: str,
    expected_az: str,
    expected_expiry: str,
) -> list[dict[str, Any]]:
    if not isinstance(plan, dict):
        raise ValueError("Terraform JSON must be an object")
    if not re.fullmatch(r"us-east-1[a-z]", expected_az):
        raise ValueError("reviewed Availability Zone is outside us-east-1")
    raw_changes = plan.get("resource_changes")
    if not isinstance(raw_changes, list) or any(not isinstance(item, dict) for item in raw_changes):
        raise ValueError("Terraform JSON must contain a resource_changes list")

    changes = [item for item in raw_changes if item.get("mode", "managed") == "managed"]
    addresses = {item.get("address") for item in changes}
    if addresses != EXPECTED_ADDRESSES or len(changes) != len(EXPECTED_ADDRESSES):
        raise ValueError("saved plan does not contain exactly the 14 approved GPU-root resources")
    if any(
        not isinstance(item.get("change"), dict)
        or item["change"].get("actions") != ["create"]
        for item in changes
    ):
        raise ValueError("initial GPU plan must contain creates only")

    after = {}
    for item in changes:
        resource_after = item["change"].get("after")
        if not isinstance(resource_after, dict):
            raise ValueError("Terraform JSON resource values are missing or invalid")
        after[item["address"]] = resource_after
    instance = after["aws_instance.gpu"]
    if (
        instance.get("instance_type") != "g6.xlarge"
        or instance.get("ami") != expected_ami
        or instance.get("availability_zone") != expected_az
        or instance.get("instance_initiated_shutdown_behavior") != "terminate"
    ):
        raise ValueError("saved plan does not match the reviewed single-L4 instance settings")

    root = _nested(instance, "root_block_device")
    if not (
        100 <= root.get("volume_size", 0) <= 120
        and root.get("volume_type") == "gp3"
        and root.get("encrypted") is True
        and root.get("delete_on_termination") is True
    ):
        raise ValueError("saved plan root volume is outside the encrypted 100-120 GiB gp3 limit")

    metadata = _nested(instance, "metadata_options")
    if (
        metadata.get("http_endpoint") != "enabled"
        or metadata.get("http_tokens") != "required"
        or metadata.get("http_put_response_hop_limit") != 1
    ):
        raise ValueError("saved plan must require IMDSv2 and a one-hop metadata response limit")

    attachment = after["aws_iam_role_policy_attachment.ssm_core"]
    if attachment.get("policy_arn") != "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore":
        raise ValueError("saved plan must attach only the documented Systems Manager core policy")

    required_tags = {
        "project": PROJECT,
        "environment": "gpu-ec2",
        "managed_by": "terraform",
        "owner": "bepoadewale",
        "cost_scope": "gpu-ec2",
        "expires_at": expected_expiry,
        "data_class": "synthetic-only",
    }
    resource_tags = {**required_tags, "Name": f"{PROJECT}-gpu-ec2"}
    for address in TAGGED_ADDRESSES:
        if after[address].get("tags") != resource_tags:
            raise ValueError(f"saved plan resource {address} does not have the required project tags")
    required_tags = resource_tags
    for key in ("tags", "volume_tags"):
        tags = instance.get(key) or {}
        if any(tags.get(name) != value for name, value in required_tags.items()):
            raise ValueError(f"saved plan instance {key} do not include the required project tags")

    security = after["aws_security_group.gpu"]
    if security.get("ingress") not in (None, []):
        raise ValueError("saved plan must not create inbound security-group rules")
    egress = security.get("egress") or []
    ports = {
        rule.get("from_port")
        for rule in egress
        if rule.get("protocol") == "tcp"
        and rule.get("from_port") == rule.get("to_port")
        and rule.get("cidr_blocks") == ["0.0.0.0/0"]
        and not rule.get("ipv6_cidr_blocks")
        and not rule.get("prefix_list_ids")
        and not rule.get("security_groups")
        and not rule.get("self", False)
    }
    if len(egress) != 2 or ports != {80, 443}:
        raise ValueError("saved plan egress must contain only TCP 80 and 443 to IPv4")

    schedule = after["aws_scheduler_schedule.expiry"]
    expected_schedule = f"at({expected_expiry[:19]})"
    if (
        schedule.get("schedule_expression") != expected_schedule
        or schedule.get("schedule_expression_timezone") != "UTC"
        or schedule.get("state") != "ENABLED"
        or _nested(schedule, "flexible_time_window").get("mode") != "OFF"
    ):
        raise ValueError("saved plan expiry schedule does not match the exact reviewed UTC deadline")

    return changes


def main() -> int:
    try:
        expected_ami = os.environ["GPU_EC2_UBUNTU_AMI_ID"]
        expected_az = os.environ["GPU_EC2_AZ"]
        expected_expiry = os.environ["GPU_EC2_EXPIRES_AT"]
        plan = json.load(sys.stdin)
        changes = validate(
            plan,
            expected_ami=expected_ami,
            expected_az=expected_az,
            expected_expiry=expected_expiry,
        )
    except (
        AttributeError,
        IndexError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        print(f"refusing: {error}", file=sys.stderr)
        return 2

    print("GPU plan summary (private plan values omitted)")
    print(f"Actions: {len(changes)} create, 0 update, 0 delete")
    print(f"Instance: one g6.xlarge in {expected_az}; Ubuntu AMI matches reviewed input")
    print("Root disk: encrypted gp3, 100-120 GiB, deleted with the instance")
    print("Network: no inbound rules; outbound TCP 80 and 443 only")
    print("Metadata: IMDSv2 required; expiry: exact reviewed UTC deadline")
    for address in sorted(EXPECTED_ADDRESSES):
        print(f"- create {address}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
