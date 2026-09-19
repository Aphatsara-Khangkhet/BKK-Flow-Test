from pathlib import Path
import numpy as np,pandas as pd,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path.cwd()
PATTERN_FIGURES={'17_daily_profile.png':'รูปแบบปริมาณรถภายในวันเดียวกัน','18_location_vehicle_mix.png':'องค์ประกอบรถรายสถานที่','19_road_concentration.png':'การกระจุกตัวบนถนนที่รายงานในแยก','20_sampling_priority.png':'ความครอบคลุมและความแปรปรวนของข้อมูล'}
def run_patterns():
 out=ROOT/'outputs/traffic_patterns';out.mkdir(parents=True,exist_ok=True);(out/'figures').mkdir(exist_ok=True)
 d=pd.read_csv(ROOT/'data/processed/traffic_analysis_candidates.csv',low_memory=False)
 # Focus on latest three complete report years, keep actual survey years in the same window.
 d=d[d.report_year.between(2023,2025)&d.survey_year.between(2023,2025)].copy()
 loc=['intersection_key','road_key'];times=['07:00-09:00','09:00-16:00','16:00-19:00'];vs=['passenger_car','pickup_van','large_bus','small_bus','truck','tuk_tuk']
 def save(x,n):x.to_csv(out/n,index=False,encoding='utf-8-sig')
 def tab(x):
  x=x.round(3).fillna('NA');return '\n'.join(['| '+' | '.join(x.columns)+' |','| '+' | '.join(['---']*len(x.columns))+' |']+['| '+' | '.join(map(str,r))+' |' for r in x.values])
 def finish(fig,n,note):
  fig.tight_layout(rect=(0,.19,1,.94));fig.text(.015,.025,note,fontsize=9);fig.savefig(out/'figures'/n,dpi=150);plt.close(fig)
 # Exact-window same-day profiles. No mixing of 9-16 with 9-17.
 visits=d[d.time_key.isin(times)].pivot_table(index=loc+['survey_date_parsed'],columns='time_key',values='vehicles_per_hour',aggfunc='median').reindex(columns=times).dropna()
 visits=visits[visits[times[1]]>0];ratios=visits.div(visits[times[1]],axis=0)
 prof=ratios.groupby(level=loc).median();n=ratios.groupby(level=loc).size();prof['visits']=n
 prof=prof.sort_values([times[0],times[2]],ascending=False);prof['code']=[f'P{i:02}' for i in range(1,len(prof)+1)]
 save(prof.reset_index(),'daily_profile_all.csv');save(visits.reset_index(),'complete_day_observations.csv')
 show=prof.head(20);fig,ax=plt.subplots(figsize=(9,max(5,len(show)*.3)))
 im=ax.imshow(show[times].values,aspect='auto',cmap='YlOrRd',vmin=0,vmax=max(2,float(show[times].max().max())))
 ax.set_yticks(range(len(show)),[f'{r.code} (n={r.visits})' for r in show.itertuples()]);ax.set_xticks(range(3),['07-09','09-16','16-19']);ax.set_title(f'17. Same-day profiles: top {len(show)} morning/midday ratios');fig.colorbar(im,ax=ax,label='Ratio to same-day midday vehicles/hour')
 for i,row in enumerate(show[times].values):
  for j,v in enumerate(row):ax.text(j,i,f'{v:.2f}',ha='center',va='center',fontsize=8)
 finish(fig,'17_daily_profile.png',f'Report and survey years 2023-2025. {len(prof)} eligible locations, {len(visits)} complete location-days.\nWithin-day ratios, then median per location. n may be 1; exploratory profile, not a stable location classification.')
 # Mix by same window, retain all eligible locations and select displayed by counts.
 am=d[d.time_key.eq(times[0])&d.vehicle_total.gt(0)].copy()
 count=am.groupby(loc).survey_date_parsed.nunique();eligible=count[count>=2].reset_index()[loc];am=am.merge(eligible,on=loc)
 for v in vs:am[v+'_share']=am[v+'_clean']/am.vehicle_total*100
 mix=am.groupby(loc)[[v+'_share' for v in vs]].mean();mix['visits']=am.groupby(loc).survey_date_parsed.nunique();mix=mix.sort_values(['visits','passenger_car_share'],ascending=[False,False]);mix['code']=[f'V{i:02}' for i in range(1,len(mix)+1)];save(mix.reset_index(),'vehicle_mix_all.csv')
 show=mix.head(20);fig,ax=plt.subplots(figsize=(11,max(5,len(show)*.32)));left=np.zeros(len(show))
 for v,label,col in zip(vs,['Passenger car','Pickup/van','Large bus','Small bus','Truck','Tuk-tuk'],plt.get_cmap('tab10').colors):
  a=show[v+'_share'].values;ax.barh(show.code,a,left=left,label=label,color=col);left+=a
 ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Mean observation share (%)');ax.set_title(f'18. Morning vehicle composition: {len(show)} locations');ax.legend(ncol=3,fontsize=8,loc='upper left',bbox_to_anchor=(0,-.12))
 finish(fig,'18_location_vehicle_mix.png',f'2023-2025; 07:00-09:00; at least two distinct survey days. {len(mix)} eligible locations.\nEqual weight per observation within location; displayed by most survey days, then car share. Missing/dash = 0.')
 # Road-set coverage: retained only modal identical observed set on >=2 days.
 groups=[];lookup=[]
 morning=d[d.time_key.eq(times[0])]
 for name,g in morning.groupby('intersection_key'):
  sets=g.groupby('survey_date_parsed').road_key.agg(lambda s:tuple(sorted(set(s))))
  sets=sets[sets.map(len)>=2]
  if sets.empty:continue
  freq=sets.value_counts();best=sorted(freq[freq.eq(freq.max())].index)[0]
  days=sets[sets.map(lambda z:z==best)].index
  if len(days)<2:continue
  z=g[g.survey_date_parsed.isin(days)];p=z.pivot(index='survey_date_parsed',columns='road_key',values='vehicles_per_hour');tot=p.sum(axis=1);p=p[tot>0];tot=tot[tot>0]
  if len(p)<2:continue
  sh=p.div(tot,axis=0);groups.append({'intersection':name,'days':len(p),'roads':len(best),'median_largest_road_share':sh.max(axis=1).median()*100,'equal_share_reference':100/len(best),'road_set':' / '.join(best)})
  for day,row in sh.iterrows():
   for road,value in row.items():lookup.append({'intersection':name,'survey_date':day,'road':road,'share_pct':value*100})
 conc=pd.DataFrame(groups).sort_values('median_largest_road_share',ascending=False);conc['code']=[f'J{i:02}' for i in range(1,len(conc)+1)];save(conc,'road_concentration.csv');save(pd.DataFrame(lookup),'road_day_shares.csv')
 show=conc.head(20);fig,ax=plt.subplots(figsize=(10,max(5,len(show)*.3)));ax.barh(show.code,show.median_largest_road_share,color='#287a9a');ax.scatter(show.equal_share_reference,show.code,color='#b96931',label='Equal-share reference');ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Median largest observed-road share (%)');ax.set_title('19. Concentration within a repeated observed road set');ax.legend()
 finish(fig,'19_road_concentration.png',f'2023-2025 mornings; {len(conc)} intersections, modal identical observed road set on >=2 days.\nObserved sets are NOT verified as all intersection arms. Largest road may differ by day; not turning-flow data.')
 # Coverage vs dispersion, exact same morning window, >=3 dates.
 q=morning.groupby(loc).vehicles_per_hour.agg(median='median',q25=lambda x:x.quantile(.25),q75=lambda x:x.quantile(.75));q['days']=morning.groupby(loc).survey_date_parsed.nunique();q['months']=morning.groupby(loc).survey_month.nunique();q['years']=morning.groupby(loc).survey_year.nunique();q['zero_assumed_rows']=morning.groupby(loc).has_assumed_zero.sum();q=q[(q.days>=3)&(q['median']>0)].copy();q['relative_iqr']=(q.q75-q.q25)/q['median'];q=q.sort_values('relative_iqr',ascending=False);q['code']=[f'S{i:02}' for i in range(1,len(q)+1)];save(q.reset_index(),'sampling_priority.csv')
 show=q.head(20);fig,ax=plt.subplots(figsize=(10,7));sc=ax.scatter(show.relative_iqr,range(len(show)),c=show.months,cmap='viridis',s=65,edgecolors='white');fig.colorbar(sc,ax=ax,label='Distinct calendar months sampled')
 ax.set_yticks(range(len(show)),[f'{r.code} (n={r.days})' for r in show.itertuples()]);ax.invert_yaxis();ax.set_xlim(left=0);ax.set_xlabel('IQR / median vehicles per hour');ax.set_title(f'20. Sampling review: top 20 of {len(q)} eligible locations')
 finish(fig,'20_sampling_priority.png','2023-2025 mornings; >=3 dates and positive median. n = distinct survey dates.\nDispersion includes calendar and year changes. Priority for DATA review, not congestion; only three dates per eligible location.')
 result={'window':'report AND survey years 2023-2025','complete_days':len(visits),'profile_locations':len(prof),'vehicle_mix_locations':len(mix),'concentration_intersections':len(conc),'sampling_locations':len(q),'source_sha256':d.source_sha256.iloc[0]}
 (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 report='# รูปแบบปริมาณรถและความต้องการข้อมูลเพิ่มเติม\n\nใช้ปีรายงานและปีสำรวจ 2023–2025 ซึ่งเป็นสามปีเต็มล่าสุดในไฟล์ ไม่ใช้ COVID เป็นแกนเปรียบเทียบ ไม่เปลี่ยน label เดิม และไม่รวมปี 2026 บางปี\n\n'
 a=prof.reset_index().iloc[0];b=mix.reset_index().iloc[0];c=conc.iloc[0];e=q.reset_index().iloc[0]
 report+=f"## ข้อค้นพบที่ใช้เล่าเรื่องได้\n\n- {a.intersection_key} / {a.road_key}: ช่วงเช้ามีรถต่อชั่วโมง {a[times[0]]:.2f} เท่าของกลางวัน แต่มีวันครบสามช่วงเพียง {a.visits} วัน จึงเป็นข้อสังเกตของวันนั้น ไม่ยืนยันรูปแบบประจำ\n- {b.intersection_key} / {b.road_key}: รถยนต์นั่งเฉลี่ย {b.passenger_car_share:.2f}% จาก {b.visits} วันสำรวจเช้า เป็นสัดส่วนในรถหกประเภทที่ไฟล์บันทึก ไม่ใช่สัดส่วนผู้เดินทางทั้งหมด\n- แยก{c.intersection}: ค่ามัธยฐานส่วนแบ่งถนนที่มีรถมากที่สุด {c.median_largest_road_share:.2f}% ในชุดถนน {c.roads} สายที่รายงานซ้ำ {c.days} วัน เหมาะทวนความครบถ้วนของถนนก่อนอธิบายความต่าง\n- {e.intersection_key} / {e.road_key}: IQR/median={e.relative_iqr:.3f} จาก {e.days} วัน ควรเก็บซ้ำในเดือนและวันประเภทเดียวกันเพื่อแยกความเปลี่ยนแปลงตามเวลาออกจากความผันผวน\n\nกราฟ 19 เลือกชุดถนนที่พบซ้ำบ่อยที่สุด หากความถี่เท่ากันเลือกตามลำดับชื่อ ชุดอื่นจึงไม่รวมในผลนี้\n\n"
 texts=[('17_daily_profile.png','เทียบปริมาณเช้า/กลางวัน/เย็นจากวันและถนนเดียวกัน โดยกลางวัน=1 ใช้เวลา 09–16 เท่านั้น ไม่รวม 09–17 รหัส P แสดงชื่อใน CSV; เลือก 20 อันดับอัตราส่วนเช้าสูงสุด ไม่ใช่ตัวแทนทั้งเมือง วันสำรวจน้อยยังบอกบุคลิกถาวรของพื้นที่ไม่ได้',prof.reset_index().head(20)),('18_location_vehicle_mix.png','แต่ละแท่งแสดงค่าเฉลี่ยสัดส่วนรถรายวันในช่วงเช้า ต้องมีอย่างน้อยสองวัน รถจำนวนเท่ากันอาจมีองค์ประกอบต่างกัน ไม่อนุมานปลายทางหรือวัตถุประสงค์จากประเภทรถ',mix.reset_index().head(20)),('19_road_concentration.png','คัดเฉพาะชุดถนนที่ปรากฏเหมือนกันซ้ำอย่างน้อยสองวัน จุดส้มคือสัดส่วนถ้าแบ่งเท่ากันทุกถนนในชุดนั้น ชุดที่รายงานยังไม่ยืนยันว่าครบทุกแขนแยก จึงใช้คำว่าส่วนแบ่งในถนนที่รายงาน ไม่ใช่การไหลทั้งแยก',conc.head(20)),('20_sampling_priority.png','แกนนอน IQR/median แกนตั้งรหัสสถานที่ พร้อมจำนวนวัน n สีแสดงจำนวนเดือนปฏิทินที่ครอบคลุม แสดง 20 อันดับสูงสุดจาก 40 สถานที่ ซึ่งทุกแห่งมีเพียง 3 วัน ค่าสูงและข้อมูลน้อยควรตรวจหรือเก็บเพิ่ม ยังไม่สร้างคะแนนความสำคัญด้วยน้ำหนักตามใจ และไม่ใช่อันดับรถติด',q.reset_index().head(15))]
 for filename,explain,frame in texts:report+='\n## '+PATTERN_FIGURES[filename]+'\n\n![]('+str(Path('figures')/filename).replace('\\','/')+')\n\n'+explain+'\n\n'+tab(frame)+'\n'
 report+='\n## ข้อจำกัดร่วม\n\nค่าว่าง/ขีดเป็นศูนย์ตามข้อตกลง; ความคลาดเคลื่อนต้นทางที่เคยพบยังต้องทวน การใช้ช่วงปีเดียวกันไม่รับรองเดือนและวันตรงกันระหว่างพื้นที่ กราฟเป็นผลเชิงพรรณนาของสถานที่ที่ผ่านเกณฑ์ ไม่ใช่ตัวแทนรถทั้งหมดในกรุงเทพฯ\n'
 (out/'Pattern_Findings.md').write_text(report,encoding='utf-8');print(json.dumps(result,ensure_ascii=False));return result
if __name__=='__main__':run_patterns()
