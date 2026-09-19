from traffic_patterns import PATTERN_FIGURES
from pathlib import Path
import ast,os
import nbformat
from traffic_eda import EXTRA_FIGURES
from traffic_additional_visuals import NEW_FIGURES
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[1]

def embedded(name):
    source=(ROOT/'src'/name).read_text(encoding='utf-8-sig')
    tree=ast.parse(source);lines=source.splitlines();remove=set()
    for node in tree.body:
        skip=isinstance(node,ast.ImportFrom) and node.module in ['traffic_audit','write_audit_report']
        skip=skip or (isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROOT' for t in node.targets))
        skip=skip or (isinstance(node,ast.If) and '__name__' in ast.unparse(node.test))
        if skip:remove.update(range(node.lineno-1,node.end_lineno))
    return '\n'.join(line for i,line in enumerate(lines) if i not in remove)
nb=nbformat.v4.new_notebook();nb.metadata.kernelspec={'name':'python3','display_name':'Python 3','language':'python'}
nb.cells=[nbformat.v4.new_markdown_cell('# Bangkok Traffic — Colab แบบไฟล์เดียว\n\nเปิดไฟล์นี้ใน Google Colab แล้วเลือก **Runtime → Run all** จากนั้นอัปโหลด Excel ที่มีชีต `traffic_data` ไม่ต้องอัปโหลดโฟลเดอร์ src หรือใช้ Notebook เก่า\n\nกติกาเดิม: ใช้ covid_period จากไฟล์; Date/month/year เป็นวันที่รายงาน; ช่องว่างและ - ของจำนวนรถเป็น 0; เก็บต้นฉบับและบันทึกค่าที่แทน วิเคราะห์เฉพาะชุดที่จับคู่ได้ ผลยังเป็นฉบับร่าง'),nbformat.v4.new_code_cell('''from pathlib import Path
import os, sys, importlib.util, subprocess
packages = {'pandas':'pandas', 'numpy':'numpy', 'openpyxl':'openpyxl', 'matplotlib':'matplotlib', 'seaborn':'seaborn'}
missing = [package for module, package in packages.items() if importlib.util.find_spec(module) is None]
if missing:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *missing])
from IPython.display import display, Image, Markdown
import pandas as pd
IN_COLAB = 'google.colab' in sys.modules
if not IN_COLAB:
    try:
        import google.colab
        IN_COLAB = True
    except ImportError:
        pass
ROOT = (Path('/content') if IN_COLAB else Path.cwd()) / 'bangkok_traffic_project'
for folder in ['data/raw', 'data/interim', 'data/processed', 'outputs/current_audit', 'outputs/eda/figures']:
    (ROOT / folder).mkdir(parents=True, exist_ok=True)
pd.set_option('display.max_rows', 12)
pd.set_option('display.max_columns', 10)'''),nbformat.v4.new_markdown_cell('## เลือก Excel\nบน Colab จะมีปุ่มอัปโหลด ถ้ารันในคอมพิวเตอร์ให้กรอก INPUT_PATH หรือกำหนด environment variable TRAFFIC_INPUT ไม่ต้องย้ายโฟลเดอร์โปรเจกต์'),nbformat.v4.new_code_cell('''INPUT_PATH = ''  # Local example: r'C:/Downloads/traffic.xlsx'
chosen = INPUT_PATH or os.environ.get('TRAFFIC_INPUT', '')
if chosen:
    INPUT = Path(chosen).expanduser().resolve()
elif IN_COLAB:
    from google.colab import files
    uploaded = files.upload()
    excel_files = [name for name in uploaded if name.lower().endswith('.xlsx')]
    if len(excel_files) != 1:
        raise ValueError('กรุณาอัปโหลดไฟล์ .xlsx เพียงหนึ่งไฟล์ แล้วรันเซลล์นี้ใหม่')
    INPUT = Path(excel_files[0]).resolve()
else:
    raise ValueError('กรุณากรอก INPUT_PATH เป็นพาธไฟล์ Excel ในเซลล์นี้')
if not INPUT.is_file():
    raise FileNotFoundError(f'ไม่พบไฟล์ Excel: {INPUT}')
with pd.ExcelFile(INPUT) as workbook:
    if 'traffic_data' not in workbook.sheet_names:
        raise ValueError('ไฟล์นี้ไม่มีชีต traffic_data')
print('Input:', INPUT.name)''')]
for name,title in [('traffic_audit.py','ฟังก์ชันตรวจข้อมูลและ matching'),('write_audit_report.py','ฟังก์ชันเขียนรายงาน audit'),('traffic_eda.py','ฟังก์ชันวิเคราะห์และสร้างกราฟ')]:
    nb.cells += [nbformat.v4.new_markdown_cell('## '+title+'\nโค้ดรวมอยู่ใน Notebook นี้แล้ว ไม่ต้อง import โมดูลของโปรเจกต์จาก src'),nbformat.v4.new_code_cell(embedded(name))]
nb.cells += [nbformat.v4.new_markdown_cell('## รัน Data Feasibility และ Matching Audit'),nbformat.v4.new_code_cell("summary = run_audit(INPUT)\nwrite_report()\nprint('Rows:', summary['rows'])\nprint('Source SHA-256:', summary['source_sha256'])\ndisplay(pd.DataFrame(summary['matching']))\ndisplay(pd.DataFrame(summary['numeric_profile']))"),nbformat.v4.new_markdown_cell('## รัน EDA\nเปรียบเทียบค่า median ต่อ location+time ภายในกลุ่ม และสร้างดัชนีเทียบ Before ของหน่วยเดียวกัน ไม่ใช้ค่าเฉลี่ยคนละสถานที่เป็น panel'),nbformat.v4.new_code_cell("evidence = run_eda()\nOUT = ROOT / 'outputs/eda'\ndisplay(pd.read_csv(OUT / 'sensitivity_summary.csv').round(2))")]
for num,name in enumerate(['01_matching_sensitivity.png','02_time_window_vph.png','03_paired_scatter.png','04_vehicle_mix.png']+list(EXTRA_FIGURES),1):
    nb.cells += [nbformat.v4.new_markdown_cell(f'## Figure {num} — {EXTRA_FIGURES.get(name, name)}'),nbformat.v4.new_code_cell(f"display(Image(filename=str(OUT / 'figures' / '{name}'), width=950))")]
    if name == '08_morning_location_ranking.png':
        nb.cells.append(nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'morning_location_ranking_displayed.csv').round(2))"))
    if name == '10_2026_matched_months.png':
        nb.cells.append(nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'year2026_matched_month_units.csv').round(2))"))
