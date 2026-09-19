from traffic_patterns import PATTERN_FIGURES
from pathlib import Path
import json,os
import nbformat
from traffic_eda import EXTRA_FIGURES
from traffic_additional_visuals import NEW_FIGURES
from nbclient import NotebookClient
from nbconvert import HTMLExporter
ROOT=Path(__file__).resolve().parents[1]
nb=nbformat.v4.new_notebook();nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
nb.cells=[
nbformat.v4.new_markdown_cell('# Bangkok Traffic — EDA และกราฟ\n\nใช้ไฟล์ใหม่ `bangkok_traffic_2560_Present (NotFinal) (1).xlsx` ชีต `traffic_data` เป็น snapshot หลัก ข้อมูลร่างมีนาคม 2017–พฤษภาคม 2026 ข้อสรุปเป็นของ matched sample ไม่ใช่ทั้งเมือง'),
nbformat.v4.new_markdown_cell('## Context & Methods\nคำถาม: ปริมาณรถต่อชั่วโมงในสถานที่และเวลาที่จับคู่ได้ แตกต่างระหว่างกลุ่ม COVID อย่างไร?\n\n### Key Assumptions\nใช้ `covid_period` ในไฟล์ ไม่สร้างกลุ่มใหม่จากวันที่; `Date/month/year` เป็นวันที่รายงาน; ช่องว่างและ `-` ของจำนวนรถเป็น 0 ตามผู้ใช้; เก็บวันที่สำรวจแยกกัน; จำนวนทศนิยมและคีย์สำรวจซ้ำกันออกจาก candidate ชั่วคราว ไม่แก้ raw\n\nหนึ่งหน่วย = intersection + road + เวลาเริ่ม–สิ้นสุดเดียวกัน ใช้ median ของ vehicles/hour ภายในแต่ละหน่วยและกลุ่ม จากนั้นสร้าง Before=100 ของแต่ละหน่วย และรายงาน median ดัชนีของหน่วย ไม่ใช่อัตราส่วนค่าเฉลี่ยรวมเมือง'),
nbformat.v4.new_code_cell("from pathlib import Path\nimport sys,json\nimport pandas as pd\nimport numpy as np\nfrom IPython.display import display, Image, Markdown\nROOT=Path.cwd() if (Path.cwd()/'src').exists() else Path.cwd().parent\nsys.path.insert(0,str(ROOT/'src'))\nfrom traffic_eda import run_eda\nfrom traffic_audit import VEHICLES, PERIODS\npd.set_option('display.max_rows',12)\npd.set_option('display.max_columns',10)\nOUT=ROOT/'outputs/eda'"),
nbformat.v4.new_markdown_cell('## Data\nNotebook นี้ใช้ผล audit รอบล่าสุดใน data/processed/traffic_candidates.csv เมื่อมี Excel ใหม่ให้รัน Notebook 01 หรือ pipeline audit ก่อน แล้วรัน Notebook นี้ ผลเชื่อมกับ SHA-256 ของ workbook ได้'),
nbformat.v4.new_code_cell("evidence=run_eda()\nsummary=evidence['results']; source=evidence['source']\nprint('Workbook:',source['source_filename'])\nprint('SHA-256:',source['source_sha256'])\nprint('Rows:',source['rows'])\ndisplay(pd.DataFrame(source['year_coverage']))"),
nbformat.v4.new_markdown_cell('## Results\n### ดัชนีตามวิธี matching\nเส้น 100 คือระดับ Before ของแต่ละหน่วย ชุดเดือน/ไตรมาสที่เข้มขึ้นอาจมีสถานที่ต่างจากชุดหลัก จึงเป็น sensitivity ต่อทั้งเวลาและองค์ประกอบตัวอย่าง'),
nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'sensitivity_summary.csv').round(2))\ndisplay(Image(filename=str(OUT/'figures/01_matching_sensitivity.png'),width=950))\nbroad=summary['same_location_time']; quarter=summary['same_report_quarter']\ndisplay(Markdown(f\"**ผล:** ชุดหลัก {broad['rows']:,} แถว / {broad['units']} หน่วย มี During={broad['index_medians']['During']:.1f} และ After={broad['index_medians']['After']:.1f} เมื่อ Before=100; ชุดไตรมาสรายงานมี {quarter['rows']} แถว / {quarter['units']} หน่วย ได้ During={quarter['index_medians']['During']:.1f}, After={quarter['index_medians']['After']:.1f}. เป็นผลเชิงพรรณนา ไม่ใช่ causal effect\"))"),
nbformat.v4.new_markdown_cell('### เวลาเริ่ม–สิ้นสุดที่เทียบได้\nหน่วย location/time เดียวกันครบทั้งสามกลุ่ม การเปรียบเทียบระหว่างเช้ากับเย็นยังไม่ได้บังคับให้ใช้ชุดสถานที่เดียวกัน'),
nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'time_window_median_vph.csv').round(1))\ndisplay(Image(filename=str(OUT/'figures/02_time_window_vph.png'),width=950))"),
nbformat.v4.new_markdown_cell('### ความแตกต่างระหว่างหน่วยที่จับคู่\nจุดเหนือเส้นคือปริมาณมากกว่า Before ภายในหน่วยนั้น ใช้แกนเชิงเส้นเดียวกันและเก็บค่าปริมาณสูงไว้'),
nbformat.v4.new_code_cell("display(Image(filename=str(OUT/'figures/03_paired_scatter.png'),width=950))\nprint(f\"After >= Before in {broad['after_at_or_above_before_pct']:.1f}% of positive-baseline units.\")"),
nbformat.v4.new_markdown_cell('### องค์ประกอบประเภทรถ\nคำนวณสัดส่วนแต่ละการสังเกต แล้วเฉลี่ยภายในหน่วยและให้น้ำหนักหน่วยเท่ากัน ใช้เฉพาะหน่วยที่มีค่ารวมมากกว่า 0 ครบสามกลุ่ม ค่านี้ไม่ใช่สัดส่วนรถทั้งหมดของกรุงเทพฯ'),
nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'vehicle_mix_equal_unit_percent.csv').round(2))\ndisplay(Image(filename=str(OUT/'figures/04_vehicle_mix.png'),width=950))"),
nbformat.v4.new_markdown_cell('### สถิติและขนาดตัวอย่าง\nตารางสถิติด้านล่างเป็นระดับแถว ให้น้ำหนักการสังเกตเท่ากัน จึงคนละตัวประมาณกับ median paired index ที่เป็นผลหลัก IQR เป็นเพียงการชี้ค่าหาง ไม่ได้ลบ outlier'),
nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'row_level_descriptive_statistics.csv').round(2))\ndisplay(pd.read_csv(OUT/'outlier_review_counts.csv'))\ndisplay(pd.read_csv(OUT/'matched_year_coverage.csv'))\nprint('Coverage limitations:', summary['coverage'])"),
nbformat.v4.new_markdown_cell('## Checks\nคำนวณ matched-unit median และดัชนีซ้ำอย่างอิสระจาก CSV ตรวจสูตรรถต่อชั่วโมง สัดส่วนรวม 100 และ fingerprint ของข้อมูล'),
nbformat.v4.new_code_cell("analysis=pd.read_csv(ROOT/'data/processed/traffic_matched_analysis.csv',low_memory=False)\nassert set(analysis.source_sha256)=={source['source_sha256']}\nassert np.allclose(analysis.vehicle_total,analysis[[c+'_clean' for c in VEHICLES]].sum(axis=1))\nassert np.allclose(analysis.vehicles_per_hour*analysis.period_hours,analysis.vehicle_total)\nkeys=['intersection_key','road_key','time_key']\ncheck=analysis.groupby(keys+['covid_period']).vehicles_per_hour.median().unstack().reindex(columns=PERIODS)\nassert check.notna().all().all()\nassert len(check)==broad['units']\nfor label,name in zip(PERIODS,['Before','During','After']):\n    calculated=(check[label]/check[PERIODS[0]].where(check[PERIODS[0]]>0)*100).median()\n    assert np.isclose(calculated,broad['index_medians'][name])\nmix=pd.read_csv(OUT/'vehicle_mix_equal_unit_percent.csv')\nassert np.allclose(mix[VEHICLES].sum(axis=1),100)\nprint('Formula, independent paired-index, composition and fingerprint checks passed.')"),
nbformat.v4.new_markdown_cell('## Takeaways\nH1: During ต่ำกว่า Before ในค่ามัธยฐาน paired index ของชุดที่ตรวจ จึงสนับสนุนสมมติฐานเชิงพรรณนาในตัวอย่างนี้\n\nH2: ข้อสรุปว่า After สูงกว่า During ไม่สม่ำเสมอระหว่าง matching designs จึงไม่ควรสรุปว่าฟื้นตัวชัดเจน\n\nH3: เพิ่มการจับคู่สถานที่และวันสำรวจเช้า–เย็นแล้วในรูป 7 ใช้ความต่างดัชนีภายในสถานที่ ไม่ใช่ความต่างของค่าเฉลี่ยคนละ sample และยังไม่อ้างเหตุและผล\n\nAfter เป็นกลุ่มรวมหลายปี ไม่ใช่ผลเฉพาะปี 2026 ไม่มีหน่วยครบทั้ง 10 ปีตาม audit รอบนี้ จึงไม่สร้างกราฟรายปีที่เปลี่ยนตัวอย่างเงียบ ๆ\n\nก่อนส่ง Final ให้ตรวจชื่อ/ค่าที่ติด flag กับต้นทาง ใส่บทบาทสมาชิกและ AI ยืนยันสิทธิ์เผยแพร่ และใช้คำว่า traffic volume ไม่ตีความว่าเป็นความเร็วหรือรถติด')]

