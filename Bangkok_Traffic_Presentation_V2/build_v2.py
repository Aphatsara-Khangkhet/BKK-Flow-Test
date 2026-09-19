from pathlib import Path
import hashlib,json,shutil
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
plt.rcParams.update({'font.family':'Tahoma','axes.unicode_minus':False,'font.size':11})
for x in ['figures','tables']: (OUT/x).mkdir(exist_ok=True)
protected=[p for f in ['src','notebooks','outputs/presentation_refinement_v1'] for p in (ROOT/f).rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[ROOT/'Read.md',ROOT/'README.md']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
codes=['L03','L14','L13'];names=['บางขุนนนท์ / จรัญสนิทวงศ์','หลักสี่ / แจ้งวัฒนะ','หลักสี่ / กำแพงเพชร 6'];periods=['ก่อนโควิด','โควิด','หลังโควิด']
a=pd.read_csv(ROOT/'outputs/presentation_refinement_v1/case_evidence_audit.csv');loc=pd.read_csv(ROOT/'outputs/additional_visuals/location_code_lookup.csv').set_index('location_code').loc[codes];dates=pd.read_csv(ROOT/'outputs/diagnostics/case_survey_dates.csv');dates=dates[dates.location_code.isin(codes)];comp=pd.read_csv(ROOT/'outputs/additional_visuals/vehicle_mean_contributions.csv');comp=comp[comp.code.isin(codes)];boot=pd.read_csv(ROOT/'outputs/diagnostics/cluster_bootstrap.csv');sens=pd.read_csv(ROOT/'outputs/eda/sensitivity_summary.csv')
for df,n in [(a,'case_audit'),(loc.reset_index(),'case_indices'),(dates,'survey_dates'),(comp,'vehicle_components'),(boot,'bootstrap'),(sens,'matching_sensitivity')]:df.to_csv(OUT/'tables'/f'{n}.csv',index=False,encoding='utf-8-sig')
def finish(fig,name,note):
 fig.tight_layout(rect=(0,.13,1,.93));fig.text(.02,.025,note,fontsize=10);fig.savefig(OUT/'figures'/name,dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,4.6));ax.errorbar(boot.median_index,[1,0],xerr=[boot.median_index-boot.bootstrap_p025,boot.bootstrap_p975-boot.median_index],fmt='o',capsize=6,color='#176b87');ax.set_yticks([1,0],['During','After']);ax.axvline(100,color='gray',ls='--');ax.set_xlim(80,103);ax.set_ylim(-.4,1.5);ax.set_xlabel('ดัชนีเทียบ Before = 100');ax.set_title('ค่ากลางต่ำกว่าฐานในชุดที่จับคู่ได้ แต่ยังไม่ใช่ผลเชิงสาเหตุ')
for i,r in boot.iterrows():ax.annotate(f'{r.median_index:.1f} ({r.bootstrap_p025:.1f}–{r.bootstrap_p975:.1f})',(r.median_index,1-i),xytext=(0,12),textcoords='offset points',ha='center')
finish(fig,'01_overview.png','623 หน่วยถนน–เวลา / 175 ทางแยก; cluster bootstrap 3,000 รอบ\nช่วง 95% ไม่รวมความคลาดเคลื่อนต้นทาง การเลือกจุดสำรวจ และความต่างปฏิทิน')
fig,ax=plt.subplots(figsize=(11,5));y=np.arange(3)
for i,col in enumerate(['Before','During','After']):
 vals=loc[col]/loc.Before*100;ax.scatter(vals,y+(i-1)*.18,label=['Before','During','After'][i],s=65)
 for j,v in enumerate(vals):ax.annotate(f'{v:.1f}',(v,j+(i-1)*.18),xytext=(6,0),textcoords='offset points',va='center',fontsize=9)
