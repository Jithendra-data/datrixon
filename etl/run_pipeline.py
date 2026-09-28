"""Build a candidate, validate it, then atomically replace the public contract."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import time
import tracemalloc
from pathlib import Path
import pandas as pd
from etl.clean_data import clean_file
from etl.build_analytics import build
from etl.export_dashboard_data import export
from etl.warehouse import load_warehouse
from python.generators.generate_all import build_transactions
from python.generators.generate_master_data import create_master_data
from utils.config import NUM_PURCHASE_ORDERS, NUM_SALES_ORDERS, PROCESSED_DIR, RAW_DIR, WEB_DATA_DIR
from utils.helpers import write_csv, write_json
from validation.run_data_quality_checks import validate
from validation.reconciliation import reconcile
from validation.publication import enforce_controls, validate_contract

def run(generate=True, orders=NUM_SALES_ORDERS, purchase_orders=NUM_PURCHASE_ORDERS, raw_dir=RAW_DIR, processed_dir=PROCESSED_DIR, web_dir=WEB_DATA_DIR):
    import shutil
    import subprocess
    import uuid
    from datetime import datetime, timezone
    from utils.config import RANDOM_SEED, AS_OF_DATE, START_DATE
    from validation.registry import CONTROL_VERSION, CONTRACT_VERSION, summarize
    run_id=os.getenv('GITHUB_RUN_ID') or uuid.uuid4().hex
    started=time.perf_counter(); timings={}; stage='initialization'
    raw_dir.mkdir(parents=True,exist_ok=True); processed_dir.mkdir(parents=True,exist_ok=True)
    bundle=processed_dir/'runs'/run_id; bundle.mkdir(parents=True,exist_ok=True)
    config=dict(seed=RANDOM_SEED,orders=orders,purchase_orders=purchase_orders,start_date=START_DATE,as_of_date=AS_OF_DATE)
    generation_file=raw_dir/'generation_manifest.json'
    def hashes():return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(raw_dir.glob('*.csv'))}
    try:
        stage='generation'
        if generate:
            if orders<1 or purchase_orders<1:raise ValueError('Order counts must be positive')
            masters=create_master_data()
            for name,frame in {**masters,**build_transactions(masters,orders,purchase_orders)}.items():write_csv(frame,raw_dir/f'{name}.csv')
            write_json(dict(configuration=config,input_sha256=hashes()),generation_file)
        input_hashes=hashes()
        generation=json.loads(generation_file.read_text(encoding='utf-8')) if generation_file.exists() else {}
        known=generation.get('input_sha256')==input_hashes
        config=generation.get('configuration',{}) if known else dict(seed=None,as_of_date=AS_OF_DATE)
        timings['generation_seconds']=round(time.perf_counter()-started,3);checkpoint=time.perf_counter();tracemalloc.start()
        stage='source_validation'
        checks=validate(raw_dir).to_dict(orient='records')
        write_csv(pd.DataFrame(checks),processed_dir/'data_quality.csv')
        write_csv(pd.DataFrame(checks),bundle/'data_quality.csv')
        enforce_controls(checks,synthetic=True)
        write_csv(pd.DataFrame(checks),processed_dir/'data_quality.csv')
        stage='staging'
        for source in raw_dir.glob('*.csv'):clean_file(source,processed_dir)
        stage='warehouse'
        warehouse=processed_dir/'warehouse.sqlite'
        counts=load_warehouse(processed_dir,warehouse)
        stage='analytics'
        data=build(processed_dir,processed_dir,warehouse)
        timings['validation_model_seconds']=round(time.perf_counter()-checkpoint,3);checkpoint=time.perf_counter()
        stage='export'
        payload=export(data,source=processed_dir,write=False)
        payload['data_quality']={'results':checks,'summary':summarize(checks)}
        stage='reconciliation'
        rec=reconcile(raw_dir,warehouse,payload);payload['reconciliation']=rec.to_dict(orient='records')
        write_csv(rec,processed_dir/'reconciliation.csv');write_csv(rec,bundle/'reconciliation.csv')
        _,peak=tracemalloc.get_traced_memory()
        timings['export_reconcile_seconds']=round(time.perf_counter()-checkpoint,3);timings['total_seconds']=round(time.perf_counter()-started,3)
        try:
            commit=os.getenv('GITHUB_SHA') or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
            dirty=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip())
        except (OSError,subprocess.CalledProcessError):commit='unavailable';dirty=None
        dataset_id=hashlib.sha256(json.dumps(input_hashes,sort_keys=True).encode()).hexdigest()
        payload['pipeline_metadata'].update(publication_status='APPROVED',random_seed=config.get('seed'),
            generation_mode='generated' if generate else 'reused raw files; verified generation manifest' if known else 'reused raw files; seed unknown',
            generation_configuration=config,business_as_of_date=AS_OF_DATE,dataset_id=dataset_id,build_id=run_id,
            publication_timestamp=datetime.now(timezone.utc).isoformat(),
            contract_version=CONTRACT_VERSION,control_version=CONTROL_VERSION,
            expected_exceptions=[r['TestName'] for r in checks if r['Status']!='PASS'],
            warehouse_engine='SQLite',warehouse_rows=counts,timings=timings,
            peak_python_allocations_mb=round(peak/1024**2,2),python_version=platform.python_version(),
            dependencies={p:importlib.metadata.version(p) for p in ['pandas','numpy','Faker']},
            input_sha256=input_hashes,commit=commit,working_tree_dirty=dirty,
            workflow_run=os.getenv('GITHUB_RUN_ID'),deployment_identity='Recorded separately by GitHub Pages deployment')
        stage='publication_contract'
        validate_contract(payload)
        web_dir.mkdir(parents=True,exist_ok=True)
        candidate=web_dir/'dashboard.candidate.json';write_json(payload,candidate)
        validate_contract(json.loads(candidate.read_text(encoding='utf-8')))
        # Complete the run evidence before changing the public file.
        evidence={**payload['pipeline_metadata'],'published_bytes':candidate.stat().st_size,'published_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest()}
        write_json(evidence,bundle/'run_manifest.json');write_json(evidence,processed_dir/'run_manifest.json')
        shutil.copy2(warehouse,bundle/'warehouse.sqlite')
        shutil.copy2(candidate,bundle/'dashboard.json')
        shutil.copy2(processed_dir/'data_quality.csv',bundle/'data_quality.csv')
        stage='publication_replace'
        candidate.replace(web_dir/'dashboard.json')
        print(f'APPROVED: {counts}; {timings}')
        return payload
    except Exception as error:
        failure=dict(build_id=run_id,status='FAILED',stage=stage,error_type=type(error).__name__,message=str(error),as_of_date=AS_OF_DATE)
        write_json(failure,bundle/'failure.json');write_json(failure,processed_dir/'failure.json')
        raise
    finally:
        if tracemalloc.is_tracing():tracemalloc.stop()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--orders',type=int,default=NUM_SALES_ORDERS);parser.add_argument('--purchase-orders',type=int,default=NUM_PURCHASE_ORDERS)
    parser.add_argument('--skip-generation',action='store_true');parser.add_argument('--workspace',type=Path,help='Isolate test files')
    args=parser.parse_args();kwargs={} if args.workspace is None else dict(raw_dir=args.workspace/'raw',processed_dir=args.workspace/'processed',web_dir=args.workspace/'web')
    run(not args.skip_generation,args.orders,args.purchase_orders,**kwargs)
