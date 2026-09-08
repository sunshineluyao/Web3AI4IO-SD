"""Check syntax, notebook structure, repository links and release inventories."""
from pathlib import Path
import argparse, ast, json, re, sys, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

def files():
    excluded={'.git','outputs','dist','__pycache__','.ipynb_checkpoints'}
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not excluded.intersection(p.relative_to(ROOT).parts))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allow-unpinned',action='store_true')
    args=parser.parse_args();errors=[];all_files=files();notebooks=[];code_count=0
    for p in all_files:
        if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
        if p.suffix=='.json':json.loads(p.read_text())
        if p.suffix=='.ipynb':
            n=json.loads(p.read_text());notebooks.append(p)
            assert n['nbformat']==4 and n['nbformat_minor']==5
            ids=[c['id'] for c in n['cells']];assert len(ids)==len(set(ids))
            content='\n'.join(c['source'] if isinstance(c['source'],str) else ''.join(c['source']) for c in n['cells'])
            for part in ['i','ii','iii','iv','v','vi','vii','viii']:
                assert content.count(f'id="part-{part}"')==1,(p,part)
            if not args.allow_unpinned:
                assert 'PIN_CODE_COMMIT' not in content,p
                assert re.search(r'CODE_COMMIT = "[0-9a-f]{40}"',content),p
            for i,c in enumerate(n['cells']):
                if c['cell_type']=='code':
                    code_count+=1;assert c['execution_count'] is None and c['outputs']==[]
                    ast.parse(c['source'],filename=f'{p.name}:cell{i}')
            for rel in re.findall(r'https://github.com/sunshineluyao/Web3AI4IO-SD/blob/[^/\s)]+/([^\s)]+)',content):
                if not (ROOT/rel).exists():errors.append(f'{p.name}: missing code/data link {rel}')
        if p.suffix=='.md':
            s=p.read_text()
            for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^\s)]+)\)',s):
                if target.startswith(('https:','http:','mailto:','#')):continue
                target=target.split('#')[0]
                if target and not (p.parent/target).resolve().exists():errors.append(f'{p.relative_to(ROOT)}: missing {target}')
        if p.stat().st_size > 2_000_000:errors.append(f'Unexpected large file: {p.name}')
    assert len(notebooks)==3
    svg=ET.parse(ROOT/'assets/pipeline.svg').getroot()
    tags=[n.tag.split('}')[-1] for n in svg.iter()]
    assert 'title' in tags and 'desc' in tags and 'text' in tags
    assert not {'image','script','foreignObject'}.intersection(tags)
    for r in json.loads((ROOT/'metadata/result_index.json').read_text()):
        for field in ['original_sources','query_code','queried_data','process_code','processed_data','analysis_code','result_outputs']:
            assert (ROOT/r[field]).exists(),(r['result_id'],field)
        assert r['evidence_status']=='SYNTHETIC'
    if errors:raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(all_files)} files; {len(notebooks)} notebooks; {code_count} code cells; syntax, local links, SVG and result paths.')

if __name__=='__main__':main()
