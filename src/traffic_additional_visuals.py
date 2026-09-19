"""Figures 11-16: additional evidence views, with reviewed geographic snapshot."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import TwoSlopeNorm
from matplotlib.path import Path as MplPath
import seaborn as sns
ROOT=Path.cwd()
NEW_FIGURES={'11_location_period_heatmap.png':'Heatmap สถานที่กับช่วงโควิด','12_case_survey_dates.png':'วันสำรวจจริงรายสถานที่','13_location_bubbles.png':'ปริมาณฐานกับการเปลี่ยนแปลงรายสถานที่','14_vehicle_contributions.png':'ผลต่างค่าเฉลี่ยแยกประเภทรถ','15_cluster_uncertainty.png':'ดัชนีพร้อมช่วงความไม่แน่นอน','16_bangkok_matched_map.png':'แผนที่กรุงเทพฯ เฉพาะทางแยกที่ตรวจพิกัดได้'}
def run_additional_visuals():
 out=ROOT/'outputs/additional_visuals';out.mkdir(parents=True,exist_ok=True);(out/'figures').mkdir(exist_ok=True)
 def save(df,n):df.to_csv(out/n,index=False,encoding='utf-8-sig')
 def finish(fig,n,note,bottom=.16):
  fig.tight_layout(rect=(0,bottom,1,.95));fig.text(.015,.015,note,fontsize=9,va='bottom');fig.savefig(out/'figures'/n,dpi=150,facecolor='white');plt.close(fig)
 sns.set_theme(style='whitegrid',font='DejaVu Sans',font_scale=.95)
 r=pd.read_csv(ROOT/'outputs/eda/morning_location_ranking_all.csv')
 c=pd.read_csv(ROOT/'outputs/diagnostics/case_survey_dates.csv');c['survey_date_parsed']=pd.to_datetime(c.survey_date_parsed)
 idx=pd.read_csv(ROOT/'outputs/eda/same_location_time_paired_indices.csv');vph=pd.read_csv(ROOT/'outputs/eda/same_location_time_paired_vph.csv')
 key=['intersection_key','road_key'];p=['Before','During','After'];colors={'ก่อนโควิด':'#777777','โควิด':'#c16b37','หลังโควิด':'#247ba0'}
 common_note='Source: supplied traffic_data; draft snapshot. Six vehicle classes; missing / dash = 0. Not a causal COVID estimate.'
 # 11 uses eligible repeated morning observations, not selected top/bottom only.
 heat=r[['location_code']+key+['n_Before','n_During','n_After']].merge(idx[idx.time_key.eq('07:00-09:00')],on=key).sort_values('After')
 save(heat,'location_period_heatmap.csv');save(r,'location_code_lookup.csv')
 fig,ax=plt.subplots(figsize=(9,9));vals=heat[p].to_numpy();norm=TwoSlopeNorm(vmin=min(40,float(vals.min())),vcenter=100,vmax=max(160,float(vals.max())))
 sns.heatmap(heat.set_index('location_code')[p],annot=True,fmt='.1f',cmap='RdBu_r',norm=norm,cbar_kws={'label':'Paired index (Before = 100)'},ax=ax)
 ax.set_yticklabels([f'{z.location_code} (n={z.n_Before}/{z.n_During}/{z.n_After})' for z in heat.itertuples()],rotation=0);ax.set_xlabel('Supplied COVID period');ax.set_ylabel('Location code; observations Before / During / After');ax.set_title(f'Figure 11. Morning traffic indices by location (n={len(heat)})')
 finish(fig,'11_location_period_heatmap.png',common_note+'\n07:00-09:00 only; >=2 observations per period. Codes and Thai road names in location_code_lookup.csv.\nL09 includes a known 2017 source discrepancy; values remain as supplied.',.14)
 # 12 actual dates with shared time axis, individual y scales clearly disclosed.
 codes=sorted(c.location_code.unique());fig,axes=plt.subplots(5,2,figsize=(13,16),sharex=True)
 for ax,code in zip(axes.flat,codes):
  g=c[c.location_code.eq(code)]
  for label,color in colors.items():
   z=g[g.covid_period.eq(label)];ax.scatter(z.survey_date_parsed,z.vehicles_per_hour,c=color,s=40,label={'ก่อนโควิด':'Before','โควิด':'During','หลังโควิด':'After'}[label])
  near=g[g.calendar_screen.str.startswith(('near_','day_after_'))];ax.scatter(near.survey_date_parsed,near.vehicles_per_hour,facecolors='none',edgecolors='#d99b00',s=135,linewidths=1.8)
  ax.set_title(f'{code} | n={len(g)}',fontsize=11);ax.set_ylabel('Vehicles/hour');ax.set_ylim(bottom=0)
  ax.xaxis.set_major_locator(mdates.YearLocator(2));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
 axes[0,0].legend(fontsize=8);fig.suptitle('Figure 12. Actual survey dates at ten selected locations',fontweight='bold');save(c,'case_survey_dates.csv')
 finish(fig,'12_case_survey_dates.png',common_note+'\n68 observations at 10 selected locations. Separate y scales; no interpolation between sparse survey days.\nGold ring = selected calendar proximity flag, not confirmed holiday impact. L09 source discrepancy unresolved.',.08)
 # 13 bubble chart same 17 eligible, baseline volume vs proportional change.
 bubble=r.copy();bubble['total_n']=bubble[['n_Before','n_During','n_After']].sum(axis=1);save(bubble,'location_bubble_data.csv')
 fig,ax=plt.subplots(figsize=(11,7));ax.scatter(bubble.Before,bubble.after_change_pct,s=bubble.total_n*22,c=np.where(bubble.after_change_pct>=0,'#bf6532','#28649c'),alpha=.7,edgecolors='white')
 for i,z in enumerate(bubble.itertuples()):ax.annotate(z.location_code,(z.Before,z.after_change_pct),xytext=(5,5 if i%2 else -12),textcoords='offset points',fontsize=8)
 
 for n in [6,10]:ax.scatter([],[],s=n*22,c='#777777',alpha=.6,label=f'n={n} observations')
 ax.legend(loc='upper right',fontsize=9)
 ax.axhline(0,color='#666666',ls='--');med=bubble.Before.median();ax.axvline(med,color='#aaaaaa',ls=':');ax.set_xlabel('Before median vehicles/hour');ax.set_ylabel('After versus Before change (%)');ax.set_title(f'Figure 13. Baseline volume and subsequent change (n={len(bubble)})')
 finish(fig,'13_location_bubbles.png',common_note+'\n07:00-09:00; bubble area = total observations across all three periods.\nVertical line = sample median baseline, not road capacity. No congestion or intervention threshold.',.18)
 # 14 additive arithmetic-mean differences, not median decomposition.
 comp=pd.read_csv(ROOT/'outputs/diagnostics/case_vehicle_mean_decomposition.csv');save(comp,'vehicle_mean_contributions.csv')
 vs=['passenger_car','pickup_van','large_bus','small_bus','truck','tuk_tuk'];labs=['Passenger car','Pickup / van','Large bus','Small bus','Truck','Tuk-tuk'];palette=sns.color_palette('tab10',6)
 pivot=comp.pivot(index='code',columns='vehicle',values='mean_vph_difference').reindex(columns=vs).sort_index();fig,ax=plt.subplots(figsize=(12,8));pos=np.zeros(len(pivot));neg=pos.copy()
 for v,label,color in zip(vs,labs,palette):
  a=pivot[v].values;left=np.where(a>=0,pos,neg);ax.barh(pivot.index,a,left=left,label=label,color=color);pos+=np.maximum(a,0);neg+=np.minimum(a,0)
 ax.axvline(0,color='black',lw=.8);ax.set_xlabel('After mean minus Before mean (vehicles/hour)');ax.set_ylabel('Location code');ax.legend(ncol=3,loc='upper left',bbox_to_anchor=(0,-.12),fontsize=9);ax.set_title('Figure 14. Vehicle-type contributions to mean volume differences')
 finish(fig,'14_vehicle_contributions.png',common_note+'\n10 selected locations, morning only. Six signed components sum to the arithmetic-mean total difference.\nThis is not a decomposition of the median index and does not identify causes. L09 remains uncorrected.',.23)
 # 15 existing validated cluster bootstrap.
 ci=pd.read_csv(ROOT/'outputs/diagnostics/cluster_bootstrap.csv');save(ci,'cluster_bootstrap.csv');fig,ax=plt.subplots(figsize=(9,5.5))
 for i,z in ci.iterrows():ax.errorbar(z.median_index,i,xerr=[[z.median_index-z.bootstrap_p025],[z.bootstrap_p975-z.median_index]],fmt='o',capsize=6,color=['#bf6532','#28649c'][i],markersize=8);ax.text(z.bootstrap_p975+.5,i,f'{z.median_index:.1f} [{z.bootstrap_p025:.1f}, {z.bootstrap_p975:.1f}]',va='center',fontsize=10)
 ax.axvline(100,color='#666666',ls='--');ax.set_yticks(range(2),ci.period);ax.set_xlim(82,105);ax.set_ylim(-.6,1.6);ax.set_xlabel('Median paired index (Before = 100)');ax.set_title('Figure 15. Conditional uncertainty in matched-sample indices')
 finish(fig,'15_cluster_uncertainty.png',common_note+'\n623 units / 175 intersection clusters; 3,000 bootstrap samples, seed 5001, percentile 95% intervals.\nIntervals exclude selection bias, calendar confounding and source transcription uncertainty.',.22)
 # 16 only exact road matches; select morning and retain each road in evidence table.
 coords=pd.read_csv(ROOT/'data/reference/map_coordinates_reviewed.csv');geo=json.loads((ROOT/'data/reference/bangkok_boundary.geojson').read_text(encoding='utf-8'))
 geometry=geo['features'][0]['geometry'];polys=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
 def inside(lon,lat):return any(MplPath(poly[0]).contains_point((lon,lat)) and not any(MplPath(h).contains_point((lon,lat)) for h in poly[1:]) for poly in polys)
 coords['inside_bangkok_boundary']=coords.apply(lambda z:inside(z.longitude,z.latitude),axis=1);coords=coords[coords.inside_bangkok_boundary].copy()
 maprows=idx[idx.time_key.eq('07:00-09:00')].merge(coords,on=key,validate='one_to_one');save(maprows,'map_road_period_indices.csv')
 mapped=maprows.groupby(['intersection_key','latitude','longitude']).agg(During=('During','median'),After=('After','median'),road_units=('road_key','size')).reset_index();mapped['map_code']=[f'M{i:02}' for i in range(1,len(mapped)+1)];save(mapped,'map_intersection_summary.csv')
 fig,axes=plt.subplots(1,3,figsize=(15,7));lat0=13.75
 def draw(ax):
  for poly in polys:
   for ring in poly:
    arr=np.asarray(ring);ax.plot(arr[:,0],arr[:,1],color='#929ba5',lw=.8)
  ax.set_aspect(1/np.cos(np.deg2rad(lat0)));ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
 for ax in axes:draw(ax)
 axes[0].scatter(mapped.longitude,mapped.latitude,color='#334155',s=15);axes[0].set_title('Bangkok boundary and mapped sample')
 dmax=max(40,float(np.abs(mapped[['During','After']]-100).to_numpy().max()));norm=TwoSlopeNorm(vmin=-dmax,vcenter=0,vmax=dmax)
 for ax,label in zip(axes[1:],['During','After']):
  sc=ax.scatter(mapped.longitude,mapped.latitude,c=mapped[label]-100,norm=norm,cmap='RdBu_r',s=60,edgecolors='white',linewidths=.5)
  ax.set_xlim(mapped.longitude.min()-.015,mapped.longitude.max()+.015);ax.set_ylim(mapped.latitude.min()-.015,mapped.latitude.max()+.015);ax.set_title(f'{label} vs Before: mapped area zoom')
 fig.colorbar(sc,ax=axes[1:],label='Median road-unit index minus 100 (points)',fraction=.035,pad=.04)
 fig.suptitle(f'Figure 16. Bangkok traffic change at {len(mapped)} reviewed intersections',fontweight='bold');fig.subplots_adjust(bottom=.25,top=.86,wspace=.32,right=.9)
 fig.text(.015,.025,f'Source: supplied traffic_data; {len(maprows)} matched morning road units at {len(mapped)} mapped intersections, not citywide coverage.\nCoordinates: OpenStreetMap contributors (ODbL), reviewed by exact connected-road names; boundary: geoBoundaries gbOpen THA ADM1 (ODbL).\nOne marker aggregates median road-unit indices; underlying roads may differ. Current reference coordinates are not historical survey GPS.\nNo geographic interpolation. Grey outline is Bangkok; no points does not mean zero traffic.',fontsize=9);fig.savefig(out/'figures'/'16_bangkok_matched_map.png',dpi=150,facecolor='white');plt.close(fig)
 # Reproducible evidence receipt.
 receipt={'figures':list(NEW_FIGURES),'heatmap_locations':len(heat),'case_rows':len(c),'case_locations':len(codes),'bubble_locations':len(bubble),'bubble_n_values':sorted(map(int,bubble.total_n.unique())),'map_intersections':len(mapped),'map_road_units':len(maprows),'map_unmapped_intersections_from_main':int(idx.intersection_key.nunique()-len(mapped)),'source_discrepancy_preserved':True}
 (out/'summary.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');write_interactive_map(ROOT);print(json.dumps(receipt,ensure_ascii=False,indent=2));return receipt
from pathlib import Path
import json
import pandas as pd

def write_interactive_map(root):
    out=root/'outputs/additional_visuals'
    points=pd.read_csv(out/'map_intersection_summary.csv').to_dict('records')
    roads=pd.read_csv(out/'map_road_period_indices.csv').to_dict('records')
    geo=json.loads((root/'data/reference/bangkok_boundary.geojson').read_text(encoding='utf-8'))
    payload=json.dumps({'points':points,'roads':roads,'geo':geo},ensure_ascii=False).replace('<','\\u003c')
    page='''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bangkok matched traffic map</title><style>
body{font:16px system-ui,sans-serif;margin:0;background:#f4f6f8;color:#182535}main{max-width:1250px;margin:auto;padding:24px}h1{font-size:26px;margin:0 0 10px}p{line-height:1.6}label{margin-right:18px}select{padding:8px;border:1px solid #bbc7d3;border-radius:6px}.layout{display:grid;grid-template-columns:1.6fr 1fr;gap:20px;margin-top:16px}.panel{background:white;border:1px solid #d7dfe6;border-radius:12px;padding:16px}svg{width:100%;height:570px;background:#edf3f7}circle{cursor:pointer;stroke:white;stroke-width:.0007}circle:focus{outline:none;stroke:#101820;stroke-width:.002}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:8px;border-bottom:1px solid #ddd;text-align:left}a{color:#17639c}.legend{display:flex;align-items:center;gap:8px;font-size:14px;margin:10px 0}.sw{width:15px;height:15px;border-radius:50%;display:inline-block}.note{font-size:14px;color:#526171}#tooltip{position:fixed;z-index:10;max-width:270px;background:#182535;color:white;border-radius:6px;padding:8px;pointer-events:none;display:none;font-size:14px}@media(max-width:850px){.layout{grid-template-columns:1fr}svg{height:420px}}
</style><main><h1>แผนที่ปริมาณรถ: ทางแยกที่ตรวจพิกัดได้</h1><p>21 ทางแยก / 42 คู่ทางแยก–ถนน ช่วง 07:00–09:00 — เป็นบางส่วนของชุดหลัก ไม่ใช่ผลทั่วกรุงเทพฯ<br>สีแสดงดัชนีเทียบ Before=100; คลิกหรือใช้ Tab เลือกจุดเพื่อดูถนนที่นำมาคำนวณ</p><label>ช่วงเปรียบเทียบ <select id="period"><option>During</option><option selected>After</option></select></label><label>มุมมอง <select id="extent"><option value="sample">ขยายบริเวณจุดสำรวจ</option><option value="city">ขอบเขตกรุงเทพฯ</option></select></label><div class="legend"><span class="sw" style="background:#2166ac"></span>ต่ำกว่าฐาน <span class="sw" style="background:#eee"></span>ใกล้ฐาน <span class="sw" style="background:#b2182b"></span>สูงกว่าฐาน <span id="range"></span></div><div class="layout"><div class="panel"><svg id="map" role="group" aria-label="แผนที่ทางแยก"></svg></div><aside class="panel" id="detail" aria-live="polite">เลือกจุดบนแผนที่เพื่อดูรายละเอียด</aside></div><p class="note">หนึ่งจุดเป็นมัธยฐานดัชนีของคู่ถนนที่ผ่านการตรวจในแยกนั้น จึงต้องอ่านค่ารายถนนประกอบ ไม่มีจุดไม่ได้แปลว่ารถเป็นศูนย์ พิกัดเป็นตำแหน่งอ้างอิงปัจจุบัน ไม่ใช่ GPS วันสำรวจ และข้อมูลยังเป็นฉบับร่าง</p><p class="note">พิกัด: <a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors — ODbL</a> · ขอบเขต: <a href="https://www.geoboundaries.org/api/current/gbOpen/THA/ADM1/">geoBoundaries gbOpen THA ADM1</a> · <a href="map_road_period_indices.csv">ตารางข้อมูลรายถนน CSV</a><br>แผนที่นี้เปิดแบบออฟไลน์ได้ ไม่มีการโหลดแผนที่หรือพิกัดจากเครือข่ายขณะใช้งาน</p></main><div id="tooltip"></div><script>
const data=__PAYLOAD__,svg=document.getElementById('map'),ns='http://www.w3.org/2000/svg',cos=Math.cos(13.75*Math.PI/180),project=([x,y])=>[x*cos,-y];let selected=null;
const geom=data.geo.features[0].geometry,polys=geom.type==='MultiPolygon'?geom.coordinates:[geom.coordinates],all=polys.flat(2).map(project),ps=data.points.map(p=>project([p.longitude,p.latitude]));
function bounds(arr){const xs=arr.map(p=>p[0]),ys=arr.map(p=>p[1]),pad=.012;return [Math.min(...xs)-pad,Math.min(...ys)-pad,Math.max(...xs)-Math.min(...xs)+2*pad,Math.max(...ys)-Math.min(...ys)+2*pad]}
const bound={city:bounds(all),sample:bounds(ps)},limit=Math.max(40,...data.points.flatMap(p=>[Math.abs(p.During-100),Math.abs(p.After-100)]));document.getElementById('range').textContent='(สเกลร่วม ±'+limit.toFixed(1)+' จุดดัชนี)';
function color(v){const f=Math.min(1,Math.abs(v)/limit),end=v>=0?[178,24,43]:[33,102,172];return 'rgb('+end.map(x=>Math.round(245+(x-245)*f)).join(',')+')'}
function el(n,attrs){let e=document.createElementNS(ns,n);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));svg.appendChild(e);return e}
function detail(p){selected=p;const box=document.getElementById('detail');box.replaceChildren();const h=document.createElement('h2');h.textContent=p.intersection_key;box.append(h);const para=document.createElement('p');para.textContent='รหัส '+p.map_code+' · '+p.road_units+' คู่ถนน · มัธยฐานดัชนี During '+p.During.toFixed(1)+' / After '+p.After.toFixed(1);box.append(para);const table=document.createElement('table');let tr=document.createElement('tr');['ถนน','During','After'].forEach(t=>{let th=document.createElement('th');th.textContent=t;tr.append(th)});table.append(tr);data.roads.filter(r=>r.intersection_key===p.intersection_key).forEach(r=>{let tr=document.createElement('tr');[r.road_key,r.During.toFixed(1),r.After.toFixed(1)].forEach(t=>{let td=document.createElement('td');td.textContent=t;tr.append(td)});table.append(tr)});box.append(table);const a=document.createElement('a');a.href=data.roads.find(r=>r.intersection_key===p.intersection_key).osm_url;a.textContent='ตรวจจุดพิกัดใน OpenStreetMap';box.append(a)}
const tip=document.getElementById('tooltip');function show(p,e){const per=document.getElementById('period').value;tip.textContent=p.intersection_key+' | '+per+' '+p[per].toFixed(1)+' | '+p.road_units+' คู่ถนน';tip.style.display='block';const r=e.target.getBoundingClientRect();tip.style.left=Math.min(window.innerWidth-290,(e.clientX||r.x)+14)+'px';tip.style.top=Math.max(10,(e.clientY||r.y)-40)+'px'}
function draw(){svg.replaceChildren();const b=bound[document.getElementById('extent').value];svg.setAttribute('viewBox',b.join(' '));polys.forEach(poly=>el('path',{d:poly.map(r=>'M'+r.map(x=>project(x).join(',')).join('L')+'Z').join(' '),fill:'#fff','fill-rule':'evenodd',stroke:'#83919d','stroke-width':b[2]/1100}));data.points.forEach(p=>{const xy=project([p.longitude,p.latitude]),per=document.getElementById('period').value,e=el('circle',{cx:xy[0],cy:xy[1],r:b[2]/95,fill:color(p[per]-100),tabindex:0,role:'button','aria-label':p.intersection_key+' '+per+' '+p[per].toFixed(1)});e.addEventListener('mouseenter',ev=>show(p,ev));e.addEventListener('mouseleave',()=>tip.style.display='none');e.addEventListener('focus',ev=>{detail(p);show(p,ev)});e.addEventListener('blur',()=>tip.style.display='none');e.addEventListener('click',()=>detail(p));e.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();detail(p)}})});if(selected)detail(selected)}
document.getElementById('period').addEventListener('change',draw);document.getElementById('extent').addEventListener('change',draw);draw();detail(data.points[0]);
</script></html>'''
    (out/'bangkok_map_interactive.html').write_text(page.replace('__PAYLOAD__',payload),encoding='utf-8')

if __name__=='__main__':run_additional_visuals()