nb.cells += [nbformat.v4.new_markdown_cell('## สมมติฐานและการเลือกกราฟสำหรับ Pitch\nH1: ระดับ During ต่ำกว่า Before ใน matched sample; H2: ทิศทาง After เทียบ During เปลี่ยนตามการ matching; H3: มีการจับคู่เช้า–เย็นบนสถานที่และวันเดียวกันแล้ว ดูรูป 7; H4: การเปลี่ยนแปลงกระจายไม่เท่ากัน ดูรูป 6/8; H5: สัดส่วนรถเปลี่ยน ดูรูป 4/9 แต่ขึ้นกับสมมติฐาน 0\n\nสำหรับ Pitch แนะนำภาพรวม → coverage → ผลหลัก → เช้า/เย็น → ตัวอย่างสถานที่ → ข้อเสนอแนะ ไม่จำเป็นต้องแสดงทุกกราฟ งานรุ่นพี่ที่ใช้ศึกษาโครงเรื่อง: https://github.com/techasit239/Dads-5001-Accident-Is-You-Dont-Love ไม่ได้นำโค้ดหรือข้อมูลอุบัติเหตุมาใช้')]
nb.cells += [nbformat.v4.new_markdown_cell('## ตรวจผลและข้อจำกัด\nAfter รวมหลายปี ไม่ใช่ผลเฉพาะปี 2026; กลุ่มไตรมาสรายงานไม่รับรองฤดูกาลสำรวจตรงกัน; ค่า 0 ที่แทนเป็นสมมติฐานผู้ใช้ ไม่สรุปเหตุและผลจาก COVID หรือใช้จำนวนรถแทนความเร็ว/รถติด'),nbformat.v4.new_code_cell("analysis = pd.read_csv(ROOT / 'data/processed/traffic_matched_analysis.csv', low_memory=False)\nassert set(analysis.source_sha256) == {summary['source_sha256']}\nassert np.allclose(analysis.vehicle_total, analysis[[c+'_clean' for c in VEHICLES]].sum(axis=1))\nassert np.allclose(analysis.vehicles_per_hour * analysis.period_hours, analysis.vehicle_total)\nprint('Checks passed. Original Excel unchanged.')"),nbformat.v4.new_markdown_cell('## ดาวน์โหลดผลลัพธ์\nZIP รวมรายงาน ตาราง กราฟ และข้อมูลที่ประมวลผล ไม่รวม Excel ต้นฉบับ บน Colab คลิกไฟล์ในแถบ Files เพื่อดาวน์โหลด'),nbformat.v4.new_code_cell("from zipfile import ZipFile, ZIP_DEFLATED\narchive = ROOT.parent / 'bangkok_traffic_results.zip'\nwith ZipFile(archive, 'w', ZIP_DEFLATED) as z:\n    for folder in [ROOT / 'outputs', ROOT / 'data/processed', ROOT / 'data/reference']:\n        for path in folder.rglob('*'):\n            if path.is_file():\n                z.write(path, path.relative_to(ROOT))\nprint('Results ZIP:', archive.name)\nif IN_COLAB:\n    print('เปิดแถบ Files ทางซ้าย แล้วดาวน์โหลด bangkok_traffic_results.zip')")]
# Supplemental computations run after EDA so their helper names do not affect original charts.
# Insert before the ZIP code, using the actual archive cell as the authoritative anchor.
zip_code=next((i for i,c in enumerate(nb.cells) if c.cell_type=='code' and 'ZipFile(' in c.source),len(nb.cells))
nb.cells[zip_code:zip_code]=[
 nbformat.v4.new_markdown_cell('## ตรวจเพิ่มเติม: วันสำรวจ ความไม่แน่นอน ค่าว่าง และปีภายใน After\nผลเป็นความสัมพันธ์ในข้อมูล ไม่ใช่ผลเชิงสาเหตุของโควิด; รายงานบริบทพื้นที่และการทวน PDF อยู่ในโปรเจค Read.md'),
 nbformat.v4.new_code_cell(embedded('traffic_diagnostics.py')+'\nmain()'),
 nbformat.v4.new_code_cell("display(Markdown((ROOT/'outputs/diagnostics/Statistical_Diagnostics.md').read_text(encoding='utf-8')))"),
 nbformat.v4.new_markdown_cell('ข้อสังเกตจากการทวนต้นทางวันที่ 14 ก.ย. 2026: ไฟล์รวมรุ่น SHA 6e1b556f… แถว Excel 704 มี truck=0 และ tuk_tuk=0 แต่ PDF กรกฎาคม 2560 หน้า 6 ระบุ 32 และ 15 ตามลำดับ ยังไม่ได้แก้ต้นฉบับ ผลกรณีศึกษาจึงเป็นฉบับร่าง ข้อสังเกตนี้เฉพาะรุ่นข้อมูลเดิม ไม่ใช่ผลตรวจอัตโนมัติสำหรับไฟล์ใหม่')]
