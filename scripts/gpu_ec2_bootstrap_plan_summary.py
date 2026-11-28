"""Validate and safely summarize the exact bootstrap plan without showing its email."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

PROJECT = "multi-tenant-ai-inference-platform"
PREFIX = f"{PROJECT}-pilot"
EXPECTED = {
    "aws_budgets_budget.monthly_pilot",
    "aws_dynamodb_table.terraform_locks",
    "aws_s3_bucket.terraform_state",
    "aws_s3_bucket_ownership_controls.terraform_state",
    "aws_s3_bucket_public_access_block.terraform_state",
    "aws_s3_bucket_server_side_encryption_configuration.terraform_state",
    "aws_s3_bucket_versioning.terraform_state",
}


def _block(after: dict[str, Any], key: str) -> dict[str, Any]:
    value = after.get(key)
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    if isinstance(value, dict):
        return value
    return {}


def validate(plan: dict[str, Any], expected_account: str) -> list[dict[str, Any]]:
    changes = [
        item
        for item in plan.get("resource_changes", [])
        if item.get("mode", "managed") == "managed"
    ]
    addresses = {item.get("address") for item in changes}
    if addresses != EXPECTED or len(changes) != len(EXPECTED):
        raise ValueError("plan does not contain exactly the seven approved bootstrap resources")
    if any(item.get("change", {}).get("actions") != ["create"] for item in changes):
        raise ValueError("bootstrap plan must contain creates only")

    after_by_address = {
        item["address"]: item.get("change", {}).get("after") or {}
        for item in changes
    }
    tags = after_by_address["aws_s3_bucket.terraform_state"].get("tags") or {}
    if tags.get("project") != PROJECT or tags.get("environment") != "pilot":
        raise ValueError("state bucket is missing required project tags")

    bucket = after_by_address["aws_s3_bucket.terraform_state"]
    if bucket.get("bucket") != f"{PROJECT}-tfstate-{expected_account}":
        raise ValueError("state bucket name does not match the expected account")
    if bucket.get("force_destroy") is not False:
        raise ValueError("state bucket must not enable force_destroy")

    public = after_by_address["aws_s3_bucket_public_access_block.terraform_state"]
    if not all(
        public.get(name) is True
        for name in (
            "block_public_acls",
            "block_public_policy",
            "ignore_public_acls",
            "restrict_public_buckets",
        )
    ):
        raise ValueError("state bucket must block all public access")

    ownership = _block(
        after_by_address["aws_s3_bucket_ownership_controls.terraform_state"], "rule"
    )
    if ownership.get("object_ownership") != "BucketOwnerEnforced":
        raise ValueError("state bucket must enforce bucket-owner ownership")

    versioning = _block(
        after_by_address["aws_s3_bucket_versioning.terraform_state"],
        "versioning_configuration",
    )
    if versioning.get("status") != "Enabled":
        raise ValueError("state bucket versioning must be enabled")

    encryption_rule = _block(
        after_by_address["aws_s3_bucket_server_side_encryption_configuration.terraform_state"],
        "rule",
    )
    encryption = _block(encryption_rule, "apply_server_side_encryption_by_default")
    if encryption.get("sse_algorithm") != "AES256":
        raise ValueError("state bucket must use server-side encryption")

    table = after_by_address["aws_dynamodb_table.terraform_locks"]
    if (
        table.get("name") != f"{PREFIX}-terraform-locks"
        or table.get("billing_mode") != "PAY_PER_REQUEST"
        or table.get("hash_key") != "LockID"
    ):
        raise ValueError("lock table name or low-cost key configuration is unexpected")

    budget = after_by_address["aws_budgets_budget.monthly_pilot"]
    if (
        budget.get("name") != f"{PREFIX}-monthly-cost"
        or budget.get("budget_type") != "COST"
        or budget.get("limit_unit") != "USD"
        or budget.get("time_unit") != "MONTHLY"
    ):
        raise ValueError("monthly Budget identity or unit is unexpected")
    try:
        amount = float(budget["limit_amount"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("monthly Budget limit is missing or invalid") from exc
    if not 0 < amount <= 25:
        raise ValueError("monthly Budget alert must be greater than zero and at most USD 25")

    notifications = budget.get("notification") or []
    thresholds: set[int] = set()
    for notification in notifications:
        if (
            notification.get("notification_type") != "ACTUAL"
            or notification.get("comparison_operator") != "GREATER_THAN"
            or notification.get("threshold_type") != "PERCENTAGE"
        ):
            raise ValueError("Budget notifications must be actual-cost percentage alerts")
        recipients = notification.get("subscriber_email_addresses") or []
        if len(recipients) != 1:
            raise ValueError("each Budget alert must have exactly one email recipient")
        recipient = recipients[0]
        if (
            not isinstance(recipient, str)
            or not recipient
            or "@" not in recipient
            or "." not in recipient.rsplit("@", 1)[-1]
            or recipient.lower().endswith(".invalid")
        ):
            raise ValueError("Budget alert recipient is invalid")
        thresholds.add(int(notification.get("threshold", -1)))
    if thresholds != {50, 80, 100} or len(notifications) != 3:
        raise ValueError("Budget alerts must be configured at 50, 80, and 100 percent")

    return changes


def main() -> int:
    try:
        expected_account = os.environ["EXPECTED_AWS_ACCOUNT_ID"]
        plan = json.load(sys.stdin)
        changes = validate(plan, expected_account)
    except (KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2

    amount = next(
        float(item["change"]["after"]["limit_amount"])
        for item in changes
        if item["address"] == "aws_budgets_budget.monthly_pilot"
    )
    print("Bootstrap plan summary (email recipient hidden)")
    print("Actions: 7 create, 0 update, 0 delete")
    print("State bucket: account-scoped, public access blocked, AES256 encrypted, versioned")
    print("State lock table: PAY_PER_REQUEST, LockID key")
    print(f"Monthly actual-cost alert budget: USD {amount:g}; recipient configured")
    for address in sorted(EXPECTED):
        print(f"- create {address}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
