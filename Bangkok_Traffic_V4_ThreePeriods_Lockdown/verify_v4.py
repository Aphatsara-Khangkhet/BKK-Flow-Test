from pathlib import Path
import json,hashlib,base64,nbformat
import pandas as pd,numpy as np
p=Path(__file__).resolve().parent
runs=sorted((p/'runs').glob('*/manifest.json'));r=runs[-1].parent
m=json.loads((r/'manifest.json').read_text(encoding='utf-8'))
d=pd.read_csv(r/'data/processed/traffic_candidates.csv',low_memory=False);d=d[d.survey_date_parsed.notna()&d.survey_year.ge(2017)];vehicles=['passenger_car','pickup_van','large_bus','small_bus','truck','tuk_tuk'];d['vph']=d[[v+'_clean' for v in vehicles]].sum(axis=1)/d.period_hours
keys=['intersection_key','road_key','time_key'];periods=['ก่อนโควิด','โควิด','หลังโควิด'];wide=d.groupby(keys+['covid_period']).vph.median().unstack().reindex(columns=periods).dropna();idx=wide.div(wide[periods[0]].where(wide[periods[0]]>0),axis=0)*100;got=pd.read_csv(r/'tables/overview.csv');assert np.allclose(idx.median().values,got.median_index)
lock=pd.read_csv(r/'tables/lockdown_matched_rows.csv');w=lock.groupby(keys+['Lockdown']).vph.median().unstack().dropna();index=(w.loc[w[0]>0,1]/w.loc[w[0]>0,0]*100).median();ls=pd.read_csv(r/'tables/lockdown_summary.csv');assert np.isclose(index,ls.iloc[0].median_index);assert len(w)==ls.iloc[0].units
mix=pd.read_csv(r/'tables/mix_change.csv');assert np.allclose(mix[periods].sum(),100)
levels=pd.read_csv(r/'tables/case_vehicle_three_periods.csv');assert set(levels.period)==set(periods)
nb=nbformat.read(p/'Bangkok_Traffic_V4_Colab.ipynb',4);cells=[c for c in nb.cells if c.cell_type=='code'];assert all(c.execution_count is not None for c in cells);assert not any(o.output_type=='error' for c in cells for o in c.outputs)
imgs=[hashlib.sha256(base64.b64decode(o.data['image/png'])).hexdigest() for c in cells for o in c.outputs if 'image/png' in o.get('data',{})];figs=list((r/'figures').glob('*.png'));assert len(imgs)==len(figs)==7;assert all(hashlib.sha256(f.read_bytes()).hexdigest() in imgs for f in figs)
root=p.parents[1];old=json.loads((p/'previous_versions_hashes.json').read_text());assert all(hashlib.sha256((root/f).read_bytes()).hexdigest()==h for f,h in old.items())
result={'overview_independently_recomputed':True,'lockdown_independently_recomputed':True,'three_period_shares_sum_100':True,'case_vehicles_have_three_periods':True,'notebook_cells':len(cells),'notebook_errors':0,'images_match_local':7,'old_files_unchanged':len(old),'source_sha256':m['source_sha256'],'lockdown_index':index}
(p/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