ax.set_yticks(y,[n+'\nวันสำรวจ B/D/A = 2/2/3' for n in names]);ax.invert_yaxis();ax.axvline(100,color='gray',ls='--');ax.set_xlim(45,165);ax.legend(ncol=3,loc='lower right');ax.set_xlabel('ดัชนีจากมัธยฐานคัน/ชั่วโมง; Before = 100');ax.set_title('สามกรณีแสดงความเปลี่ยนแปลงต่างกัน')
finish(fig,'02_three_cases.png','เฉพาะ 07–09 น.; เลือกกรณีแบบเจาะจง ไม่ใช่ตัวแทนเมือง\nทั้งสามกรณีไม่มีเดือนสำรวจร่วมครบสามช่วง; ชื่อช่วงใช้ covid_period เดิม')
labels=['รถยนต์*','ตู้–ปิกอัพ','เมล์ใหญ่*','เมล์เล็ก','บรรทุก','สามล้อ'];vehicles=['passenger_car','pickup_van','large_bus','small_bus','truck','tuk_tuk'];fig,axs=plt.subplots(1,3,figsize=(14,5.6),sharex=True,sharey=True)
for ax,code,name in zip(axs,codes,names):
 g=comp[comp.code.eq(code)].set_index('vehicle').loc[vehicles];v=g.mean_vph_difference;ax.barh(labels,v,color=['#218c80' if x>=0 else '#c25b52' for x in v]);ax.axvline(0,color='gray');ax.set_title(name.replace(' / ','\n'));ax.set_xlabel('After − Before (คัน/ชั่วโมง)')
 for j,x in enumerate(v):ax.text(x+(8 if x>=0 else -8),j,f'{x:+.1f}',ha='left' if x>=0 else 'right',va='center',fontsize=9)
axs[0].invert_yaxis();axs[0].set_xlim(-950,800);fig.suptitle('รถประเภทใดประกอบเป็นผลต่าง: ใช้ค่าเฉลี่ยที่บวกแยกส่วนได้')
finish(fig,'03_vehicle_components.png','*รถยนต์รวมแท็กซี่/รถแวน; เมล์ใหญ่รวมรถทัวร์/สวัสดิการตามคู่มือ\nหกประเภทในไฟล์ ไม่ใช่ผู้เดินทางทั้งหมด; ไม่ใช่การแยกดัชนีมัธยฐาน และไม่ใช่การระบุสาเหตุ')
fig,ax=plt.subplots(figsize=(11,5));a=a.set_index('รหัส').loc[codes];v=a['After เทียบ Before (%)'];w=a['After ไม่รวมวันสำรวจ 2026 (%)'];ax.hlines(y,v,w,color='gray');ax.scatter(v,y,label='After ตามข้อมูลเดิม',s=70);ax.scatter(w,y,label='After ไม่รวมวันสำรวจ 2026',s=70,marker='D')
for j,(x,z) in enumerate(zip(v,w)):
 ax.annotate(f'{x:+.1f}%',(x,j),xytext=(0,12),textcoords='offset points',ha='center');ax.annotate(f'{z:+.1f}%',(z,j),xytext=(0,-19),textcoords='offset points',ha='center')
