#!/usr/bin/env python3
"""
blue_cleanup.py - Safe Blue VPC cleanup after green cutover

Audits the Blue Terraform state, removes TGW and any other shared/preserved
resources from state (without destroying them in AWS), then offers to run
terraform destroy on what remains (Blue VPC only).

Usage:
    python blue_cleanup.py --terraform-dir /path/to/blue/terraform
    python blue_cleanup.py --terraform-dir /path/to/blue/terraform --dry-run
"""

import argparse
import subprocess
import sys
import re
from typing import List, Tuple


# Resource type patterns that should NEVER be destroyed during Blue cleanup.
#
# The TGW itself, its route tables, routes, and associations are shared
# infrastructure. By the time this script runs, route table entries have
# already been updated to point traffic to the Green attachment — those
# tables and routes must be preserved.
#
# The Blue TGW VPC *attachment* is Blue-specific (Green has its own separate
# attachment) and is intentionally left out of this list so it gets destroyed.
TGW_PATTERNS = [
    r"aws_ec2_transit_gateway\b",                        # TGW itself
    r"aws_ec2_transit_gateway_route_table\b",            # Shared route tables
    r"aws_ec2_transit_gateway_route\b",                  # Routes (already point to Green)
    r"aws_ec2_transit_gateway_route_table_association",  # Customer VPC associations
    r"aws_ec2_transit_gateway_route_table_propagation",  # Route propagations
]

# Also protect by module name patterns for the above resource types.
# e.g. module.vpc-transit-gateway[0].aws_ec2_transit_gateway.main
# Note: module.vpc-transit-gateway-attachment is NOT protected — it's Blue-specific.
TGW_MODULE_PATTERNS = [
    r"module\.vpc.transit.gateway(?!.attachment).*\.aws_ec2_transit_gateway\b",
    r"module\.vpc.transit.gateway(?!.attachment).*\.aws_ec2_transit_gateway_route",
    r"module\.tgw(?!.attachment).*\.aws_ec2_transit_gateway\b",
]


def run(cmd: List[str], cwd: str) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def get_state_list(terraform_dir: str) -> List[str]:
    """Return all resource addresses in the state file."""
    print("\n[1/5] Reading Terraform state...")
    rc, stdout, stderr = run(["terraform", "state", "list"], terraform_dir)
    if rc != 0:
        print(f"ERROR: terraform state list failed:\n{stderr}")
        sys.exit(1)
    resources = [line.strip() for line in stdout.splitlines() if line.strip()]
    print(f"      Found {len(resources)} resources in state.")
    return resources


def classify_resources(resources: List[str]) -> Tuple[List[str], List[str]]:
    """
    Split resources into:
      - tgw_resources: must be removed from state (not destroyed)
      - blue_resources: safe to destroy
    """
    tgw = []
    blue = []

    all_tgw_patterns = [re.compile(p, re.IGNORECASE) for p in TGW_PATTERNS + TGW_MODULE_PATTERNS]

    for addr in resources:
        if any(p.search(addr) for p in all_tgw_patterns):
            tgw.append(addr)
        else:
            blue.append(addr)

    return tgw, blue


def print_classification(tgw: List[str], blue: List[str]) -> None:
    """Print the classification results for review."""
    print("\n[2/5] Classification Results")
    print("=" * 60)

    if tgw:
        print(f"\n  PROTECTED (will be removed from state, NOT destroyed) [{len(tgw)}]:")
        for r in tgw:
            print(f"    - {r}")
    else:
        print("\n  PROTECTED: none found — TGW does not appear to be in this state file.")

    print(f"\n  BLUE VPC (will be destroyed) [{len(blue)}]:")
    for r in blue:
        print(f"    + {r}")
    print()


def confirm(prompt: str) -> bool:
    """Ask yes/no confirmation."""
    while True:
        answer = input(f"{prompt} [yes/no]: ").strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("Please type 'yes' or 'no'.")


