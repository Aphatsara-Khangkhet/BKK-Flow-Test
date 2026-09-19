"""EDA for the supplied traffic_data snapshot. Groups always come from covid_period."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from traffic_audit import ROOT, VEHICLES, PERIODS, matching, save_csv
from write_audit_report import table

LABELS=dict(zip(PERIODS,['Before','During','After']))
COLORS={'Before':'#6b7280','During':'#bf6532','After':'#28649c'}
OUT=ROOT/'outputs/eda'

def paired(frame,keys):
    _,_,matched=matching(frame,keys)
    cells=matched.groupby(keys+['covid_period']).vehicles_per_hour.agg(['median','mean','size']).reset_index()
    wide=cells.pivot(index=keys,columns='covid_period',values='median').reindex(columns=PERIODS)
    assert wide.notna().all().all()
    wide.columns=['Before','During','After']
    good=wide.Before.gt(0)
    index=wide.div(wide.Before.where(good),axis=0)*100
    info={'rows':len(matched),'units':len(wide),'locations':len(matched[['intersection_key','road_key']].drop_duplicates()),'positive_baseline_units':int(good.sum()),'zero_baseline_units':int((~good).sum()),'row_counts':matched.covid_period.map(LABELS).value_counts().to_dict(),'index_medians':index.median().to_dict(),'index_means':index.mean().to_dict(),'vph_medians':wide.median().to_dict(),'after_at_or_above_before_pct':float((wide.loc[good,'After']>=wide.loc[good,'Before']).mean()*100) if good.any() else None,'report_year_counts':matched.report_year.value_counts().sort_index().to_dict()}
    return matched,cells,wide,index,info

def finish(fig,name,note,left=.10):
    fig.text(.02,.025,note,fontsize=9,color='#4b5563',va='bottom')
    fig.subplots_adjust(bottom=.22,top=.86,left=left,right=.97)
    fig.savefig(OUT/'figures'/name,dpi=160,facecolor='white')
    plt.close(fig)

EXTRA_FIGURES = {
    '05_report_coverage.png': 'Coverage ของข้อมูลตามปีและเดือนรายงาน',
    '06_recovery_distribution.png': 'การกระจายดัชนีปริมาณรถใน matched units',
    '07_paired_morning_evening.png': 'เช้าและเย็นบนสถานที่และวันสำรวจชุดเดียวกัน',
    '08_morning_location_ranking.png': 'ตัวอย่างสถานที่ช่วงเช้าที่ควรติดตาม',
    '09_vehicle_share_change.png': 'การเปลี่ยนสัดส่วนรถเป็น percentage points',
    '10_2026_matched_months.png': 'ปี 2026 เทียบ Before เฉพาะเดือนตรงกัน'
}

def extended_eda(d,main,wide,index,mix,meta):
    """Question-driven additions. No external example data or code used."""
    result={}
    # 5. Sampling coverage: missing source months are not zero traffic volume.
    audited=pd.read_csv(ROOT/'data/interim/traffic_audited.csv',low_memory=False)
    coverage=audited.groupby(['report_year','report_month']).size().unstack(fill_value=0).reindex(index=range(2017,2027),columns=range(1,13),fill_value=0).astype(float)
    coverage.loc[2017,[1,2]]=np.nan;coverage.loc[2026,list(range(6,13))]=np.nan
    fig,ax=plt.subplots(figsize=(11,6.5))
    ax.set_facecolor('#e5e7eb')
    sns.heatmap(coverage,annot=True,fmt='.0f',cmap='Blues',linewidths=.5,cbar_kws={'label':'Source observations (rows)'},ax=ax)
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],rotation=0)
    ax.set_yticklabels([str(y) for y in range(2017,2027)],rotation=0);ax.set_xlabel('Report month');ax.set_ylabel('Report year')
    ax.set_title('Figure 5. Sampling coverage by report month',pad=18)
    finish(fig,'05_report_coverage.png','Source: supplied workbook, traffic_data; all source rows before exclusions. Numbers count observations, not vehicles.\n0 = no rows in that report month; grey = outside agreed scope. A populated month does not mean a full traffic census.')
    save_csv(coverage.reset_index(),OUT/'report_month_coverage.csv')
    # 6. Full empirical distributions retain high-index observations.
    fig,ax=plt.subplots(figsize=(10.5,5.8))
    for label in ['During','After']:
        values=np.sort(index[label].dropna().to_numpy());n=len(values)
        ax.step(np.r_[0,values],np.r_[0,np.arange(1,n+1)/n*100],where='post',color=COLORS[label],label=f'{label} (n={n})',linewidth=2)
    ax.axvline(100,color='#6b7280',linestyle='--',linewidth=1)
    ax.set_ylim(0,102);ax.set_xlim(left=0);ax.set_xlabel('Paired index (Before = 100)');ax.set_ylabel('Cumulative share of matched units (%)')
    ax.set_title('Figure 6. Distribution of paired traffic-volume indices',pad=18);ax.legend(loc='lower right')
    finish(fig,'06_recovery_distribution.png','Source: supplied workbook, traffic_data. Each location + exact time has equal weight; all positive-baseline units.\nThe curve shows the share at or below an index; it is not a confidence interval. No high-index units removed.')
    result['after_at_or_above_100_pct']=float(index.After.ge(100).mean()*100)
    save_csv(index[['During','After']].quantile([0,.25,.5,.75,1]).reset_index(names='quantile'),OUT/'paired_index_quantiles.csv')
    # 7. Match morning and evening observations within the same survey day first.
    loc=['intersection_key','road_key'];times=['07:00-09:00','16:00-19:00']
    visits=main.loc[main.time_key.isin(times)&main.survey_date_parsed.notna()].copy()
    visitkey=loc+['survey_date_parsed','covid_period']
    complete_visits=visits.groupby(visitkey).time_key.nunique();complete_visits=complete_visits[complete_visits.eq(2)].reset_index()[visitkey]
    visits=visits.merge(complete_visits,on=visitkey,validate='many_to_one')
    paired_windows=visits.groupby(loc+['covid_period','time_key']).vehicles_per_hour.median().unstack(['covid_period','time_key'])
    required=pd.MultiIndex.from_product([PERIODS,times],names=['covid_period','time_key'])
    paired_windows=paired_windows.reindex(columns=required).dropna()
    positive=(paired_windows[(PERIODS[0],times[0])]>0)&(paired_windows[(PERIODS[0],times[1])]>0)
    paired_windows=paired_windows.loc[positive]
    ampm={}
    for window in times:
        base=paired_windows[(PERIODS[0],window)]
        ampm[window]=pd.DataFrame({LABELS[p]:paired_windows[(p,window)]/base*100 for p in PERIODS})
    n=len(paired_windows)
    med=pd.DataFrame({window:ampm[window].median() for window in times}).reindex(['Before','During','After'])
    diffs=pd.DataFrame({label:ampm[times[1]][label]-ampm[times[0]][label] for label in ['During','After']})
    save_csv(med.reset_index(names='period'),OUT/'paired_am_pm_median_indices.csv')
    save_csv(diffs.reset_index(),OUT/'paired_am_pm_location_differences.csv')
    fig,axes=plt.subplots(1,2,figsize=(12,6))
    positions=np.arange(3)
    for j,(window,color) in enumerate(zip(times,['#28649c','#bf6532'])):
        bars=axes[0].bar(positions+(j-.5)*.32,med[window],.32,color=color,label=window)
        axes[0].bar_label(bars,fmt='%.1f',padding=3,fontsize=9)
    axes[0].set_xticks(positions,['Before','During','After']);axes[0].set_ylabel('Median paired index (Before = 100)')
    axes[0].axhline(100,color='#6b7280',linestyle='--',linewidth=1);axes[0].legend(fontsize=9);axes[0].set_ylim(0,max(120,float(med.max().max())*1.3))
    axes[0].set_title(f'Same locations, paired survey days (n={n})',fontsize=11)
    axes[1].boxplot([diffs.During,diffs.After],tick_labels=['During','After'],showfliers=True,medianprops={'color':'#28649c','linewidth':2})
    axes[1].axhline(0,color='#6b7280',linestyle='--',linewidth=1);axes[1].set_ylabel('Evening index minus morning index (points)')
    axes[1].set_title('Within-location difference',fontsize=11)
    fig.suptitle('Figure 7. Morning versus evening on a shared sample',fontweight='bold')
    finish(fig,'07_paired_morning_evening.png','Source: supplied workbook, traffic_data. Both windows observed on the same survey day within each period.\nEach window has its own Before baseline; box = IQR, whiskers = 1.5 IQR, points = tails (not confidence intervals).')
    result['paired_am_pm']={'locations':n,'median_after_pm_minus_am_points':float(diffs.After.median()),'median_during_pm_minus_am_points':float(diffs.During.median()),'median_indices':med.to_dict()}
    # 8. Require repeated observations in every period, hold window fixed.
    morning=main[main.time_key.eq(times[0])]
    counts=morning.groupby(loc+['covid_period']).size().unstack(fill_value=0).reindex(columns=PERIODS,fill_value=0)
    eligible=counts[counts.ge(2).all(axis=1)].index
    ranks=wide.xs(times[0],level='time_key').loc[eligible].copy()
    ranks['after_change_pct']=(ranks.After/ranks.Before-1)*100
    ranks=ranks[ranks.Before>0].sort_index();ranks['location_code']=[f'L{i+1:02d}' for i in range(len(ranks))]
    ranks=ranks.join(counts.rename(columns={p:f'n_{LABELS[p]}' for p in PERIODS})).reset_index()
    ordered=ranks.sort_values('after_change_pct')
    selected=pd.concat([ordered.head(5),ordered.tail(5)]).drop_duplicates(loc).sort_values('after_change_pct')
    save_csv(ranks,OUT/'morning_location_ranking_all.csv');save_csv(selected,OUT/'morning_location_ranking_displayed.csv')
    fig,ax=plt.subplots(figsize=(10.5,6.2));values=selected.after_change_pct
    bars=ax.barh(selected.location_code,values,color=np.where(values.ge(0),'#28649c','#bf6532'))
    ax.bar_label(bars,labels=[f'{x:+.1f}%' for x in values],padding=4,fontsize=10)
    ax.axvline(0,color='#6b7280',linewidth=1);ax.margins(x=.25)
    ax.set_xlabel('After versus Before: change in median vehicles/hour (%)');ax.set_ylabel('Location code (names in adjacent table)')
    ax.set_title(f'Figure 8. Morning locations with repeated observations\nFive lowest and five highest among {len(ranks)} eligible locations',fontsize=12,pad=18)
    finish(fig,'08_morning_location_ranking.png','Source: supplied workbook, traffic_data. 07:00-09:00 only; at least 2 observations in each supplied COVID period.\nRanks are within this eligible sample, not all Bangkok. Review source counts and baseline before targeting a location.')
    result['ranking_eligible_locations']=len(ranks)
    # 9. Small categories become visible on a percentage-point scale.
    delta=(mix.loc[PERIODS[2]]-mix.loc[PERIODS[0]]).sort_values()
    names=dict(zip(VEHICLES,['Passenger car','Pickup / van','Large bus','Small bus','Truck','Tuk-tuk']))
    fig,ax=plt.subplots(figsize=(10.5,5.8));bars=ax.barh([names[v] for v in delta.index],delta,color=np.where(delta.ge(0),'#28649c','#bf6532'))
    ax.bar_label(bars,labels=[f'{v:+.2f} pp' for v in delta],padding=4,fontsize=10);ax.axvline(0,color='#6b7280',linewidth=1);ax.margins(x=.3)
    ax.set_xlabel('After share minus Before share (percentage points)');ax.set_title('Figure 9. Vehicle-share changes in matched units',pad=18)
    finish(fig,'09_vehicle_share_change.png','Source: supplied workbook, traffic_data; same equal-unit share estimator as Figure 4.\nPercentage-point change is not percentage growth. Missing / dash = 0 can affect the smaller vehicle categories.',left=.20)
    save_csv(pd.DataFrame({'vehicle_type':delta.index,'share_change_pp':delta.values}),OUT/'vehicle_share_change_pp.csv')
    result['share_change_pp']=delta.to_dict()
    # 10. Latest YTD compared only on exact matched report month and time.
    ytd=d[((d.covid_period.eq(PERIODS[2]))&d.report_year.eq(2026))|d.covid_period.eq(PERIODS[0])].copy()
    ytd=ytd[ytd.report_month.between(1,5)]
    ytd['comparison']=np.where(ytd.report_year.eq(2026),'2026 YTD','Before')
    ykey=loc+['time_key','report_month']
    ywide=ytd.groupby(ykey+['comparison']).vehicles_per_hour.median().unstack().reindex(columns=['Before','2026 YTD']).dropna()
    ywide['paired_index']=ywide['2026 YTD']/ywide.Before.where(ywide.Before>0)*100
    yt=ywide.reset_index();yt['unit_code']=[f'Y{i+1:02d}' for i in range(len(yt))]
    save_csv(yt,OUT/'year2026_matched_month_units.csv')
    selected_rows=ytd.merge(yt[ykey],on=ykey,validate='many_to_one');save_csv(selected_rows[['source_excel_row','intersection_key','road_key','time_key','report_month','report_year','comparison','vehicles_per_hour']],OUT/'year2026_matched_month_rows.csv')
    fig,ax=plt.subplots(figsize=(10.5,5.8));positions=np.arange(len(yt))
    for i,row in yt.iterrows():ax.plot([row['Before'],row['2026 YTD']],[i,i],color='#c3c7cd',linewidth=2,zorder=1)
    ax.scatter(yt.Before,positions,color=COLORS['Before'],s=45,label='Before same month',zorder=2)
    ax.scatter(yt['2026 YTD'],positions,color=COLORS['After'],s=45,label='2026 YTD',zorder=2)
    ax.set_yticks(positions,[f"{r.unit_code} | month {int(r.report_month)} | {r.time_key}" for r in yt.itertuples()])
    ax.set_xlim(left=0);ax.set_xlabel('Median vehicles per hour');ax.set_title(f'Figure 10. 2026 YTD on matched report months\nExploratory only: {len(yt)} matched units',pad=18,fontsize=12);ax.legend(loc='best',fontsize=9)
    finish(fig,'10_2026_matched_months.png','Source: supplied workbook, traffic_data. Match location + exact time + report month (January-May only).\nBefore uses supplied Before labels; 2026 is a subset of supplied After. Small sample; no citywide recovery claim.',left=.34)
    result['year2026']={'units':len(yt),'rows':len(selected_rows),'median_paired_index':float(ywide.paired_index.median()),'locations':len(yt[loc].drop_duplicates())}
    notes=f'''\n\n## กราฟที่เพิ่มหลังทบทวนเกณฑ์ Mini Project และงานรุ่นพี่

กราฟเพิ่มเติมมีคำถามกำกับ ไม่ได้กำหนดจำนวนรูปตามงานรุ่นพี่ อ้างอิงแนวการเล่าเรื่อง: https://github.com/techasit239/Dads-5001-Accident-Is-You-Dont-Love ; รายละเอียดเกณฑ์ที่มีและแผน Pitch อยู่ใน docs/rubric_and_senior_review.md

### Figure 5 — Coverage
![Figure 5](figures/05_report_coverage.png)
Evidence: report_month_coverage.csv นับแถวข้อมูลทั้งหมดต่อปี/เดือนรายงาน ไม่ใช่จำนวนรถ Interpretation: ชี้ช่องว่างและขอบเขตเวลาที่ใช้จริง Limitation: มีแถวไม่ได้แปลว่าทุกสถานที่มีครบเดือน Action: ใช้ต้นเรื่องอธิบายเหตุผลที่ต้อง matching แทนเทียบยอดดิบรายปี

### Figure 6 — ผลกระจายทั่วหน่วยหรือไม่
![Figure 6](figures/06_recovery_distribution.png)
Evidence: หน่วยที่ After ไม่น้อยกว่าฐานมี {result['after_at_or_above_100_pct']:.1f}% ของ matched units Interpretation: ผลภาพรวมไม่เหมือนกันทุกสถานที่/เวลา Limitation: แต่ละหน่วยไม่อิสระจากกันเมื่ออยู่ทางแยกเดียวกัน Action: เลือกตรวจรายสถานที่ ไม่ใช้ค่า median เมืองตัดสินทุกแห่ง

### Figure 7 — เช้า/เย็นบนฐานเดียวกัน
![Figure 7](figures/07_paired_morning_evening.png)
Evidence: จับคู่เช้าและเย็นวันสำรวจเดียวกันและมีครบทุก COVID period ได้ {n} คู่สถานที่ ค่ามัธยฐานความต่างดัชนีเย็นลบเช้าช่วง After เท่ากับ {diffs.After.median():+.2f} จุดดัชนี Interpretation: เป็นการเปรียบเทียบ within-location ที่ตอบ H3 ได้ตรงกว่ารูป 2 Limitation: ไม่ควบคุมเดือน/ปีสำรวจข้าม COVID periods และไม่ได้ทดสอบ causal effect Action: ถ้าจะประเมินการเดินทางเช้าหรือเย็น ให้เก็บวัน/เดือน/สถานที่เดิมซ้ำ

### Figure 8 — สถานที่สำหรับติดตาม
![Figure 8](figures/08_morning_location_ranking.png)
{table(selected[['location_code','intersection_key','road_key','Before','After','after_change_pct','n_Before','n_During','n_After']].round(2))}
Evidence: {len(ranks)} คู่สถานที่ผ่านเกณฑ์เวลา 07:00–09:00 และอย่างน้อย 2 observations ในทุกกลุ่ม แสดง 5 ค่าต่ำสุดและ 5 ค่าสูงสุด Limitation: อันดับเป็นของ eligible sample เท่านั้น และข้อมูลซ้ำเพียง 2 ครั้งยังมีความไม่แน่นอนสูง Action: ทวนชื่อและต้นทางของสถานที่ในตารางก่อนเลือกตัวอย่างเล่าเรื่อง ไม่ใช้สั่งเปลี่ยนสัญญาณไฟจากดัชนีนี้อย่างเดียว

### Figure 9 — สัดส่วนรถชนิดที่พบน้อย
![Figure 9](figures/09_vehicle_share_change.png)
Evidence: vehicle_share_change_pp.csv แสดง After ลบ Before เป็น percentage points Interpretation: ทำให้ความเปลี่ยนของหมวดเล็กที่ stacked bar ซ่อนไว้เห็นชัด Limitation: เป็นสัดส่วนใน sample และสมมติฐานช่องว่าง=0 อาจมีผล Action: ตรวจนิยามรถเมล์/ประเภทรถก่อนตีความการเปลี่ยนพฤติกรรมการเดินทาง

### Figure 10 — ปีล่าสุดบนเดือนตรงกัน
![Figure 10](figures/10_2026_matched_months.png)
{table(yt.round(2))}
Evidence: ปี 2026 จับคู่ Before บนสถานที่+เดือนรายงาน+เวลาเดียวกันได้ {len(yt)} หน่วย {len(selected_rows)} แถว ค่ามัธยฐานดัชนี {ywide.paired_index.median():.1f} Interpretation: แสดงขอบเขตหลักฐานที่มีจริงสำหรับ Present Limitation: ขนาดเล็กและไม่ใช่ panel ทั้งเมือง Action: เก็บข้อมูลเพิ่มในสถานที่และเดือนเดิมก่อนใช้ปี 2026 เป็นข้อสรุปหลัก
'''
    p=OUT/'EDA_Findings.md';p.write_text(p.read_text(encoding='utf-8')+notes,encoding='utf-8')
    (OUT/'extended_findings.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def run_eda():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
    meta=json.loads((ROOT/'outputs/current_audit/summary.json').read_text(encoding='utf-8'))
    d=pd.read_csv(ROOT/'data/processed/traffic_candidates.csv',low_memory=False)
    assert set(d.source_sha256)=={meta['source_sha256']}
    d['vehicle_total']=d[[c+'_clean' for c in VEHICLES]].sum(axis=1,min_count=6)
    d['vehicles_per_hour']=d.vehicle_total/d.period_hours
    assert d.period_hours.gt(0).all() and d.vehicles_per_hour.notna().all()
    assert np.isfinite(d.vehicles_per_hour).all()
    save_csv(d,ROOT/'data/processed/traffic_analysis_candidates.csv')
    key=['intersection_key','road_key','time_key']
    designs={'same_location_time':key,'same_report_quarter':key+['report_quarter'],'same_report_month':key+['report_month'],'same_survey_month':key+['survey_month']}
    samples={};summaries={}
    for name,keys in designs.items():
        sample,cells,wide,index,info=paired(d,keys)
        samples[name]=(sample,cells,wide,index);summaries[name]=info
        save_csv(cells,OUT/f'{name}_unit_statistics.csv')
        save_csv(wide.reset_index(),OUT/f'{name}_paired_vph.csv')
        save_csv(index.reset_index(),OUT/f'{name}_paired_indices.csv')
    main,cells,wide,index=samples['same_location_time']
    save_csv(main,ROOT/'data/processed/traffic_matched_analysis.csv')
    describe=main.groupby('covid_period').vehicles_per_hour.describe().reindex(PERIODS)
    save_csv(describe.reset_index(),OUT/'row_level_descriptive_statistics.csv')
    # Flag distribution tails, but do not discard high traffic counts.
    outliers=[]
    for label,g in main.groupby('covid_period'):
        q1,q3=g.vehicles_per_hour.quantile([.25,.75]);iqr=q3-q1
        mask=(g.vehicles_per_hour<q1-1.5*iqr)|(g.vehicles_per_hour>q3+1.5*iqr)
        outliers.append({'covid_period':label,'rows':len(g),'iqr_flagged_rows':int(mask.sum())})
    save_csv(pd.DataFrame(outliers),OUT/'outlier_review_counts.csv')
    # Type composition: observation shares -> mean within matched unit -> mean across units.
    mixrows=main.loc[main.vehicle_total.gt(0)].copy()
    shares=mixrows[[c+'_clean' for c in VEHICLES]].div(mixrows.vehicle_total,axis=0)
    shares.columns=VEHICLES
    sh=pd.concat([mixrows[key+['covid_period']].reset_index(drop=True),shares.reset_index(drop=True)],axis=1)
    unitshares=sh.groupby(key+['covid_period'])[VEHICLES].mean().reset_index()
    complete_mix=unitshares.groupby(key).covid_period.nunique();valid_mix=complete_mix[complete_mix.eq(3)].reset_index()[key]
    unitshares=unitshares.merge(valid_mix,on=key,validate='many_to_one')
    mix=unitshares.groupby('covid_period')[VEHICLES].mean().reindex(PERIODS)*100
    assert np.allclose(mix.sum(axis=1),100)
    save_csv(mix.reset_index(),OUT/'vehicle_mix_equal_unit_percent.csv')
    save_csv(main.groupby(['report_year','covid_period']).size().reset_index(name='rows'),OUT/'matched_year_coverage.csv')
    # Newest year is described by coverage only; no full-year totals versus YTD.
    ytd=main[main.report_year.eq(2026)]
    # Number of units represented in every report year (not assumed to exist).
    yearly=main.groupby(key).report_year.nunique()
    summaries['coverage']={'balanced_all_10_report_year_units':int(yearly.eq(10).sum()),'year_2026_rows':len(ytd),'year_2026_locations':len(ytd[['intersection_key','road_key']].drop_duplicates()),'main_assumed_zero_rows':int(main.has_assumed_zero.sum()),'mix_units':len(valid_mix),'all_zero_rows_excluded_from_mix':int(main.vehicle_total.eq(0).sum())}
    sns.set_theme(style='whitegrid',font='DejaVu Sans',font_scale=1.02)
    plt.rcParams.update({'axes.spines.top':False,'axes.spines.right':False,'grid.alpha':.25,'axes.titleweight':'bold','figure.facecolor':'white'})
    # Figure 1: sensitivity to matching choices; each matched unit has equal weight.
    fig,ax=plt.subplots(figsize=(10.5,5.6))
    names=['same_location_time','same_report_quarter'];x=np.arange(2);width=.23
    for j,label in enumerate(['Before','During','After']):
        values=[summaries[n]['index_medians'][label] for n in names]
        bars=ax.bar(x+(j-1)*width,values,width,label=label,color=COLORS[label])
        ax.bar_label(bars,fmt='%.1f',padding=4,fontsize=10)
    ax.set_xticks(x,[f"Same location + time\nn={summaries[names[0]]['positive_baseline_units']} units",f"Also same report quarter\nn={summaries[names[1]]['positive_baseline_units']} units"])
    ax.axhline(100,color='#4b5563',linestyle='--',linewidth=1)
    ax.set_ylabel('Median paired index (Before = 100)');ax.set_ylim(0,max(ax.get_ylim()[1],115)*1.12)
    ax.set_title('Figure 1. Traffic volume indices by matching design',pad=22);ax.legend(ncol=3,loc='upper left')
    finish(fig,'01_matching_sensitivity.png','Source: supplied workbook, traffic_data. Equal weight per matched unit; within-unit median vehicles/hour.\nMissing / dash vehicle values = 0. Report quarter is not necessarily survey season. After is pooled, not 2026 alone.')
    # Figure 2: median within unit, then across units for each exact observation window.
    abs_table=wide.groupby(level='time_key').median()
    counts=wide.groupby(level='time_key').size()
    save_csv(abs_table.reset_index(),OUT/'time_window_median_vph.csv')
    fig,ax=plt.subplots(figsize=(11,5.8));x=np.arange(len(abs_table));width=.24
    for j,label in enumerate(['Before','During','After']):
        bars=ax.bar(x+(j-1)*width,abs_table[label],width,color=COLORS[label],label=label)
        ax.bar_label(bars,fmt='%.0f',padding=3,fontsize=9)
    ax.set_xticks(x,[f'{t}\nn={counts[t]} units' for t in abs_table.index]);ax.set_ylabel('Median vehicles per hour');ax.set_xlabel('Exact survey time window')
    ax.set_ylim(0,ax.get_ylim()[1]*1.18);ax.set_title('Figure 2. Traffic volume by survey time window',pad=22);ax.legend(ncol=3,loc='upper left')
    finish(fig,'02_time_window_vph.png','Source: supplied workbook, traffic_data. Median per unit-period, then median across units; equal unit weights.\nSame locations within each time window across all 3 periods. Month, year and weekday composition can differ.')
    # Figure 3: paired locations, not independent samples from changing station sets.
    fig,axes=plt.subplots(1,2,figsize=(11,5.7),sharex=True,sharey=True)
    maximum=float(wide[['Before','During','After']].max().max())*1.05
    for ax,label in zip(axes,['During','After']):
        ax.scatter(wide.Before,wide[label],s=23,alpha=.55,color=COLORS[label],edgecolors='none')
        ax.plot([0,maximum],[0,maximum],color='#6b7280',linestyle='--',linewidth=1)
        ax.set_xlim(0,maximum);ax.set_ylim(0,maximum);ax.set_title(label);ax.set_xlabel('Before: median vehicles/hour')
    axes[0].set_ylabel('Comparison: median vehicles/hour');fig.suptitle('Figure 3. Paired traffic volumes at the same location and time',fontweight='bold')
    finish(fig,'03_paired_scatter.png',f'Source: supplied workbook, traffic_data. One point = one matched location + time unit (n={len(wide)}).\nDashed line: equal volume. Shared linear axes; high-volume points retained. No causal interpretation.')
    # Figure 4: whole composition at equal unit weight, not fleet/population estimates.
    fig,ax=plt.subplots(figsize=(10.5,5.8));bottom=np.zeros(3)
    palette=['#28649c','#d49842','#6b7280','#b85b78','#6f8051','#9b79b4']
    typenames=['Passenger car','Pickup / van','Large bus','Small bus','Truck','Tuk-tuk']
    for col,color,label in zip(VEHICLES,palette,typenames):
        values=mix[col].to_numpy();ax.bar(['Before','During','After'],values,bottom=bottom,color=color,label=label,width=.55)
        for j,value in enumerate(values):
            if value>=6:ax.text(j,bottom[j]+value/2,f'{value:.1f}%',ha='center',va='center',color='white',fontsize=10)
        bottom+=values
    ax.set_ylim(0,100);ax.set_ylabel('Mean vehicle share (%)');ax.set_title('Figure 4. Vehicle mix in matched units',pad=32)
    ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,1.12),fontsize=9,frameon=False)
    finish(fig,'04_vehicle_mix.png',f'Source: supplied workbook, traffic_data. Observation shares averaged within unit, then equally across {len(valid_mix)} units.\nOnly units with positive-total observations in all periods. Missing / dash = 0; not a citywide fleet estimate.')
    evidence={'source':meta,'results':summaries}
    (OUT/'eda_summary.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    broad=summaries['same_location_time'];quarter=summaries['same_report_quarter']
    comparison=pd.DataFrame([{'design':name,'rows':v['rows'],'units':v['units'],'Before':v['index_medians']['Before'],'During':v['index_medians']['During'],'After':v['index_medians']['After']} for name,v in summaries.items() if name!='coverage'])
    save_csv(comparison,OUT/'sensitivity_summary.csv')
    period_notes='; '.join(f"{name}: {count:,}" for name,count in broad['row_counts'].items())
    report=f'''# Bangkok Traffic — EDA ฉบับร่าง

ใช้ไฟล์ {meta['source_filename']} ชีต traffic_data จำนวน {meta['rows']:,} แถว ขอบเขตมีนาคม 2017–พฤษภาคม 2026

## ผลหลัก

ชุดสถานที่และเวลาเดียวกันมี {broad['rows']:,} แถว จาก {broad['locations']} คู่ทางแยก–ถนน และ {broad['units']} หน่วย location+time ({period_notes}) ค่ามัธยฐานดัชนีปริมาณรถต่อชั่วโมงเทียบกับ Before=100 เป็น **During {broad['index_medians']['During']:.1f} และ After {broad['index_medians']['After']:.1f}**

เมื่อเพิ่มเงื่อนไขไตรมาสรายงานเดียวกัน เหลือ {quarter['rows']} แถว {quarter['units']} หน่วย ดัชนีเป็น **During {quarter['index_medians']['During']:.1f} และ After {quarter['index_medians']['After']:.1f}** จึงต้องประเมินความไวต่อการเลือกชุดตัวอย่างก่อนสรุปการฟื้นตัว

## วิธีคำนวณและข้อกำหนด

- กลุ่มใช้ covid_period จากไฟล์โดยตรง ไม่คำนวณใหม่จากวันสำรวจหรือวันรายงาน
- Date/month/year คือวันที่รายงาน เก็บแยกจาก survey_date ความต่างกันไม่เป็นเหตุให้ตัดแถว
- ช่องว่างและ - ของจำนวนรถ 6 ประเภทเป็น 0 ตามผู้ใช้; เก็บค่าเดิมและ log จำนวน {meta['zero_assumed_cells']:,} เซลล์
- ปริมาณรถต่อชั่วโมง = ผลบวกรถ 6 ประเภท / ชั่วโมงตาม time_period จริง ไม่เทียบยอดช่วง 2 ชั่วโมงกับ 7–8 ชั่วโมงตรง ๆ
- ภายในแต่ละหน่วย location+exact-time และ covid_period ใช้ median vehicles/hour จากการสำรวจที่มี แล้วหารด้วย median ของ Before ของหน่วยเดียวกัน ดัชนีภาพรวมคือ median ของดัชนีหน่วย โดยทุกหน่วยมีน้ำหนักเท่ากัน
- หน่วยที่ Before=0 ไม่คำนวณอัตราส่วน (ชุดหลัก {broad['zero_baseline_units']} หน่วย) ไม่มีการเติมเดือนหรือสถานที่ที่ขาดเป็นศูนย์
- เก็บค่าปริมาณสูงไว้ ไม่ลบเพียงเพราะเป็น outlier ไม่ทดสอบ causal effect และแถวหลายช่วงเวลาของสถานที่เดียวกันไม่ใช่ตัวอย่างอิสระ
- กันคีย์สำรวจซ้ำและจำนวนรถทศนิยมออกจาก candidate ชั่วคราว ดูรายการ audit ไม่ถือว่าตัดสินความผิดของต้นทางแล้ว

## ผลและหลักฐาน

![Figure 1](figures/01_matching_sensitivity.png)

**Evidence:** ดัชนีจากแต่ละ matched unit ใน same_location_time_paired_indices.csv และ sensitivity_summary.csv

**Interpretation:** ผลที่เห็นเป็นการเปลี่ยนของปริมาณรถในตัวอย่างที่จับคู่ได้ การเปลี่ยนวิธีควบคุมเวลาอาจเปลี่ยนขนาดผล

**Limitation:** เดือน/ปี/วันในสัปดาห์ที่สำรวจไม่สมดุล ไตรมาสรายงานไม่จำเป็นต้องเป็นฤดูกาลสำรวจเดียวกัน และกลุ่ม After รวมหลายปี

**Implication:** ใช้หลาย matching designs ประกอบกันก่อนเลือกประเด็นนำเสนอ ไม่เลือกเฉพาะชุดที่ให้ผลตรงสมมติฐาน

{table(comparison.round(2))}

![Figure 2](figures/02_time_window_vph.png)

**Evidence:** time_window_median_vph.csv เปรียบเทียบสถานที่เดียวกันภายในเวลาเริ่ม–สิ้นสุดเดียวกัน

**Interpretation:** ใช้ดูว่าปริมาณต่อชั่วโมงต่างกันตามช่วงเวลาหรือไม่โดยคงหน่วยให้เทียบได้

**Limitation:** ชุดสถานที่ระหว่างเวลาเช้ากับเย็นอาจไม่เท่ากัน จึงยังไม่ใช่ผล paired morning-versus-evening และช่วง 09:00–17:00/17:00–19:00 อาจไม่ครบทั้งสามกลุ่ม

**Implication:** หากจะสรุปว่าเช้าฟื้นตัวดีกว่าเย็น ต้องทำ intersection ของชุดสถานที่ทั้งสองเวลาก่อน

![Figure 3](figures/03_paired_scatter.png)

**Evidence:** {broad['after_at_or_above_before_pct']:.1f}% ของหน่วยที่มี Before>0 มี After ไม่น้อยกว่า Before ในชุดกว้าง

**Interpretation:** ไม่ควรแทนทุกสถานที่ด้วยค่าเฉลี่ยเมืองเพียงค่าเดียว

**Limitation:** แต่ละจุดเป็น location+time และอาจมีทางแยกเดียวกันหลายถนน/เวลา ชื่อจับคู่ด้วย Unicode/whitespace ยังไม่ได้ยืนยันพิกัด

**Implication:** เลือกตัวอย่างสถานที่สำหรับนำเสนอหลังทวนชื่อและการตรวจนับต้นทาง

![Figure 4](figures/04_vehicle_mix.png)

**Evidence:** vehicle_mix_equal_unit_percent.csv เฉลี่ยสัดส่วนภายในหน่วยก่อนให้น้ำหนักหน่วยเท่ากัน

**Interpretation:** แสดงองค์ประกอบรถที่รายงานใน matched sample

**Limitation:** การแทนช่องว่าง/- เป็น 0 มีผลต่อสัดส่วน โดยเฉพาะรถที่พบน้อย ไม่ใช่สัดส่วนรถทั้งหมดในกรุงเทพฯ

**Implication:** ระบุสมมติฐาน 0 ใต้กราฟและตรวจชนิดรถก่อนใช้เสนอเชิงนโยบาย

## ปีล่าสุดและความครบถ้วน

ชุดหลักมีปีรายงาน 2026 จำนวน {len(ytd)} แถว จาก {summaries['coverage']['year_2026_locations']} คู่สถานที่ และมีหน่วยที่ครอบคลุมครบทุกปีรายงานทั้ง 10 ปีจำนวน {summaries['coverage']['balanced_all_10_report_year_units']} หน่วย จึงไม่ทำเส้นแนวโน้มรายปีจากคนละชุดตัวอย่าง และไม่เทียบยอดบางปี 2026 กับยอดเต็มปี

## สรุปขอบเขตข้อกล่าวอ้าง

ผลนี้ตอบเชิงพรรณนาว่าปริมาณรถใน matched sample ต่างกันอย่างไรระหว่าง label COVID ที่ผู้ใช้ให้มา ยังยืนยันไม่ได้ว่า COVID เป็นสาเหตุ หรือปริมาณรถทั้งกรุงเทพฯ กลับสู่ระดับเดิม และไม่ใช้ปริมาณรถสรุปความเร็ว เวลาเดินทาง หรือความติดขัด

## ตรวจย้อนและรันใหม่

Notebook: notebooks/02_eda_and_visualization.ipynb; โค้ด: src/traffic_eda.py; รูปและตารางอยู่ใน outputs/eda; ข้อมูลพร้อม metrics ใน data/processed/traffic_matched_analysis.csv

SHA-256: `{meta['source_sha256']}`

AI ช่วยจัดข้อมูล เขียนโค้ด สร้างกราฟและร่างคำอธิบาย สมาชิกยังต้องตรวจตัวเลขและชื่อกับหลักฐานต้นทางและเลือกขอบเขตข้อสรุป ไฟล์นี้ยังเป็น NotFinal
'''
    (OUT/'EDA_Findings.md').write_text(report,encoding='utf-8')
    evidence["extended"] = extended_eda(d,main,wide,index,mix,meta)
    (OUT/"eda_summary.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    return evidence

if __name__=='__main__':
    result=run_eda();print(json.dumps(result['results'],ensure_ascii=False,indent=2))
