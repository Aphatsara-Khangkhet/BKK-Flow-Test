from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,nbformat,re
root=Path.cwd();o=root/'outputs/diagnostics'
s=json.loads((o/'summary.json').read_text(encoding='utf-8'),parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
source=Path('C:/Users/AphatsaraKhangkhet(C/Downloads/bangkok_traffic_2560_Present (NotFinal) (1).xlsx')
assert hashlib.sha256(source.read_bytes()).hexdigest()==s['source_sha256']
x=pd.read_csv(root/'data/processed/traffic_analysis_candidates.csv',low_memory=False)
c=pd.read_csv(o/'case_survey_dates.csv');assert len(c)==68 and c.source_excel_row.is_unique
assert pd.to_datetime(c.survey_date_parsed).dt.day_name().equals(c.survey_weekday)
assert len(c.location_code.unique())==10
idx=pd.read_csv('outputs/eda/same_location_time_paired_indices.csv')
ci=pd.read_csv(o/'cluster_bootstrap.csv')
for _,r in ci.iterrows():assert np.isclose(r.median_index,idx[r.period].median())
m=pd.read_csv(o/'zero_vehicle_mix_sensitivity.csv')
assert np.allclose(m.groupby('design').Before_share.sum(),100)
assert np.allclose(m.groupby('design').After_share.sum(),100)
y=pd.read_csv(o/'after_year_matched_units.csv');assert np.allclose(y.paired_index,y.After_year/y.Before*100)
nb=nbformat.read('notebooks/Bangkok_Traffic_Colab.ipynb',4);nbformat.validate(nb);cells=[c for c in nb.cells if c.cell_type=='code'];assert all(c.execution_count is not None for c in cells)
assert not any(z.output_type=='error' for c in cells for z in c.outputs)
assert sum('image/png' in z.get('data',{}) for c in cells for z in c.outputs)==20
smoke=json.loads((root/'tmp/colab_isolated_test/bangkok_traffic_project/outputs/diagnostics/summary.json').read_text(encoding='utf-8'));assert smoke==s
links=[]
for file in ['Read.md','outputs/diagnostics/Location_Context_and_Methodology.md','outputs/diagnostics/Statistical_Diagnostics.md']:
 p=root/file
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if not link.startswith(('http','#')):assert (p.parent/link).exists(),link
receipt={'source_unchanged':True,'source_sha256':s['source_sha256'],'case_rows':68,'locations':10,'date_weekdays_checked':True,'index_formula_checked':True,'mix_sums_100':True,'colab_executed_cells':len(cells),'colab_errors':0,'colab_images':20,'isolated_colab_matches_local':True,'local_document_links_valid':True,'source_spot_check_discrepancies':2,'source_spot_check_scope':'Jul2017 p6 L09 row704; Mar2017 p3 L03 row62, not full-source reconciliation'}
(o/'validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(receipt,ensure_ascii=False,indent=2))