ax.set_yticks(y,names);ax.invert_yaxis();ax.axvline(0,color='gray',ls='--');ax.set_xlim(-55,60);ax.set_ylim(2.65,-.6);ax.set_xlabel('การเปลี่ยนมัธยฐานคัน/ชั่วโมง After เทียบ Before (%)');ax.legend(loc='lower right',fontsize=9);ax.set_title('ทิศทางคงเดิม แต่ขนาดผลบางแห่งไวต่อวันสำรวจปี 2026')
finish(fig,'04_2026_sensitivity.png','ผลประกอบ: After ลดจาก 3 เหลือ 2 วันต่อกรณี; ไม่เปลี่ยนผลหลัก\nไม่ได้พิสูจน์ว่าควรตัด 2026 และไม่ใช่ confidence interval')
readme='''# Bangkok Traffic: ภาพรวมต่ำกว่าฐาน แต่แต่ละสถานที่เปลี่ยนไม่เหมือนกัน

ฉบับนำเสนอ V2 | ข้อมูลฉบับร่าง มีนาคม 2017–พฤษภาคม 2026 | Pandas และ Matplotlib

## ผลสำคัญ

- ชุดสถานที่และเวลาเดียวกันมีมัธยฐานดัชนี During 91.6 และ After 90.4 เมื่อ Before = 100; ยังไม่พิสูจน์ว่าโควิดเป็นสาเหตุ
- บางขุนนนท์–จรัญสนิทวงศ์เพิ่ม 37.7% ขณะที่หลักสี่–แจ้งวัฒนะลด 28.5% ในสามกรณีที่คัดเลือก
- หลักสี่–กำแพงเพชร 6 มีรถยนต์ตามหมวดหน่วยงานลด แต่ตู้–ปิกอัพเพิ่ม; เมื่อไม่รวมวันสำรวจ 2026 ขนาดการลดของรถรวมเปลี่ยนจาก 39.6% เป็น 19.3%

## ที่มาและคำถาม

ใช้ผลสำรวจทางแยกที่เผยแพร่โดย [สำนักการจราจรและขนส่ง กรุงเทพมหานคร](https://traffic.bangkok.go.th/re_intersection/intersection/intersection.html) ผ่านไฟล์ที่รวบรวมชื่อ `bangkok_traffic_2560_Present (NotFinal) (1).xlsx` ชีต traffic_data จำนวน 17,005 แถว ไม่ใช่ข้อมูลต่อเนื่องของทุกแยกทุกวัน

คำถามคือ (1) หน่วยสถานที่–เวลาเดียวกันต่างกันระหว่างช่วงโควิดอย่างไร (2) แต่ละสถานที่เปลี่ยนเหมือนกันหรือไม่ และ (3) รถประเภทใดประกอบเป็นผลต่าง

ตาม [คู่มือ สจส. พ.ศ. 2564 หน้าเลขพิมพ์ 133–137](https://traffic.bangkok.go.th/TechnicalManuals/TTD.pdf#page=139) การสำรวจรองรับความต้องการข้อมูลและการวางแผน เช่น สัญญาณไฟ ทางข้าม และจุดกลับรถ แต่ยังไม่มีใบงานยืนยันเหตุผลการเลือกทุกจุดในไฟล์เรา

## วิธีวิเคราะห์

ใช้ covid_period ในไฟล์โดยตรง; Before 2017–2019, During 2020–2021, After 2022–พฤษภาคม 2026 ตามขอบเขตงาน ตัด 2016 แยกวันที่รายงานกับวันที่สำรวจจริง ค่าว่าง/ขีดของประเภทรถแทนศูนย์ตามข้อตกลง แต่ไม่เติมรายการสำรวจที่ไม่มี

คำนวณคันต่อชั่วโมงจากจำนวนหารชั่วโมงสำรวจ จับคู่ทางแยก+ถนน+เวลาเดียวกันครบสามช่วง ชุดหลักมี 2,612 แถว 623 หน่วย จาก 175 ทางแยก ใช้มัธยฐานภายในหน่วยและช่วง ก่อนสร้างดัชนีเทียบฐานของหน่วยเดียวกัน ไม่ใช้ยอดรวมคนละชุดสถานที่เป็นแนวโน้มเมือง

## 1. ภาพรวมพร้อมความไม่แน่นอน

![ภาพรวม](figures/01_overview.png)

จุดคือมัธยฐานดัชนี เส้นคือ percentile 95% จากการสุ่มซ้ำระดับทางแยก 3,000 รอบ: During 88.4–94.9, After 86.6–93.8 ช่วงทั้งคู่ต่ำกว่า 100 ภายใต้การสุ่มซ้ำนี้ แต่ไม่รวมอคติการเลือกสถานที่ ความผิดต้นทาง หรือความต่างฤดูกาล และไม่ใช่การทดสอบ After เทียบ During โดยตรง

## 2. ความต่างรายสถานที่

![สามกรณี](figures/02_three_cases.png)

คัดสามกรณีจากชุดที่มีการตรวจวันสำรวจและ leave-one-out แล้ว ให้มีทั้งเพิ่ม ลด และองค์ประกอบสวนทาง ไม่ใช่การสุ่มตัวแทน แต่ละกรณีมีวัน Before/During/After = 2/2/3 วัน และไม่มีเดือนสำรวจร่วมครบทั้งสามช่วง จึงไม่ถือว่าควบคุมฤดูกาลแล้ว

บางขุนนนท์เพิ่ม 37.7%; หลักสี่–แจ้งวัฒนะลด 28.5%; หลักสี่–กำแพงเพชร 6 ลด 39.6% ตัวเลขเป็นผลของหน่วยที่เลือก ไม่ใช่การจัดอันดับทั้งเมือง หลักฐานวันที่และแถว Excel อยู่ใน [survey_dates.csv](tables/survey_dates.csv)

## 3. องค์ประกอบของผลต่าง

![ประเภทรถ](figures/03_vehicle_components.png)

ค่าเฉลี่ยรถยนต์ของบางขุนนนท์เพิ่มประมาณ 646.2 คัน/ชั่วโมง ส่วนหลักสี่–กำแพงเพชร 6 ลดประมาณ 598.2 แต่ตู้–ปิกอัพเพิ่ม 133.9 คัน/ชั่วโมง ผลรวมแบบมีเครื่องหมายของหกประเภทเท่ากับผลต่างค่าเฉลี่ยรถรวม เป็นการแยกส่วนเชิงตัวเลข ไม่ใช่การแยกสาเหตุ และไม่ใช่ดัชนีมัธยฐานจากภาพก่อนหน้า

**นิยามที่แก้จากคำอธิบายเดิม:** รถยนต์รวมแท็กซี่/รถแวนตามคู่มือ จึงไม่เรียกว่า “รถส่วนตัว” ทั้งกลุ่ม; เมล์ใหญ่รวมรถทัวร์และสวัสดิการ จึงไม่เท่ากับรถประจำทางอย่างเดียว ผลรวมครอบคลุมรถหกหมวดที่บันทึก ไม่ใช่ยานพาหนะทุกประเภทหรือจำนวนผู้เดินทาง นิยามจากคู่มือ 2564 ยังต้องตรวจว่าคงเดิมทุกปีหรือไม่

## 4. ตรวจข้อสรุปก่อนนำไปใช้

![ความไวปี 2026](figures/04_2026_sensitivity.png)

เมื่อตัดวันสำรวจ 2026 ออกจาก After เพื่อดูความไว ทั้งสามกรณียังคงทิศทางเดิม แต่กำแพงเพชร 6 ลดจาก 39.6% เหลือ 19.3% แสดงว่าขนาดผลไวต่อวันสำรวจ ผลประกอบนี้เหลือ After เพียงสองวัน ไม่เสนอให้ลบข้อมูลหรือแทนผลหลัก

การตัดวันออกทีละรายการให้ช่วงการเปลี่ยนแปลง: บางขุนนนท์ +29.5 ถึง +47.1%; แจ้งวัฒนะ −37.1 ถึง −17.3%; กำแพงเพชร 6 −50.2 ถึง −19.3% ช่วงเหล่านี้ไม่ใช่ช่วงความเชื่อมั่น

เมื่อเพิ่มเงื่อนไขจับคู่เดือน ชุดหลัก 623 หน่วยเหลือ 15 หน่วย และ After เปลี่ยนจาก 90.4 เป็น 96.1 ขณะที่ During เปลี่ยนจาก 91.6 เป็น 85.5 ดังนั้นเรื่อง “After ฟื้นจาก During หรือไม่” ไวต่อการจับคู่และชุดสมาชิก ส่วนข้อสังเกตว่าทั้งคู่ต่ำกว่าฐานยังพบในแบบเหล่านี้ [ตารางผล](tables/matching_sensitivity.csv)

## ข้อเสนอแนะที่ข้อมูลรองรับ

1. เลือกพื้นที่สำรวจซ้ำโดยดูทั้งผลต่าง จำนวนวัน และความไวของผล
2. เก็บจุดเดิม เวลาเดิม เดือนและประเภทวันใกล้เคียงกัน เพื่อให้เปรียบเทียบได้ดีขึ้น
3. ทวนช่องศูนย์กับต้นทาง โดยเฉพาะรถพบน้อย ไม่ถือว่าสมมติฐานศูนย์ได้รับการยืนยันแล้ว
4. หากต้องการประเมินรถติดหรือปรับสัญญาณไฟ ต้องเพิ่มความเร็ว เวลาเดินทาง แถวคอย และทิศทางรถ

## ข้อจำกัดและสถานะข้อมูล

ยังมีค่าที่เคยพบไม่ตรง PDF ต้นทางใน L09 ซึ่งไม่นำมาเป็นกรณีหลักของฉบับนี้ แต่ยังอยู่ในผลภาพรวมเดิม การเลือกสามกรณีไม่ได้แปลว่าทวนต้นทางครบทุกแถว L13 มีหนึ่งแถวที่ใช้สมมติฐานศูนย์; L03/L14 ไม่มีในชุดกรณีนี้ ไม่มีข้อมูลปลายทาง ฝน ก่อสร้าง หรือกิจกรรมครบทุกวัน จึงไม่แต่งเหตุผลของความเปลี่ยนแปลง

## แหล่งอ้างอิง

- [รายงานปริมาณจราจร สจส.](https://traffic.bangkok.go.th/re_intersection/intersection/intersection.html): แหล่งต้นทาง
- [คู่มือ สจส.](https://traffic.bangkok.go.th/TechnicalManuals/TTD.pdf#page=139): วัตถุประสงค์และนิยาม ไม่ใช่ใบรับรองวิธีสำรวจทุกแถว
- [FHWA Traffic Monitoring Guide](https://www.fhwa.dot.gov/policyinformation/tmguide/tmg_2022/traffic-data-methodologies.cfm): หลักการคำนึงถึงเวลา วันและฤดูกาล ไม่อ้างว่า กทม. ใช้ทุกข้อ

## ไฟล์และการนำขึ้น GitHub

อัปโหลดเนื้อหาภายใน ZIP ทั้งหมดโดยให้ README.md อยู่ระดับเดียวกับ figures/ และ tables/ ลิงก์รูปจะเปิดได้ในหน้าแรก หากใช้ repository เดิมให้เพิ่มเป็นโฟลเดอร์ presentation_v2 แล้วลิงก์จาก README หลัก

ชุดนี้เป็นฉบับเล่าเรื่องพร้อมกราฟใหม่ ไม่ใช่โค้ดโปรเจคทั้งหมด ดู [บันทึกสิ่งที่เปลี่ยน](CHANGES.md) และ [แนวพูด](Speaker_Notes.md) โค้ด build_v2.py ใช้สร้างฉบับนี้ในโครงสร้างโปรเจคเดิม โดยอ่าน outputs ที่มีอยู่ ไม่รันแบบ standalone จาก ZIP อย่างเดียว

ก่อนส่งอาจารย์ยังต้องแนบโค้ด/Notebook เดิม เตรียม PDF ตามข้อกำหนด และเติมการแบ่งงานสมาชิกกับบทบาท AI ตามจริง ไม่กำหนดจำนวนกราฟเป็นเกณฑ์ของอาจารย์
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
(OUT/'CHANGES.md').write_text('''# ต่างจาก V1 และชุด 20 กราฟอย่างไร