# Include reviewed geographic assets so Colab needs no live geocoder or GIS package.
assets={str(p.relative_to(ROOT)):p.read_text(encoding='utf-8-sig') for p in [ROOT/'data/reference/map_coordinates_reviewed.csv',ROOT/'data/reference/map_coordinate_matching_audit.csv',ROOT/'data/reference/bangkok_boundary.geojson',ROOT/'data/reference/map_sources.json',ROOT/'outputs/additional_visuals/Graph_Guide.md']}
asset_code="embedded_assets = "+repr(assets)+"\nfor rel, content in embedded_assets.items():\n    target = ROOT / rel\n    target.parent.mkdir(parents=True, exist_ok=True)\n    target.write_text(content, encoding='utf-8')"
newcells=[nbformat.v4.new_markdown_cell('## กราฟเพิ่มเติม 11–16 และพิกัดที่ตรวจแล้ว\nแผนที่เป็นบางส่วนของกรุงเทพฯ พิกัดอ้างอิงจาก OpenStreetMap และขอบเขต geoBoundaries ไม่ใช่ GPS วันสำรวจ'),nbformat.v4.new_code_cell(asset_code),nbformat.v4.new_code_cell(embedded('traffic_additional_visuals.py')+'\nnew_evidence = run_additional_visuals()')]
for name,title in NEW_FIGURES.items():
    newcells += [nbformat.v4.new_markdown_cell('### '+title),nbformat.v4.new_code_cell(f"display(Image(filename=str(ROOT/'outputs/additional_visuals/figures'/'{name}'), width=1050))")]
