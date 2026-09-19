from pathlib import Path
import json, os, sys
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
ROOT=Path(__file__).resolve().parents[1]
s=json.loads((ROOT/'outputs/current_audit/summary.json').read_text(encoding='utf-8'))
nb=nbformat.v4.new_notebook()
nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
nb.cells=[
nbformat.v4.new_markdown_cell('# Bangkok Traffic — Data Feasibility และ Matching Audit\n\nฉบับร่าง ตามข้อตกลงผู้ใช้ล่าสุด ขอบเขตมีนาคม 2017–พฤษภาคม 2026 ยังไม่มี EDA หรือกราฟ ก่อนผู้ใช้ตรวจ audit'),
nbformat.v4.new_markdown_cell('## Context & Methods\nใช้ `covid_period` ตามไฟล์; `Date/month/year` คือวันที่รายงาน; `survey_date` คือวันสำรวจ; ช่องว่างและ `-` ของจำนวนรถ 6 ประเภทเป็น 0 พร้อม log ไม่เปลี่ยน Excel ต้นฉบับ\n\n### Key Assumptions\nชื่อปรับเฉพาะ Unicode/whitespace; ข้อมูลซ้ำและตัวเลขกำกวมคงไว้ใน staging และกันออกจาก candidate ชั่วคราว; เดือนรายงานไม่ใช่เดือนสำรวจ ข้อมูลปี 2026 เป็น YTD'),
nbformat.v4.new_code_cell("from pathlib import Path\nimport os, sys, json\nimport pandas as pd\nROOT = Path.cwd() if (Path.cwd() / 'src').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT / 'src'))\nfrom traffic_audit import run_audit, normalize, survey_date, time_bounds\nfrom write_audit_report import write_report\npd.set_option('display.max_rows', 12)\npd.set_option('display.max_columns', 10)\nINPUT = Path(os.environ.get('TRAFFIC_INPUT', str(ROOT / "+repr(s['snapshot'].replace('\\','/'))+")))\nOUTPUT = ROOT / 'outputs/current_audit'"),
nbformat.v4.new_markdown_cell('## Data\nอ่านชีต traffic_data และรันกติกาเดิมทุกครั้ง ผลลัพธ์อ้างถึง snapshot และเลขแถว Excel ได้ เมื่อมีข้อมูลใหม่ให้ตั้ง TRAFFIC_INPUT เป็นพาธไฟล์นั้นแล้ว Run All'),
nbformat.v4.new_code_cell("summary = run_audit(INPUT, OUTPUT)\nwrite_report()\nprint(f\"Rows: {summary['rows']:,}; candidate rows: {summary['candidate_rows']:,}\")\nprint('Source SHA-256:', summary['source_sha256'])\nprint('Period counts:', summary['period_counts'])"),
nbformat.v4.new_markdown_cell('## Results\n### Coverage ตามปีรายงาน\nปี 2017 เริ่มมีนาคม และปี 2026 สิ้นสุดพฤษภาคมตามขอบเขต ไม่ถือว่าเดือนนอกขอบเขตหาย'),
nbformat.v4.new_code_cell("display(pd.DataFrame(summary['year_coverage']))"),
nbformat.v4.new_markdown_cell('### ผลการแทน 0 และค่าที่ต้องตรวจ\nจำนวนเซลล์ไม่เท่ากับจำนวนแถว ค่า 0 ที่แทนเป็นสมมติฐานที่ผู้ใช้กำหนด'),
nbformat.v4.new_code_cell("display(pd.DataFrame(summary['numeric_profile']))\nprint('Rows with assumed zeros:', summary['zero_assumed_rows'])\ndisplay(pd.read_csv(OUTPUT / 'numeric_review.csv'))"),
nbformat.v4.new_markdown_cell('### Matching Audit\nทุกกลุ่มมี covid_period ครบสามช่วง แต่ไม่รับรองว่ามีทุกปี `groups` คือชุดคีย์; `locations` คือคู่ทางแยก+ถนน; `rows` คือแถวต้นทาง'),
nbformat.v4.new_code_cell("display(pd.DataFrame(summary['matching']))"),
nbformat.v4.new_markdown_cell('### Coverage ของชุดไตรมาสรายงาน\nตรวจปีจริงที่เหลือ ห้ามใช้จำนวนแถวทั้งชุดแทน sample size ของปี 2026'),
nbformat.v4.new_code_cell("quarter = pd.read_csv(OUTPUT / 'candidate_report_quarter_time_rows.csv')\ndisplay(quarter.groupby(['report_year', 'covid_period']).size().reset_index(name='rows'))"),
nbformat.v4.new_markdown_cell('## Checks\nตรวจ parser เวลา/วันที่ และคำนวณ intersection ของเซตสถานที่อย่างอิสระจาก groupby เพื่อยืนยันผล matching'),
nbformat.v4.new_code_cell("assert survey_date('(18 เม.ย. 65)') == pd.Timestamp('2022-04-18')\nassert time_bounds('เร่งด่วนเช้า (07:00-09:00)') == time_bounds('เร่งด่วนเช้า (7.00 - 9.00 น.)')\nassert time_bounds('นอกเร่งด่วน (9.00 - 17.00 น.)')[2] == 8\nstaging = pd.read_csv(ROOT / 'data/interim/traffic_audited.csv')\nsets = [set(zip(g.intersection_key, g.road_key)) for _, g in staging.groupby('covid_period')]\nassert len(set.intersection(*sets)) == summary['matching'][0]['locations']\nassert len(staging) == summary['rows']\nassert staging['passenger_car_zero_assumed'].sum() == summary['numeric_profile'][0]['zero_assumed']\nprint('Independent matching, source-preservation, and parser checks passed.')"),
nbformat.v4.new_markdown_cell('## Takeaways\nเริ่มทำ Mini Project แบบมีเงื่อนไขได้ เลือก matching ให้ตรงกับคำถามก่อน EDA; กลุ่มรายเดือนตรงกันมีขนาดเล็ก ชุดไตรมาสรายงานเป็นทางเลือกแต่ไม่ควบคุมฤดูกาลสำรวจโดยสมบูรณ์ ตรวจข้อมูลซ้ำ/ตัวเลขกำกวมและชื่อสถานที่ก่อนยืนยันตัวอย่าง อ่านรายงาน outputs/current_audit/Data_Feasibility_Matching_Audit.md ที่สร้างจากผลรันนี้\n\nAI ช่วยสร้างโค้ดและเอกสาร สมาชิกต้องทวนข้อมูลต้นทางและตัดสินขอบเขต ยังไม่ได้สรุปแนวโน้ม การฟื้นตัว หรือสาเหตุจาก COVID')]
nbformat.validate(nb)
path=ROOT/'notebooks/01_data_feasibility_matching.ipynb'
nbformat.write(nb,path)
os.environ.setdefault('TRAFFIC_INPUT', str(ROOT / s['snapshot']))
# ipykernel is installed only in the project venv; use its default python3 kernel.
client=NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}},allow_errors=False)
client.execute()
nbformat.validate(nb);nbformat.write(nb,path)
html,_=HTMLExporter().from_notebook_node(nb)
(ROOT/'outputs/current_audit/notebook_preview.html').write_text(html,encoding='utf-8')
assert not any(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.get('outputs',[]))
assert all(c.execution_count is not None for c in nb.cells if c.cell_type=='code')
print('Notebook executed and saved:',path)