- สร้างกราฟใหม่สี่ภาพ: ภาพรวมภาษาไทย, สามกรณีแบบเห็นชื่อ, ผลต่างรถเฉพาะสามกรณี, ความไวต่อ 2026
- ใช้นิยามจากคู่มือแก้ชื่อและการตีความในเนื้อหาและกราฟจริง
- README เป็นเรื่องราวครบ มีรูป สูตร ขอบเขต ผลสำคัญและข้อจำกัด ไม่ใช่สารบัญอย่างเดียว
- ใช้ผลเดิมเป็นหลัก ไม่อ้างว่ามีข้อมูลใหม่; ผลไม่รวม 2026 มาจากการคำนวณเพิ่มเติมใน V1
- ไม่แก้ src, notebooks, Read.md, README.md หลัก หรือเอกสาร V1 ตรวจ hash ก่อนและหลัง
- ไม่รวมกราฟสำรวจเบื้องต้นที่หลักฐานน้อยไว้ในเรื่องหลัก และไม่สรุปสาเหตุของโควิด
''',encoding='utf-8')
(OUT/'Speaker_Notes.md').write_text('''# แนวพูด 6 ช่วง

1. ที่มา: เราใช้รายงานนับรถตามจุดและวันสำรวจของ สจส. ถามว่าภาพรวมกับแต่ละพื้นที่ต่างกันอย่างไร
2. กราฟ 1: ดัชนีทั้งสองช่วงต่ำกว่าฐานในหน่วยที่จับคู่ได้ ความไม่แน่นอนนี้ยังไม่รวมอคติการเลือกสถานที่
3. กราฟ 2: เลือกสามกรณีแสดงว่าแต่ละพื้นที่เปลี่ยนไม่เหมือนกัน แต่มีข้อมูลเพียง 2/2/3 วัน และฤดูกาลไม่ตรงกัน
4. กราฟ 3: แยกส่วนด้วยค่าเฉลี่ย รถยนต์ในนิยามนี้รวมแท็กซี่ จึงไม่เรียกการเพิ่มว่าเปลี่ยนมาใช้รถส่วนตัว
5. กราฟ 4: ตรวจแล้วทิศทางคงเดิม แต่ขนาดผลกำแพงเพชร 6 ไวต่อวันสำรวจปี 2026 จึงเสนอสำรวจซ้ำ ไม่เสนอให้ลบปีนี้
6. ปิดด้วยสิ่งที่ทำได้: จับคู่และเก็บข้อมูลให้สม่ำเสมอ ทวนศูนย์ และเพิ่มความเร็ว/แถวคอยหากจะตอบเรื่องรถติด