extra_cells=[]
for name,title in EXTRA_FIGURES.items():
    extra_cells += [nbformat.v4.new_markdown_cell('### '+title),nbformat.v4.new_code_cell(f"display(Image(filename=str(OUT/'figures'/'{name}'), width=950))")]
    if name == '08_morning_location_ranking.png':
        extra_cells.append(nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'morning_location_ranking_displayed.csv').round(2))"))
    if name == '10_2026_matched_months.png':
        extra_cells.append(nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'year2026_matched_month_units.csv').round(2))"))
extra_cells += [nbformat.v4.new_markdown_cell('### การนำไปใช้ใน Pitch\nรายละเอียดคำถาม/เกณฑ์/หน้าที่ของแต่ละกราฟอยู่ใน docs/rubric_and_senior_review.md การศึกษางานรุ่นพี่ใช้แนวการเล่าเรื่อง ไม่คัดลอกโค้ดหรือข้อมูล และยังไม่ได้ตรวจ PDF description ของ DADS5001 ซ้ำจากต้นฉบับ\n\nอ้างอิง: https://github.com/techasit239/Dads-5001-Accident-Is-You-Dont-Love')]
position=next(i for i,c in enumerate(nb.cells) if c.cell_type=='markdown' and c.source.startswith('## Checks'))
nb.cells[position:position]=extra_cells