def remove_from_state(resources: List[str], terraform_dir: str, dry_run: bool) -> None:
    """Run terraform state rm for each resource."""
    if not resources:
        print("\n[3/5] No TGW resources to remove from state — skipping.")
        return

    print(f"\n[3/5] Removing {len(resources)} TGW resource(s) from state (AWS resources unchanged)...")

    for addr in resources:
        if dry_run:
            print(f"  [DRY RUN] terraform state rm '{addr}'")
        else:
            print(f"  Removing: {addr}")
            rc, stdout, stderr = run(["terraform", "state", "rm", addr], terraform_dir)
            if rc != 0:
                print(f"  ERROR removing {addr}:\n{stderr}")
                print("  Aborting — no resources have been destroyed.")
                sys.exit(1)
            print(f"  OK")


def plan_destroy(terraform_dir: str, dry_run: bool) -> None:
    """Run terraform plan -destroy so the user can review what will be destroyed."""
    print("\n[4/5] Running terraform plan -destroy (review before final destroy)...")
    if dry_run:
        print("  [DRY RUN] terraform plan -destroy")
        return

    rc, stdout, stderr = run(["terraform", "plan", "-destroy"], terraform_dir)
    print(stdout)
    if stderr:
        print(stderr)
    if rc != 0:
        print("ERROR: terraform plan -destroy failed. Aborting.")
        sys.exit(1)


def destroy(terraform_dir: str, dry_run: bool) -> None:
    """Run terraform destroy."""
    print("\n[5/5] Running terraform destroy...")
    if dry_run:
        print("  [DRY RUN] terraform destroy -auto-approve")
        print("\nDry run complete. Re-run without --dry-run to execute.")
        return

    rc, stdout, stderr = run(["terraform", "destroy", "-auto-approve"], terraform_dir)
    print(stdout)
    if stderr:
        print(stderr)
    if rc != 0:
        print("ERROR: terraform destroy failed.")
        sys.exit(1)
    print("\nBlue VPC cleanup complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Safely destroy Blue VPC without touching the Transit Gateway."
    )
    parser.add_argument(
        "--terraform-dir",
        required=True,
        help="Path to the Blue Terraform directory (where terraform.tfstate or backend config lives)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making any changes",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Blue VPC Cleanup - Safe TGW-Aware Terraform Destroy")
    print("=" * 60)
    if args.dry_run:
        print("  *** DRY RUN MODE — no changes will be made ***")
    print(f"  Terraform dir: {args.terraform_dir}")

    # Step 1: Read state
    resources = get_state_list(args.terraform_dir)
    if not resources:
        print("State file is empty or no resources found. Nothing to do.")
        sys.exit(0)

    # Step 2: Classify
    tgw_resources, blue_resources = classify_resources(resources)
    print_classification(tgw_resources, blue_resources)

    if not blue_resources:
        print("No Blue VPC resources found to destroy. Exiting.")
        sys.exit(0)

    # Confirm before doing anything
    if not args.dry_run:
        if tgw_resources:
            print(f"  {len(tgw_resources)} TGW resource(s) will be detached from state (NOT destroyed).")
        print(f"  {len(blue_resources)} Blue VPC resource(s) will be PERMANENTLY DESTROYED.\n")
        if not confirm("Proceed with cleanup?"):
            print("Aborted.")
            sys.exit(0)

    # Step 3: Remove TGW from state
    remove_from_state(tgw_resources, args.terraform_dir, args.dry_run)

    # Step 4: Plan destroy for review
    plan_destroy(args.terraform_dir, args.dry_run)

    # Step 5: Final confirm + destroy
    if not args.dry_run:
        print()
        if not confirm("Plan looks correct. Run terraform destroy now?"):
            print("Aborted. TGW resources have already been removed from state.")
            print("To restore them: terraform import <resource_type> <resource_id>")
            sys.exit(0)
        destroy(args.terraform_dir, args.dry_run)
    else:
        destroy(args.terraform_dir, args.dry_run)


if __name__ == "__main__":
    main()
