# ข้อสรุปใดคงอยู่เมื่อเปลี่ยนเงื่อนไข

## การจับคู่

| design | rows | units | Before | During | After |
| --- | --- | --- | --- | --- | --- |
| same_location_time | 2612 | 623 | 100.0 | 91.588 | 90.357 |
| same_report_quarter | 226 | 70 | 100.0 | 87.677 | 87.82 |
| same_report_month | 47 | 15 | 100.0 | 85.491 | 96.137 |
| same_survey_month | 47 | 15 | 100.0 | 85.491 | 96.137 |

ทุกแบบที่แสดงมี During และ After ต่ำกว่า 100 แต่ทิศทาง After เทียบ During เปลี่ยน: ชุดหลัก After ต่ำกว่า During ขณะที่ชุดเดือนตรงกัน After สูงกว่า During จึงไม่สรุปการฟื้นตัวแบบเดียวกันทุกวิธี ชุดตัวอย่างลดจาก 623 เหลือ 15 หน่วย ไม่ใช่การทดลองเปลี่ยนเงื่อนไขบนสมาชิกเดิมทั้งหมด

## สมมติฐานศูนย์

| design | rows | units | During | After |
| --- | --- | --- | --- | --- |
| main_zero_assumption | 2612 | 623 | 91.588 | 90.357 |
| main_restricted_to_complete_units | 1913 | 440 | 92.086 | 91.168 |
| complete_numeric_only | 1858 | 440 | 91.831 | 91.101 |

เปรียบเทียบบน 440 หน่วยร่วม: After 91.168 กับ 91.101 ต่างประมาณ 0.07 จุดดัชนี ภาพรวมใกล้กัน แต่ไม่พิสูจน์ว่าศูนย์ถูกต้องทุกช่อง และการตัดแถวยังเปลี่ยนวันสำรวจ คงวิธีศูนย์เป็นวิธีหลักตามข้อตกลง

## วันในสัปดาห์

| design | units | During | After |
| --- | --- | --- | --- |
| same_weekday | 50 | 92.147 | 88.992 |
| same_survey_month_weekday | 0 | — | — |

เดือนสำรวจและวันในสัปดาห์ตรงกันไม่เหลือหน่วยครบสามช่วง จึงไม่อ้างว่าได้ควบคุมปฏิทินครบแล้ว

## สัดส่วนประเภทรถ

| design | vehicle | Before_share | After_share | change_pp | units |
| --- | --- | --- | --- | --- | --- |
| main | passenger_car | 71.922 | 73.513 | 1.591 | 621 |
| main | pickup_van | 21.625 | 21.032 | -0.594 | 621 |
| main | large_bus | 2.209 | 1.889 | -0.32 | 621 |
| main | small_bus | 0.397 | 0.252 | -0.145 | 621 |
| main | truck | 0.956 | 1.228 | 0.271 | 621 |
| main | tuk_tuk | 2.891 | 2.087 | -0.804 | 621 |
| original_common_units | passenger_car | 73.138 | 74.155 | 1.017 | 440 |
| original_common_units | pickup_van | 21.104 | 20.65 | -0.454 | 440 |
| original_common_units | large_bus | 2.192 | 1.993 | -0.199 | 440 |
| original_common_units | small_bus | 0.481 | 0.291 | -0.19 | 440 |
| original_common_units | truck | 0.858 | 1.156 | 0.297 | 440 |
| original_common_units | tuk_tuk | 2.227 | 1.756 | -0.471 | 440 |
| complete_numeric_common_units | passenger_car | 73.138 | 74.238 | 1.1 | 440 |
| complete_numeric_common_units | pickup_van | 21.104 | 20.587 | -0.517 | 440 |
| complete_numeric_common_units | large_bus | 2.192 | 2.001 | -0.191 | 440 |
| complete_numeric_common_units | small_bus | 0.481 | 0.291 | -0.189 | 440 |
| complete_numeric_common_units | truck | 0.858 | 1.151 | 0.293 | 440 |
| complete_numeric_common_units | tuk_tuk | 2.227 | 1.731 | -0.496 | 440 |

ใช้ change_pp เป็นจุดเปอร์เซ็นต์ ไม่ใช่ร้อยละการเปลี่ยนจำนวนรถ ตรวจจำนวน units ของแต่ละแบบก่อนเทียบ
