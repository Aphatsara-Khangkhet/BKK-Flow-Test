from pathlib import Path
import json,hashlib,nbformat,pandas as pd
root=Path.cwd();out=root/'outputs/current_audit'
nb=nbformat.read(root/'notebooks/01_data_feasibility_matching.ipynb',as_version=4)
nbformat.validate(nb)
code=[c for c in nb.cells if c.cell_type=='code']
errors=[o for c in code for o in c.outputs if o.output_type=='error']
s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
raw=pd.read_excel(root/s['snapshot'],sheet_name='traffic_data')
d=pd.read_csv(root/'data/interim/traffic_audited.csv')
assert len(raw)==len(d)==s['rows']
assert raw.covid_period.tolist()==d.covid_period.tolist()
assert not errors and all(c.execution_count is not None for c in code)
assert all(not any(o.get('data',{}).get('image/png') for o in c.outputs) for c in code)
changes=pd.read_csv(out/'zero_assumption_log.csv')
assert changes.replacement.eq(0).all() and len(changes)==s['zero_assumed_cells']
checks={'notebook_format':'valid','executed_code_cells':len(code),'error_outputs':len(errors),'source_sha256':s['source_sha256'],'source_rows_preserved':len(d),'covid_period_preserved':True,'zero_log_rows':len(changes),'charts_created':0,'visual_preview':'Not completed: browser runtime could not start (CreateProcessWithLogonW 1907). Executed cell outputs inspected structurally.'}
(out/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
p=out/'Data_Feasibility_Matching_Audit.md';text=p.read_text(encoding='utf-8');text+='\n## การทดสอบไฟล์ส่งมอบ\n\nNotebook รันจาก kernel ใหม่ครบ '+str(len(code))+' code cells ไม่มี error output และไม่มีกราฟ ตรวจจำนวนแถว คง covid_period เดิม และ log ค่า 0 แล้ว การตรวจหน้าตา HTML preview ด้วยเบราว์เซอร์ยังทำไม่ได้ เพราะ runtime ของเครื่องเริ่มไม่สำเร็จ (CreateProcessWithLogonW 1907); ตรวจโครงสร้างและผลลัพธ์เซลล์แล้ว รายละเอียดอยู่ใน validation.json\n';p.write_text(text,encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
