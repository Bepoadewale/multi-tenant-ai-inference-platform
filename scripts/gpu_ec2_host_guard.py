"""Fail-closed identity checks for commands intended to run on the project L4 host."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from urllib.request import Request, urlopen

IMDS = "http://169.254.169.254/latest"
EXPECTED_INSTANCE_TYPE = "g6.xlarge"
EXPECTED_REGION = "us-east-1"


def instance_identity() -> dict[str, str]:
    token_request = Request(
        f"{IMDS}/api/token",
        data=b"",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        method="PUT",
    )
    with urlopen(token_request, timeout=2) as response:
        token = response.read().decode("utf-8")
    document_request = Request(
        f"{IMDS}/dynamic/instance-identity/document",
        headers={"X-aws-ec2-metadata-token": token},
    )
    with urlopen(document_request, timeout=2) as response:
        document = json.loads(response.read())
    return {
        "account_id": str(document.get("accountId", "")),
        "instance_id": str(document.get("instanceId", "")),
        "instance_type": str(document.get("instanceType", "")),
        "region": str(document.get("region", "")),
    }


def verify_host(
    *,
    expected_account_id: str | None = None,
    expected_instance_id: str | None = None,
    require_l4: bool = False,
) -> dict[str, str]:
    identity = instance_identity()
    expected_account_id = expected_account_id or os.getenv("EXPECTED_AWS_ACCOUNT_ID", "")
    expected_instance_id = expected_instance_id or os.getenv("GPU_EC2_INSTANCE_ID", "")
    if not expected_account_id or identity["account_id"] != expected_account_id:
        raise ValueError("host account does not match EXPECTED_AWS_ACCOUNT_ID")
    if not expected_instance_id or identity["instance_id"] != expected_instance_id:
        raise ValueError("host instance does not match GPU_EC2_INSTANCE_ID")
    if identity["region"] != EXPECTED_REGION:
        raise ValueError("GPU host must be in us-east-1")
    if identity["instance_type"] != EXPECTED_INSTANCE_TYPE:
        raise ValueError("GPU host must be the authorized g6.xlarge instance")
    if require_l4:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        devices = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if len(devices) != 1 or "L4" not in devices[0]:
            raise ValueError("expected exactly one visible NVIDIA L4")
        identity["gpu"] = devices[0]
    return identity


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-l4", action="store_true")
    args = parser.parse_args()
    try:
        identity = verify_host(require_l4=args.require_l4)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"refusing GPU host operation: {error}", file=sys.stderr)
        return 2
    print(
        "GPU host verified: "
        f"region={identity['region']} instance_type={identity['instance_type']}"
        + (f" gpu={identity['gpu']}" if "gpu" in identity else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
