from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
count=0
for p in root.rglob('*.md'):
    if any(x in p.parts for x in ['.runtime','node_modules','.git']):continue
    count+=1
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('https://','http://','#','mailto:')):continue
        if not (p.parent/target.split('#')[0]).exists():raise SystemExit(f'Broken link in {p}: {target}')
print(f'Checked links in {count} Markdown files')
