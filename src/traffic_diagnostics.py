"""Supplementary diagnostics. Run from the project root; preserves supplied periods and source."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
ROOT=Path.cwd()
OUT=ROOT/'outputs/diagnostics'
OUT.mkdir(parents=True,exist_ok=True)
KEY=['intersection_key','road_key','time_key'];V=['passenger_car','pickup_van','large_bus','small_bus','truck','tuk_tuk'];P=['ก่อนโควิด','โควิด','หลังโควิด'];L=dict(zip(P,['Before','During','After']))
def save(x,n):x.to_csv(OUT/n,index=False,encoding='utf-8-sig')
def paired(x,keys=KEY):
 w=x.groupby(keys+['covid_period']).vehicles_per_hour.median().unstack('covid_period').reindex(columns=P).dropna()
 w=w[w[P[0]]>0];idx=w.div(w[P[0]],axis=0)*100;idx.columns=['Before','During','After'];return w,idx

def mix(x):
 x=x[x.vehicle_total.gt(0)].copy()
 for v in V:x[v]=x[v+'_clean']/x.vehicle_total*100
 u=x.groupby(KEY+['covid_period'])[V].mean().reset_index()
 k=u.groupby(KEY).covid_period.nunique();k=k[k.eq(3)].reset_index()[KEY]
 u=u.merge(k,on=KEY);return u.groupby('covid_period')[V].mean().reindex(P),k

def md(x):
    x=x.round(3).fillna('NA'); rows=[list(x.columns)]+x.astype(str).values.tolist()
    out=['| '+' | '.join(map(str,rows[0]))+' |','| '+' | '.join(['---']*len(x.columns))+' |']
    out.extend('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in rows[1:])
    return '\n'.join(out)
def main():
 d=pd.read_csv(ROOT/'data/processed/traffic_analysis_candidates.csv',low_memory=False)
 d['survey_date_parsed']=pd.to_datetime(d.survey_date_parsed)
 d['survey_weekday']=d.survey_date_parsed.dt.day_name();d['actual_month']=d.survey_date_parsed.dt.month
 w,idx=paired(d);keys=w.reset_index()[KEY];m=d.merge(keys,on=KEY,validate='many_to_one')
 # Intersection-cluster bootstrap retains every location-time unit and original equal-unit median estimand.
 groups=[g[['During','After']].to_numpy() for _,g in idx.reset_index().groupby('intersection_key')]
 rng=np.random.default_rng(5001);boot=np.empty((3000,2))
 for i in range(len(boot)):boot[i]=np.median(np.concatenate([groups[j] for j in rng.integers(0,len(groups),len(groups))]),axis=0)
 ci=pd.DataFrame({'period':['During','After'],'median_index':idx[['During','After']].median().values,'bootstrap_p025':np.quantile(boot,.025,axis=0),'bootstrap_p975':np.quantile(boot,.975,axis=0),'units':len(idx),'intersection_clusters':len(groups),'replicates':len(boot),'seed':5001});save(ci,'cluster_bootstrap.csv')
 # Complete-number sensitivity with common-unit controls.
 complete=d.loc[~d.has_assumed_zero].copy();wc,ic=paired(complete)
 rows=[]
 for name,z in [('main_zero_assumption',d),('main_restricted_to_complete_units',d.merge(wc.reset_index()[KEY],on=KEY)),('complete_numeric_only',complete)]:
  a,b=paired(z);rows.append({'design':name,'rows':len(z.merge(a.reset_index()[KEY],on=KEY)),'units':len(a),'During':b.During.median(),'After':b.After.median()})
 sensitivity=pd.DataFrame(rows);save(sensitivity,'zero_sensitivity.csv')
 mx,k=mix(m);c0=complete.merge(wc.reset_index()[KEY],on=KEY);mc,kc=mix(c0)
 # same mix units for a clearer sensitivity comparison
 original_common=m.merge(kc,on=KEY);mo,ko=mix(original_common)
 mixes=[]
 for name,a,ks in [('main',mx,k),('original_common_units',mo,ko),('complete_numeric_common_units',mc,kc)]:
  for v in V:mixes.append({'design':name,'vehicle':v,'Before_share':a.loc[P[0],v],'After_share':a.loc[P[2],v],'change_pp':a.loc[P[2],v]-a.loc[P[0],v],'units':len(ks)})
 save(pd.DataFrame(mixes),'zero_vehicle_mix_sensitivity.csv')
 # Survey weekday/month matching (not holiday adjustment).
 strict=[]
 for name,kk in [('same_weekday',KEY+['survey_weekday']),('same_survey_month_weekday',KEY+['actual_month','survey_weekday'])]:
  a,b=paired(d,kk);strict.append({'design':name,'units':len(a),'During':float(b.During.median()) if len(b) else None,'After':float(b.After.median()) if len(b) else None})
 save(pd.DataFrame(strict),'weekday_sensitivity.csv')
 # Separate report years; each matches the same actual survey month as its own Before comparison.
 years=[];year_units=[]
 for year in range(2022,2027):
  pre=d[d.covid_period.eq(P[0])].groupby(KEY+['actual_month']).vehicles_per_hour.median().rename('Before')
  post=d[d.covid_period.eq(P[2])&d.report_year.eq(year)].groupby(KEY+['actual_month']).vehicles_per_hour.median().rename('After_year')
  y=pd.concat([pre,post],axis=1).dropna();y=y[y.Before.gt(0)];y['paired_index']=y.After_year/y.Before*100
  q=y.reset_index();q['report_year']=year;year_units.append(q)
  years.append({'report_year':year,'units':len(y),'locations':len(q[['intersection_key','road_key']].drop_duplicates()),'median_index':y.paired_index.median(),'months':','.join(map(str,sorted(q.actual_month.unique()))),'interpretation':'different matched sample each year; no trend line'})
 yu=pd.concat(year_units,ignore_index=True);save(yu,'after_year_matched_units.csv');save(pd.DataFrame(years),'after_year_summary.csv')
 # All ten displayed locations, exact observed dates and low-assumption calendar windows.
 r=pd.read_csv(ROOT/'outputs/eda/morning_location_ranking_displayed.csv')
 case=d[d.time_key.eq('07:00-09:00')].merge(r[['intersection_key','road_key','location_code']],on=['intersection_key','road_key'])
 def flag(t):
  if (t.month==12 and t.day>=25) or (t.month==1 and t.day<=3):return 'near_new_year_window_not_official_holiday_flag'
  if t.month==4 and 10<=t.day<=17:return 'near_songkran_window_not_official_holiday_flag'
  if t.strftime('%m-%d')=='05-02':return 'day_after_May1_not_itself_confirmed_holiday'
  return 'no_selected_calendar_window; other_events_not_ruled_out'
 case['calendar_screen']=case.survey_date_parsed.map(flag)
 case['period_before_emergency']=case.covid_period.eq(P[1])&case.survey_date_parsed.lt('2020-03-26')
 cols=['location_code','intersection_key','road_key','covid_period','survey_date_parsed','survey_weekday','report_date','vehicles_per_hour','has_assumed_zero','calendar_screen','period_before_emergency','source_excel_row']
 case=case.sort_values(['location_code','survey_date_parsed']);save(case[cols],'case_survey_dates.csv')
 # Descriptive leave-one-visit-out ranges (not confidence intervals).
 loo=[];components=[]
 for code,g in case.groupby('location_code'):
  b=g[g.covid_period.eq(P[0])];a=g[g.covid_period.eq(P[2])];base=b.vehicles_per_hour.median();post=a.vehicles_per_hour.median();vals=[]
  for j in b.index:vals.append((post/b.drop(j).vehicles_per_hour.median()-1)*100)
  for j in a.index:vals.append((a.drop(j).vehicles_per_hour.median()/base-1)*100)
  counts=g.covid_period.value_counts();loo.append({'code':code,'intersection':g.intersection_key.iloc[0],'road':g.road_key.iloc[0],'Before_n':counts.get(P[0],0),'During_n':counts.get(P[1],0),'After_n':counts.get(P[2],0),'after_change_pct':(post/base-1)*100,'leave_one_visit_min_pct':min(vals),'leave_one_visit_max_pct':max(vals),'all_weekdays':bool((g.survey_date_parsed.dt.dayofweek<5).all())})
  for v in V:components.append({'code':code,'vehicle':v,'before_mean_vph':(b[v+'_clean']/b.period_hours).mean(),'after_mean_vph':(a[v+'_clean']/a.period_hours).mean(),'mean_vph_difference':(a[v+'_clean']/a.period_hours).mean()-(b[v+'_clean']/b.period_hours).mean()})
  cc=sum(x['mean_vph_difference'] for x in components if x['code']==code)
  assert np.isclose(cc,a.vehicles_per_hour.mean()-b.vehicles_per_hour.mean())
 save(pd.DataFrame(loo),'case_leave_one_visit_out.csv');save(pd.DataFrame(components),'case_vehicle_mean_decomposition.csv')
 # Sample receipt for each of the original ten figures.
 receipt=[{'figure':1,'sample':'623 same-time units; 70 same-report-quarter units'},{'figure':2,'sample':str(w.groupby(level='time_key').size().to_dict())},{'figure':3,'sample':f'{len(w)} units; {len(m)} rows'},{'figure':4,'sample':f'{len(k)} positive-total complete mix units'},{'figure':5,'sample':'17005 raw source rows; counts per report month'},{'figure':6,'sample':f'{len(idx)} positive-baseline units'},{'figure':7,'sample':'133 paired AM/PM locations'},{'figure':8,'sample':'10 displayed / 17 eligible locations; individual period n in case table'},{'figure':9,'sample':f'{len(k)} mix units'},{'figure':10,'sample':'6 report-month matched units; 12 observations'}];save(pd.DataFrame(receipt),'figure_sample_sizes.csv')
 result={'source_sha256':d.source_sha256.iloc[0],'matched_rows':len(m),'clusters':len(groups),'case_rows':len(case),'case_dates':case.survey_date_parsed.nunique(),'case_weekend_rows':int((case.survey_date_parsed.dt.dayofweek>=5).sum()),'during_before_2020_03_26_rows_in_main':int((m.covid_period.eq(P[1])&m.survey_date_parsed.lt('2020-03-26')).sum()),'bootstrap':ci.to_dict('records'),'zero_sensitivity':rows,'weekday_sensitivity':strict,'annual':years}
 (OUT/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 report='# ผลตรวจเพิ่มเติม: ความไม่แน่นอน ค่าว่าง วันสำรวจ และปีภายใน After\n\n'
 report+='สูตรหลักและ covid_period คงเดิม ผลนี้เป็นภาคผนวกของ EDA ไม่ใช่ causal effect\n\n## Bootstrap ตามกลุ่มทางแยก\n\n'+md(ci)+'\n\nสุ่มทางแยกพร้อมหน่วยถนน–เวลาภายใน 3,000 รอบ seed=5001; percentile 95% เป็นความไม่แน่นอนภายในตัวอย่าง ไม่รวม selection bias ความผิดการวัด หรือความต่างวันสำรวจ\n\n## สมมติฐานค่าว่าง=0\n\n'+md(sensitivity)+'\n\nแถว original restricted ใช้หน่วยชุดเดียวกับ complete numeric เพื่อแยกการเปลี่ยนสมาชิกบางส่วน แต่การลบวันสำรวจยังเปลี่ยนองค์ประกอบเวลา ไม่แทนวิธีหลักโดยอัตโนมัติ ดู zero_vehicle_mix_sensitivity.csv สำหรับผลสัดส่วนรถ\n\n## วันในสัปดาห์\n\n'+md(pd.DataFrame(strict))+'\n\nใช้วันสำรวจจริงและไม่ได้ปรับวันหยุด การเพิ่มเงื่อนไขทำให้ชุดตัวอย่างเปลี่ยน\n\n## แยกปี After\n\n'+md(pd.DataFrame(years))+'\n\nแต่ละปีจับคู่กับ Before บนสถานที่+เวลา+เดือนสำรวจเดียวกัน แต่คนละชุดระหว่างปี จึงไม่ลากเส้นแนวโน้ม\n\n## สถานที่แสดงในกราฟ 8\n\n'+md(pd.DataFrame(loo))+'\n\nช่วง leave-one-visit-out แสดงความไวเมื่อเอาวันสำรวจ Before หรือ After ออกทีละหนึ่งรายการ ไม่ใช่ confidence interval และไม่ใช่ข้อเสนอให้ลบข้อมูล\n\nทุกวันสำรวจของสิบสถานที่เป็นจันทร์–ศุกร์ แต่ไม่ได้หมายความว่าทุกวันเป็นวันทำงานปกติ ต้องตรวจวันหยุดและกิจกรรมแยก\n\n'
 for code,g in case.groupby('location_code'):
  report+='### '+code+' '+g.intersection_key.iloc[0]+' / '+g.road_key.iloc[0]+'\n\n'+md(g[['covid_period','survey_date_parsed','survey_weekday','vehicles_per_hour','calendar_screen','source_excel_row']].assign(survey_date_parsed=lambda z:z.survey_date_parsed.dt.strftime('%Y-%m-%d')))+'\n\n'
 report+='## จำนวนตัวอย่างกราฟเดิม\n\n'+md(pd.DataFrame(receipt))+'\n'
 (OUT/'Statistical_Diagnostics.md').write_text(report,encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
