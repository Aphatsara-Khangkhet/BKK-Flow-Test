"""Generate the current audit report only from saved, executed audit evidence."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def table(frame):
    frame=frame.fillna('')
    lines=['| '+' | '.join(map(str,frame.columns))+' |','|'+'|'.join(['---']*len(frame.columns))+'|']
    for row in frame.itertuples(index=False,name=None): lines.append('| '+' | '.join(str(x).replace('|','/') for x in row)+' |')
    return '\n'.join(lines)

def write_report():
    out=ROOT/'outputs/current_audit';s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    matrix=pd.DataFrame(s['matching']);quality={k:s[k] for k in ['zero_assumed_cells','zero_assumed_rows','numeric_unresolved_rows','numeric_fractional_rows','numeric_negative_rows','exact_repeat_excess','repeated_survey_key_rows','report_date_unparseable_rows','survey_date_missing','survey_date_unparsed_nonblank']}
    text=f"# Data Feasibility และ Matching Audit — ไฟล์ล่าสุด\n\nSource: {s['source_filename']} / traffic_data; {s['rows']:,} แถว {s['columns']} คอลัมน์\n\nSHA-256: {s['source_sha256']}\n\n"
    text+="## ข้อตกลง\n\nขอบเขตมีนาคม 2017–พฤษภาคม 2026 ใช้ covid_period ตามไฟล์ ไม่คำนวณกลุ่มใหม่ Date/month/year คือวันที่รายงาน แยกจาก survey_date ช่องว่างและ - ในจำนวนรถหกประเภทเป็น 0 ตามผู้ใช้ มี log เก็บค่าเดิม ไม่ตีความว่าไม่มีเดือน/สถานที่เท่ากับปริมาณรถ 0\n\n"
    text+="## Coverage ปีรายงาน\n\n"+table(pd.DataFrame(s['year_coverage']))+"\n\nจำนวนเดือนครบไม่แปลว่าทุกสถานที่มีครบปี ปี 2017 เริ่มมีนาคม ปี 2026 สิ้นสุดพฤษภาคมตามขอบเขต\n\n"
    text+="## Quality\n\n"+table(pd.DataFrame(quality.items(),columns=['check','count']))+"\n\nเก็บทุกแถวใน staging ชุด candidate กันคีย์สำรวจซ้ำทุกสมาชิกและตัวเลขที่ยังไม่ยืนยันออกชั่วคราว จำนวน flag อาจทับซ้อน ไม่ถือว่าทุกแถวที่ flag เป็นข้อมูลผิด\n\n"
    text+="ข้อความวัน/เดือน/ปีรองรับช่องว่างรอบ / และวันที่ไทย วันที่รายงานต่างจากวันที่สำรวจไม่ใช่เหตุให้ตัดแถว คอลัมน์ไม่มีชื่อยังไม่ใช้เป็นยอดรวมและยังไม่ตรวจ reconciliation กับ PDF ต้นทาง\n\n"
    text+="## Matching\n\n"+table(matrix)+"\n\nlocation นับ intersection+road; unit/group นับคีย์ตาม design; rows นับการสังเกตที่มีจริง ต้องมี covid_period ทั้งสามค่า ไม่หมายถึงทุกปี ชื่อ normalize เฉพาะ Unicode กับ whitespace ไม่ fuzzy match\n\n"
    text+="แบบรายเดือน/ไตรมาสรายงานและแบบเดือนสำรวจเป็นคนละนิยาม ใช้ดูความไวต่อชุดตัวอย่าง สำหรับ EDA ต้องคงเวลาเริ่ม–สิ้นสุดเดียวกัน คำนวณจำนวนรถต่อชั่วโมงตามชั่วโมงจริง และรายงาน sample ของแต่ละผล ห้ามอนุมานผลทั้งเมืองหรือปี 2026 จากการรวมกลุ่ม After หลายปี\n\n"
    text+="## สถานะ\n\nข้อมูลมีชุด candidate สำหรับทำ Mini Project ต่อ ผู้ใช้อนุญาตให้ทำ EDA แล้ว ผล EDA อยู่ใน outputs/eda/EDA_Findings.md และ Notebook 02 ยังต้องตรวจ numeric_review.csv, duplicate_review.csv และชื่อสถานที่กับต้นทางก่อนส่งฉบับ Final\n"
    target=out/'Data_Feasibility_Matching_Audit.md';target.write_text(text,encoding='utf-8');return target
if __name__=='__main__': print(write_report())