newcells=[nbformat.v4.new_markdown_cell('## กราฟเพิ่มเติม 11–16\nใช้ผลตรวจค่าว่าง/วันสำรวจและพิกัดที่ตรวจแล้ว แผนที่เป็น subset ไม่ใช่ตัวแทนทั้งเมือง'),nbformat.v4.new_code_cell("from traffic_diagnostics import main as run_diagnostics\nfrom traffic_additional_visuals import run_additional_visuals\nrun_diagnostics()\nrun_additional_visuals()")]
for name,title in NEW_FIGURES.items():
    newcells += [nbformat.v4.new_markdown_cell('### '+title),nbformat.v4.new_code_cell(f"display(Image(filename=str(ROOT/'outputs/additional_visuals/figures'/'{name}'), width=1050))")]
newcells.append(nbformat.v4.new_code_cell("display(pd.read_csv(ROOT/'outputs/additional_visuals/location_code_lookup.csv'))\ndisplay(pd.read_csv(ROOT/'outputs/additional_visuals/map_road_period_indices.csv'))"))
position=next(i for i,c in enumerate(nb.cells) if c.cell_type=='markdown' and c.source.startswith('## Checks'))
nb.cells[position:position]=newcells


pattern_cells=[nbformat.v4.new_markdown_cell('## กราฟ 17–20: Insight นอกประเด็น COVID\nใช้ปีรายงานและปีสำรวจ 2023–2025; รายละเอียดและชื่อสถานที่ใน Pattern_Findings.md'),nbformat.v4.new_code_cell("from traffic_patterns import run_patterns\nrun_patterns()")]
for name,title in PATTERN_FIGURES.items():
    pattern_cells += [nbformat.v4.new_markdown_cell('### '+title),nbformat.v4.new_code_cell(f"display(Image(filename=str(ROOT/'outputs/traffic_patterns/figures'/'{name}'), width=1000))")]
pattern_cells.append(nbformat.v4.new_code_cell("display(Markdown(chr(10).join(line for line in (ROOT/'outputs/traffic_patterns/Pattern_Findings.md').read_text(encoding='utf-8').splitlines() if not line.startswith('![]'))))"))
position=next(i for i,c in enumerate(nb.cells) if c.cell_type=='markdown' and c.source.startswith('## Checks'))
nb.cells[position:position]=pattern_cells

nbformat.validate(nb);path=ROOT/'notebooks/02_eda_and_visualization.ipynb';nbformat.write(nb,path)
NotebookClient(nb,timeout=240,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}},allow_errors=False).execute()
nbformat.validate(nb);nbformat.write(nb,path)
html,_=HTMLExporter().from_notebook_node(nb);(ROOT/'outputs/eda/notebook_preview.html').write_text(html,encoding='utf-8')
code=[c for c in nb.cells if c.cell_type=='code'];assert all(c.execution_count is not None for c in code)
assert not any(o.output_type=='error' for c in code for o in c.outputs)
print('EDA notebook executed:',len(code),'code cells')
