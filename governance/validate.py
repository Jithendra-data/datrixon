"""CI entry point for approved governance definitions and publication evidence."""
import argparse
import json
from pathlib import Path
from governance.registry import ROOT, validate_registry
from governance.contracts import load_contracts, validate_sources, enforce_contracts
from governance.build import validate_governance
from governance.trust import load_policy


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--payload',type=Path,default=ROOT/'web/data/dashboard.json')
    parser.add_argument('--source',type=Path);args=parser.parse_args()
    baseline=json.loads((ROOT/'governance/metrics/history/2.0.0.json').read_text())
    registry=validate_registry(previous=baseline);policy=load_policy()
    for metric in registry['metrics']:
        if any(role not in policy['roles'] or metric['domain'] not in policy['roles'][role] for role in metric['permitted_roles']):
            raise ValueError('Incomplete authorization coverage')
    contracts=load_contracts()
    for source in contracts['sources']:
        if not source['keys'] or not set(source['keys'])<=set(source['columns']):raise ValueError('Invalid source keys')
    if args.source:enforce_contracts(validate_sources(args.source))
    validate_governance(json.loads(args.payload.read_text(encoding='utf-8')))
    print(f"PASS: {len(registry['metrics'])} metric definitions, {len(contracts['sources'])} contracts, policy coverage, lineage and approved V2 evidence")

if __name__=='__main__':main()
