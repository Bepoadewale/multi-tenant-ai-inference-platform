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


def _resource_expressions(plan: dict[str, Any], address: str) -> dict[str, Any]:
    configuration = plan.get("configuration")
    root_module = configuration.get("root_module") if isinstance(configuration, dict) else None
    resources = root_module.get("resources") if isinstance(root_module, dict) else None
    if not isinstance(resources, list):
        raise ValueError("saved plan configuration expressions are missing")
    matches = [
        resource
        for resource in resources
        if isinstance(resource, dict)
        and resource.get("mode") == "managed"
        and resource.get("address") == address
    ]
    if len(matches) != 1 or not isinstance(matches[0].get("expressions"), dict):
        raise ValueError(f"saved plan configuration for {address} is missing or ambiguous")
    return matches[0]["expressions"]


def _references(expression: Any) -> set[str]:
    if not isinstance(expression, dict):
        return set()
    references = expression.get("references")
    if not isinstance(references, list) or any(not isinstance(item, str) for item in references):
        return set()
    return set(references)


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
        or instance.get("associate_public_ip_address") is not True
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

    vpc = after["aws_vpc.gpu"]
    if (
        vpc.get("cidr_block") != "10.74.0.0/16"
        or vpc.get("enable_dns_support") is not True
        or vpc.get("enable_dns_hostnames") is not True
    ):
        raise ValueError("saved plan VPC does not match the isolated GPU network")
    subnet = after["aws_subnet.gpu"]
    if (
        subnet.get("cidr_block") != "10.74.1.0/24"
        or subnet.get("availability_zone") != expected_az
        or subnet.get("map_public_ip_on_launch") is not True
    ):
        raise ValueError("saved plan subnet does not match the approved public GPU subnet")
    route_table = after["aws_route_table.gpu"]
    routes = route_table.get("route")
    if (
        not isinstance(routes, list)
        or len(routes) != 1
        or not isinstance(routes[0], dict)
        or routes[0].get("cidr_block") != "0.0.0.0/0"
    ):
        raise ValueError("saved plan route table must contain only the project internet route")
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

    vpc_id_references = {"aws_vpc.gpu.id", "aws_vpc.gpu"}
    network_bindings = (
        ("aws_internet_gateway.gpu", "vpc_id", vpc_id_references),
        ("aws_subnet.gpu", "vpc_id", vpc_id_references),
        ("aws_route_table.gpu", "vpc_id", vpc_id_references),
        ("aws_security_group.gpu", "vpc_id", vpc_id_references),
        (
            "aws_route_table_association.gpu",
            "subnet_id",
            {"aws_subnet.gpu.id", "aws_subnet.gpu"},
        ),
        (
            "aws_route_table_association.gpu",
            "route_table_id",
            {"aws_route_table.gpu.id", "aws_route_table.gpu"},
        ),
        ("aws_instance.gpu", "subnet_id", {"aws_subnet.gpu.id", "aws_subnet.gpu"}),
        (
            "aws_instance.gpu",
            "vpc_security_group_ids",
            {"aws_security_group.gpu.id", "aws_security_group.gpu"},
        ),
    )
    for address, argument, expected_references in network_bindings:
        expression = _resource_expressions(plan, address).get(argument)
        if _references(expression) != expected_references:
            raise ValueError(
                f"saved plan network {address}.{argument} is not bound to the project topology"
            )

    route_expressions = _resource_expressions(plan, "aws_route_table.gpu").get("route")
    if not isinstance(route_expressions, list) or len(route_expressions) != 1:
        raise ValueError("saved plan must configure exactly one internet route")
    route_gateway = route_expressions[0].get("gateway_id")
    if _references(route_gateway) != {"aws_internet_gateway.gpu.id", "aws_internet_gateway.gpu"}:
        raise ValueError("saved plan internet route must use the project internet gateway")

    schedule = after["aws_scheduler_schedule.expiry"]
    expected_schedule = f"at({expected_expiry[:19]})"
    target = _nested(schedule, "target")
    if (
        schedule.get("name") != f"{PROJECT}-gpu-ec2"
        or schedule.get("group_name") != f"{PROJECT}-gpu-ec2"
        or schedule.get("schedule_expression") != expected_schedule
        or schedule.get("schedule_expression_timezone") != "UTC"
        or schedule.get("state") != "ENABLED"
        or _nested(schedule, "flexible_time_window").get("mode") != "OFF"
        or target.get("arn") != "arn:aws:scheduler:::aws-sdk:ec2:terminateInstances"
    ):
        raise ValueError(
            "saved plan expiry must use the project schedule group and exact UTC deadline "
            "to invoke EC2 TerminateInstances"
        )

    # The EC2 ID and IAM role ARN are unknown until apply, so Terraform's planned
    # values cannot prove their relationship. Its machine-readable configuration
    # retains expression references; bind both schedule arguments to this exact
    # instance and the project's narrowly scoped expiry role.
    schedule_expressions = _resource_expressions(plan, "aws_scheduler_schedule.expiry")
    target_expressions = schedule_expressions.get("target")
    if not isinstance(target_expressions, list) or len(target_expressions) != 1:
        raise ValueError("saved plan expiry must contain one configured termination target")
    target_expression = target_expressions[0]
    if not isinstance(target_expression, dict):
        raise ValueError("saved plan expiry target configuration is invalid")
    expected_role_references = {"aws_iam_role.expiry.arn", "aws_iam_role.expiry"}
    expected_instance_references = {"aws_instance.gpu.id", "aws_instance.gpu"}
    target_arn_expression = target_expression.get("arn")
    if not isinstance(target_arn_expression, dict) or target_arn_expression.get(
        "constant_value"
    ) != "arn:aws:scheduler:::aws-sdk:ec2:terminateInstances":
        raise ValueError("saved plan expiry target configuration must call EC2 TerminateInstances")
    if _references(target_expression.get("role_arn")) != expected_role_references:
        raise ValueError("saved plan expiry target must use the project-only termination role")
    if _references(target_expression.get("input")) != expected_instance_references:
        raise ValueError("saved plan expiry target must reference only the project GPU instance")

    policy_expressions = _resource_expressions(plan, "aws_iam_role_policy.expiry")
    if _references(policy_expressions.get("role")) != {
        "aws_iam_role.expiry.id",
        "aws_iam_role.expiry",
    }:
        raise ValueError("saved plan expiry policy must attach to the project termination role")
    expected_instance_arn_references = {"aws_instance.gpu.arn", "aws_instance.gpu"}
    if _references(policy_expressions.get("policy")) != expected_instance_arn_references:
        raise ValueError("saved plan expiry policy must reference only the project GPU instance")

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
    print(
        "Network: one project subnet and gateway; no inbound rules; "
        "outbound TCP 80 and 443 only"
    )
    print("Metadata: IMDSv2 required; expiry: exact UTC deadline invokes EC2 TerminateInstances")
    for address in sorted(EXPECTED_ADDRESSES):
        print(f"- create {address}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