คำถาม: โควิดมีผลไหม? คำตอบ: พบความแตกต่างระหว่างช่วงในข้อมูลที่จับคู่ แต่ยังแยกโควิดจากปัจจัยอื่นไม่ได้
คำถาม: ทำไมสามแยก? คำตอบ: คัดกรณีต่างรูปแบบจากชุดที่มีหลักฐานวันและผลความไวแล้ว ไม่ใช่ตัวแทนแบบสุ่ม
คำถาม: ทำไมกราฟ 2 กับ 3 ไม่เท่ากัน? คำตอบ: กราฟ 2 ใช้มัธยฐานและดัชนี กราฟ 3 ใช้ผลต่างค่าเฉลี่ยที่บวกแยกประเภทรถได้
''',encoding='utf-8')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in hashes.items())
for c in codes:
 g=dates[dates.location_code.eq(c)];med=g.groupby('covid_period').vehicles_per_hour.median();assert np.isclose((med['หลังโควิด']/med['ก่อนโควิด']-1)*100,a.loc[c,'After เทียบ Before (%)'])
(OUT/'validation.json').write_text(json.dumps({'original_files_unchanged':True,'protected_file_count':len(hashes),'case_indices_recomputed':True,'charts_generated':4},indent=2),encoding='utf-8')
zip_path=ROOT/'outputs/delivery/Bangkok_Traffic_Presentation_V2.zip'
with ZipFile(zip_path,'w',ZIP_DEFLATED) as z:
 for p in OUT.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(OUT))
print(zip_path)
