from pathlib import Path
import argparse,os,subprocess,sys
from traffic_audit import run_audit,ROOT
from write_audit_report import write_report
from traffic_eda import run_eda
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--notebooks',action='store_true');a=p.parse_args()
    source=Path(a.input).resolve()
    if a.notebooks:
        # Build the audit notebook from this exact source, then the EDA notebook from its outputs.
        run_audit(source)
        env=os.environ.copy();env['TRAFFIC_INPUT']=str(source)
        subprocess.run([sys.executable,str(ROOT/'src/build_audit_notebook.py')],cwd=ROOT,env=env,check=True)
        subprocess.run([sys.executable,str(ROOT/'src/build_eda_notebook.py')],cwd=ROOT,env=env,check=True)
    else:
        run_audit(source);write_report();run_eda()
        subprocess.run([sys.executable,str(ROOT/'src/traffic_diagnostics.py')],cwd=ROOT,check=True)
        subprocess.run([sys.executable,str(ROOT/'src/traffic_additional_visuals.py')],cwd=ROOT,check=True)
        subprocess.run([sys.executable,str(ROOT/'src/traffic_patterns.py')],cwd=ROOT,check=True)
    print('Current outputs: outputs/current_audit, outputs/eda, outputs/diagnostics and outputs/additional_visuals')
