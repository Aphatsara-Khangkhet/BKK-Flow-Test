from pathlib import Path
import json,hashlib,base64,nbformat,pandas as pd,numpy as np,ast
root=Path.cwd();o=root/'outputs/additional_visuals';s=json.loads((o/'summary.json').read_text())
roads=pd.read_csv(o/'map_road_period_indices.csv');points=pd.read_csv(o/'map_intersection_summary.csv');coords=pd.read_csv('data/reference/map_coordinates_reviewed.csv')
assert len(roads)==42 and len(points)==21
assert roads.inside_bangkok_boundary.all()
assert not coords.duplicated(['intersection_key','road_key']).any()
j=roads.merge(coords,on=['intersection_key','road_key'],validate='one_to_one');assert np.allclose(j.latitude_x,j.latitude_y) and np.allclose(j.longitude_x,j.longitude_y)
for _,p in points.iterrows():
 g=roads[roads.intersection_key.eq(p.intersection_key)]
 assert len(g)==p.road_units and np.isclose(g.After.median(),p.After)
heat=pd.read_csv(o/'location_period_heatmap.csv');assert len(heat)==17 and heat.Before.eq(100).all()
b=pd.read_csv(o/'location_bubble_data.csv');assert b.total_n.equals(b[['n_Before','n_During','n_After']].sum(axis=1))
images=list((root/'outputs/eda/figures').glob('*.png'))+list((o/'figures').glob('*.png'))+list((root/'outputs/traffic_patterns/figures').glob('*.png'));assert len(images)==20
nb=nbformat.read(root/'notebooks/Bangkok_Traffic_Colab.ipynb',4)
embedded=[hashlib.sha256(base64.b64decode(v['data']['image/png'])).hexdigest() for c in nb.cells if c.cell_type=='code' for v in c.outputs if 'image/png' in v.get('data',{})]
assert all(hashlib.sha256(p.read_bytes()).hexdigest() in embedded for p in images)
from zipfile import ZipFile
zpath=root/'tmp/colab_isolated_test/bangkok_traffic_results.zip'
with ZipFile(zpath) as z:
 names=z.namelist();assert sum(n.endswith('.png') for n in names)==20
 assert 'outputs/additional_visuals/bangkok_map_interactive.html' in names
 assert 'outputs/diagnostics/summary.json' in names
 assert 'data/reference/map_coordinates_reviewed.csv' in names
for f in ['src/run_project.py','src/traffic_additional_visuals.py','src/build_colab_notebook.py']:ast.parse((root/f).read_text(encoding='utf-8-sig'))
receipt={'plots':20,'mapped_intersections':21,'mapped_road_units':42,'coordinates_match_reviewed_snapshot':True,'map_aggregates_checked':True,'heatmap_locations':17,'bubble_total_n_checked':True,'colab_images_match_local':True,'colab_zip_includes_all_plots_diagnostics_map_assets_and_html':True,'static_visual_qa':'All six new figures inspected; bubble legend inspected after revision','interactive_qa':'JavaScript focus, selection, period and extent logic checked in DOM mock; actual browser layout unavailable due browser tool failure','source_discrepancy':'Excel row704 remains unchanged; draft caveat retained'}
(o/'validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(receipt,ensure_ascii=False,indent=2))
