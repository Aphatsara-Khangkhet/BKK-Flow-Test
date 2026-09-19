from pathlib import Path
import pandas as pd,numpy as np,json
r=Path('outputs/traffic_patterns');d=pd.read_csv('data/processed/traffic_analysis_candidates.csv',low_memory=False);d=d[d.report_year.between(2023,2025)&d.survey_year.between(2023,2025)]
p=pd.read_csv(r/'daily_profile_all.csv');v=pd.read_csv(r/'complete_day_observations.csv');m=pd.read_csv(r/'vehicle_mix_all.csv');c=pd.read_csv(r/'road_concentration.csv');sh=pd.read_csv(r/'road_day_shares.csv');s=pd.read_csv(r/'sampling_priority.csv')
assert len(p)==len(v)==26 and p.visits.eq(1).all()
j=v.merge(p,on=['intersection_key','road_key']);assert np.allclose(j['07:00-09:00_x']/j['09:00-16:00_x'],j['07:00-09:00_y'])
assert np.allclose(m.filter(like='_share').sum(axis=1),100) and m.visits.ge(2).all()
assert np.allclose(sh.groupby(['intersection','survey_date']).share_pct.sum(),100)
calc=sh.groupby(['intersection','survey_date']).share_pct.max().groupby('intersection').median();assert np.allclose(c.set_index('intersection').median_largest_road_share.sort_index(),calc.sort_index())
for row in s.itertuples():
 a=d[(d.intersection_key==row.intersection_key)&(d.road_key==row.road_key)&(d.time_key=='07:00-09:00')].vehicles_per_hour
 assert np.isclose((a.quantile(.75)-a.quantile(.25))/a.median(),row.relative_iqr)
assert s.days.eq(3).all()
(r/'validation.json').write_text(json.dumps({'within_day_ratios_verified':True,'vehicle_shares_sum_100':True,'road_shares_and_medians_verified':True,'dispersion_recomputed_from_candidates':True,'profile_locations':len(p),'mix_locations':len(m),'intersections':len(c),'sampling_locations':len(s)},indent=2),encoding='utf-8')
print('New metrics independently checked')
