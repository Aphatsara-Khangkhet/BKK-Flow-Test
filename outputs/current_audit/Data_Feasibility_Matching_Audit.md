# Data Feasibility และ Matching Audit — ไฟล์ล่าสุด

Source: bangkok_traffic_2560_Present (NotFinal) (1).xlsx / traffic_data; 17,005 แถว 18 คอลัมน์

SHA-256: 6e1b556f353c66fec5c8a664f3e1e5b5e52e5a756f75c2ae28562c5c0fa6118b

## ข้อตกลง

ขอบเขตมีนาคม 2017–พฤษภาคม 2026 ใช้ covid_period ตามไฟล์ ไม่คำนวณกลุ่มใหม่ Date/month/year คือวันที่รายงาน แยกจาก survey_date ช่องว่างและ - ในจำนวนรถหกประเภทเป็น 0 ตามผู้ใช้ มี log เก็บค่าเดิม ไม่ตีความว่าไม่มีเดือน/สถานที่เท่ากับปริมาณรถ 0

## Coverage ปีรายงาน

| report_year | rows | months_present | months_missing_within_scope | locations | assumed_zero_rows |
|---|---|---|---|---|---|
| 2017 | 1422 | 3,4,5,6,7,8,9,10,11,12 |  | 476 | 0 |
| 2018 | 1671 | 1,2,3,4,5,6,7,8,9,10,11,12 |  | 531 | 0 |
| 2019 | 1824 | 1,2,3,4,5,6,7,8,9,10,11,12 |  | 611 | 0 |
| 2020 | 1333 | 1,2,3,4,5,7,8,10,11,12 | 6,9 | 420 | 560 |
| 2021 | 2136 | 1,2,3,4,5,6,7,8,9,10,11,12 |  | 677 | 549 |
| 2022 | 2048 | 1,2,3,4,5,6,7,8,9,10,11,12 |  | 671 | 400 |
| 2023 | 1923 | 1,2,3,4,5,6,7,8,9,10,11,12 |  | 627 | 0 |
| 2024 | 1875 | 1,2,3,4,5,6,7,8,9,10,11,12 |  | 618 | 0 |
| 2025 | 2062 | 1,2,3,4,5,6,7,8,9,10,11,12 |  | 657 | 0 |
| 2026 | 711 | 1,2,3,4,5 |  | 233 | 0 |

จำนวนเดือนครบไม่แปลว่าทุกสถานที่มีครบปี ปี 2017 เริ่มมีนาคม ปี 2026 สิ้นสุดพฤษภาคมตามขอบเขต

## Quality

| check | count |
|---|---|
| zero_assumed_cells | 2288 |
| zero_assumed_rows | 1509 |
| numeric_unresolved_rows | 0 |
| numeric_fractional_rows | 6 |
| numeric_negative_rows | 0 |
| exact_repeat_excess | 59 |
| repeated_survey_key_rows | 170 |
| report_date_unparseable_rows | 0 |
| survey_date_missing | 0 |
| survey_date_unparsed_nonblank | 0 |

เก็บทุกแถวใน staging ชุด candidate กันคีย์สำรวจซ้ำทุกสมาชิกและตัวเลขที่ยังไม่ยืนยันออกชั่วคราว จำนวน flag อาจทับซ้อน ไม่ถือว่าทุกแถวที่ flag เป็นข้อมูลผิด

ข้อความวัน/เดือน/ปีรองรับช่องว่างรอบ / และวันที่ไทย วันที่รายงานต่างจากวันที่สำรวจไม่ใช่เหตุให้ตัดแถว คอลัมน์ไม่มีชื่อยังไม่ใช้เป็นยอดรวมและยังไม่ตรวจ reconciliation กับ PDF ต้นทาง

## Matching

| design | groups | locations | intersections | rows | before_rows | during_rows | after_rows |
|---|---|---|---|---|---|---|---|
| raw_location | 357 | 357 | 177 | 5072 | 1587 | 1295 | 2190 |
| candidate_location | 357 | 357 | 177 | 5047 | 1587 | 1289 | 2171 |
| candidate_location_time | 623 | 352 | 175 | 2612 | 902 | 733 | 977 |
| candidate_report_month_time | 15 | 11 | 6 | 47 | 17 | 15 | 15 |
| candidate_report_quarter_time | 70 | 52 | 29 | 226 | 81 | 70 | 75 |
| candidate_survey_month_time | 15 | 11 | 6 | 47 | 17 | 15 | 15 |

location นับ intersection+road; unit/group นับคีย์ตาม design; rows นับการสังเกตที่มีจริง ต้องมี covid_period ทั้งสามค่า ไม่หมายถึงทุกปี ชื่อ normalize เฉพาะ Unicode กับ whitespace ไม่ fuzzy match

แบบรายเดือน/ไตรมาสรายงานและแบบเดือนสำรวจเป็นคนละนิยาม ใช้ดูความไวต่อชุดตัวอย่าง สำหรับ EDA ต้องคงเวลาเริ่ม–สิ้นสุดเดียวกัน คำนวณจำนวนรถต่อชั่วโมงตามชั่วโมงจริง และรายงาน sample ของแต่ละผล ห้ามอนุมานผลทั้งเมืองหรือปี 2026 จากการรวมกลุ่ม After หลายปี

## สถานะ

ข้อมูลมีชุด candidate สำหรับทำ Mini Project ต่อ ผู้ใช้อนุญาตให้ทำ EDA แล้ว ผล EDA อยู่ใน outputs/eda/EDA_Findings.md และ Notebook 02 ยังต้องตรวจ numeric_review.csv, duplicate_review.csv และชื่อสถานที่กับต้นทางก่อนส่งฉบับ Final