newcells += [nbformat.v4.new_code_cell("display(pd.read_csv(ROOT/'outputs/additional_visuals/location_code_lookup.csv'))\ndisplay(pd.read_csv(ROOT/'outputs/additional_visuals/map_road_period_indices.csv'))"),nbformat.v4.new_markdown_cell('คำอธิบายกราฟพร้อมวิธีอ่าน ผลและข้อจำกัดอยู่ใน outputs/additional_visuals/Graph_Guide.md ภายใน ZIP; ตารางรายถนนแสดงลิงก์พิกัด OSM สำหรับตรวจย้อน')]
zip_code=next(i for i,c in enumerate(nb.cells) if c.cell_type=='code' and 'ZipFile(' in c.source)
nb.cells[zip_code:zip_code]=newcells


pattern_cells=[nbformat.v4.new_markdown_cell('## กราฟ 17–20: Insight นอกประเด็น COVID\nใช้ปีรายงานและปีสำรวจ 2023–2025; รายละเอียดและชื่อสถานที่ใน Pattern_Findings.md'),nbformat.v4.new_code_cell(embedded('traffic_patterns.py')+'\nrun_patterns()')]
for name,title in PATTERN_FIGURES.items():
    pattern_cells += [nbformat.v4.new_markdown_cell('### '+title),nbformat.v4.new_code_cell(f"display(Image(filename=str(ROOT/'outputs/traffic_patterns/figures'/'{name}'), width=1000))")]
pattern_cells.append(nbformat.v4.new_code_cell("display(Markdown(chr(10).join(line for line in (ROOT/'outputs/traffic_patterns/Pattern_Findings.md').read_text(encoding='utf-8').splitlines() if not line.startswith('![]'))))"))
position=next(i for i,c in enumerate(nb.cells) if c.cell_type=='code' and 'ZipFile(' in c.source)
nb.cells[position:position]=pattern_cells

nbformat.validate(nb)
path=ROOT/'notebooks/Bangkok_Traffic_Colab.ipynb';nbformat.write(nb,path)
# Execute outside the repository, without src and without prior audit outputs.
smoke=ROOT/'tmp/colab_isolated_test';smoke.mkdir(parents=True,exist_ok=True)
os.environ['TRAFFIC_INPUT']='C:/Users/AphatsaraKhangkhet(C/Downloads/bangkok_traffic_2560_Present (NotFinal) (1).xlsx'
NotebookClient(nb,timeout=300,kernel_name='python3',resources={'metadata':{'path':str(smoke)}},allow_errors=False).execute()
nbformat.validate(nb)
assert all(c.execution_count is not None for c in nb.cells if c.cell_type=='code')
assert not any(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
nbformat.write(nb,path)
print('Standalone notebook tested from isolated directory:',path)
