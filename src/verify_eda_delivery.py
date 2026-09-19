from pathlib import Path
import base64,hashlib,json,importlib.metadata
import nbformat,pandas as pd,numpy as np
root=Path.cwd();meta=json.loads((root/'outputs/current_audit/summary.json').read_text(encoding='utf-8'))
eda=json.loads((root/'outputs/eda/eda_summary.json').read_text(encoding='utf-8'))
source=Path('C:/Users/AphatsaraKhangkhet(C/Downloads/bangkok_traffic_2560_Present (NotFinal) (1).xlsx')
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['source_sha256']==eda['source']['source_sha256']
receipts=[];embedded=[]
for filename in ['01_data_feasibility_matching.ipynb','02_eda_and_visualization.ipynb']:
    nb=nbformat.read(root/'notebooks'/filename,as_version=4);nbformat.validate(nb)
    cells=[c for c in nb.cells if c.cell_type=='code']
    assert all(c.execution_count is not None for c in cells)
    errors=[o for c in cells for o in c.outputs if o.output_type=='error'];assert not errors
    imgs=[o['data']['image/png'] for c in cells for o in c.outputs if 'image/png' in o.get('data',{})]
    embedded.extend(hashlib.sha256(base64.b64decode(x)).hexdigest() for x in imgs)
    receipts.append({'notebook':filename,'executed_code_cells':len(cells),'errors':0,'embedded_images':len(imgs)})
plots=list((root/'outputs/eda/figures').glob('*.png'))+list((root/'outputs/additional_visuals/figures').glob('*.png'))+list((root/'outputs/traffic_patterns/figures').glob('*.png'));assert len(plots)==20
for p in plots:assert hashlib.sha256(p.read_bytes()).hexdigest() in embedded
m=pd.read_csv(root/'data/processed/traffic_matched_analysis.csv',low_memory=False)
assert m.source_excel_row.nunique()==len(m)==eda['results']['same_location_time']['rows']
raw=pd.read_excel(source,sheet_name='traffic_data');lookup=raw.covid_period.to_dict()
assert all(lookup[int(row)-2]==label for row,label in zip(m.source_excel_row,m.covid_period))
versions={p:importlib.metadata.version(p) for p in ['pandas','numpy','openpyxl','matplotlib','seaborn','nbformat','nbclient','ipykernel','nbconvert']}
receipt={'source_sha256':meta['source_sha256'],'source_unchanged':True,'notebooks':receipts,'figures_reviewed':20,'embedded_images_match_reviewed_files':True,'matched_rows':len(m),'period_labels_match_source':True,'versions':versions,'visual_qa':'All twenty chart images inspected; labels, axes, legends and notes readable. Full browser HTML preview not inspected.'}
(root/'outputs/eda/validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'outputs/current_audit/validation.json').write_text(json.dumps({'source_sha256':meta['source_sha256'],'notebook':receipts[0],'rows':meta['rows'],'covid_period_preserved':True,'zero_assumed_cells':meta['zero_assumed_cells']},ensure_ascii=False,indent=2),encoding='utf-8')
(root/'requirements-tested.txt').write_text('\n'.join(f'{p}=={v}' for p,v in versions.items())+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
