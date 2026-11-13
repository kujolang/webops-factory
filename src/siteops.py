"""Bounded static-site intake, deterministic checks and trusted patch operations."""
from html.parser import HTMLParser
from html import escape
from pathlib import Path
from urllib.parse import urlsplit, unquote
import hashlib, json, os, re, shutil, tempfile

MAX_FILES=120
MAX_BYTES=8_000_000
EXTENSIONS={'.html','.css','.svg','.png','.jpg','.jpeg','.webp','.ico','.txt','.xml'}

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    text=value if isinstance(value,str) else json.dumps(value,indent=2,ensure_ascii=False)+'\n'
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(text)
        os.replace(tmp,path)
    finally:
        if Path(tmp).exists():Path(tmp).unlink()
    return path

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def confined(root,relative):
    root=Path(root).resolve();p=Path(relative)
    if p.is_absolute() or '..' in p.parts:raise ValueError('Path escapes root')
    current=root
    for part in p.parts:
        current=current/part
        if current.is_symlink():raise ValueError('Symlinks are not allowed')
    p=(root/p).resolve()
    if p==root or not p.is_relative_to(root):raise ValueError('Path escapes root')
    return p

class Tags(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.tags=[];self.ends=[];self.offsets=[0]
        for line in text.splitlines(keepends=True):self.offsets.append(self.offsets[-1]+len(line))
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        line,col=self.getpos();self.tags.append({'tag':tag,'attrs':dict(attrs),'start':self.offsets[line-1]+col,'raw':self.get_starttag_text()})
    handle_startendtag=handle_starttag
    def handle_endtag(self,tag):
        line,col=self.getpos();self.ends.append({'tag':tag,'start':self.offsets[line-1]+col})

def intake(source,destination):
    source=Path(source)
    if source.is_symlink() or not source.is_dir():raise ValueError('Site must be a real directory')
    files=[];total=0
    for p in sorted(source.rglob('*')):
        if any(x.startswith('.') or x=='node_modules' for x in p.relative_to(source).parts):continue
        if p.is_symlink():raise ValueError('Site contains a symlink')
        if not p.is_file():continue
        if p.suffix.lower() not in EXTENSIONS:raise ValueError('Unsupported file: '+str(p.relative_to(source)))
        total+=p.stat().st_size;files.append(p)
        if len(files)>MAX_FILES or total>MAX_BYTES:raise ValueError('Site exceeds intake bounds')
        if p.suffix.lower() in {'.html','.svg'}:
            text=p.read_text()
            for t in Tags(text).tags:
                if t['tag'] in {'script','iframe','object','embed','base','foreignobject'} or (t['tag']=='meta' and 'http-equiv' in t['attrs']):raise ValueError('Active HTML is outside the static-site contract')
                if any(k.startswith('on') for k in t['attrs']):raise ValueError('Inline event handlers are outside the contract')
    if not any(p.suffix=='.html' for p in files):raise ValueError('No HTML pages found')
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    manifest=[]
    for p in files:
        rel=p.relative_to(source).as_posix();q=confined(destination,rel);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);manifest.append({'path':rel,'sha256':sha(q)})
    return manifest

def local_target(root,file,href):
    u=urlsplit(href)
    if u.scheme or u.netloc or not u.path:return None
    path=unquote(u.path)
    target=(root/path.lstrip('/')) if path.startswith('/') else (root/Path(file).parent/path)
    target=target.resolve()
    if not target.is_relative_to(root.resolve()):return root/'__outside_scope__'
    if target.is_dir():target=target/'index.html'
    return target

def title_span(text,parsed):
    title=next((t for t in parsed.tags if t['tag']=='title'),None)
    if title is None:return None
    end=next((t['start'] for t in parsed.ends if t['tag']=='title' and t['start']>title['start']),None)
    if end is None:raise ValueError('Unclosed title')
    return title['start']+len(title['raw']),end

def head_end(text):
    end=next((t['start'] for t in Tags(text).ends if t['tag']=='head'),None)
    if end is None:raise ValueError('Missing head boundary')
    return end

def audit(root):
    root=Path(root);findings=[]
    def add(file,kind,tag=None):
        ordinal=sum(1 for f in findings if f['file']==file and f['kind']==kind);key=f"{file}:{kind}:{ordinal}";fid=hashlib.sha256(key.encode()).hexdigest()[:12]
        findings.append({'id':fid,'file':file,'kind':kind,'tag':tag,'sourceSha256':sha(root/file),'severity':'error' if kind=='broken_link' else 'warning','label':{'title':'Page needs a title','description':'Page needs a search description','image_alt':'Image needs a text alternative','broken_link':'Internal link leads to a missing page'}[kind]})
    for p in sorted(root.rglob('*.html')):
        text=p.read_text();file=p.relative_to(root).as_posix();parsed=Tags(text);tags=parsed.tags
        title=title_span(text,parsed)
        if title is None or not text[title[0]:title[1]].strip():add(file,'title')
        metas=[t for t in tags if t['tag']=='meta' and str(t['attrs'].get('name','')).lower()=='description']
        if not metas or not str(metas[0]['attrs'].get('content') or '').strip():add(file,'description',metas[0] if metas else None)
        for t in tags:
            if t['tag']=='img' and 'alt' not in t['attrs']:add(file,'image_alt',t)
            if t['tag']=='a' and t['attrs'].get('href'):
                target=local_target(root,file,t['attrs']['href'])
                if target is not None and not target.is_file():add(file,'broken_link',t)
    return findings

def plain(value,maxlen):
    if not isinstance(value,str) or not value.strip() or len(value)>maxlen or any(ord(c)<32 for c in value) or '<' in value or '>' in value:raise ValueError('Invalid repair value')
    return value.strip()

def apply(root,findings,edits):
    root=Path(root);byid={f['id']:f for f in findings};seen=set();changes={}
    if not isinstance(edits,list) or len(edits)>len(findings):raise ValueError('Invalid edit count')
    for edit in edits:
        if set(edit)!={'findingId','value','reason'}:raise ValueError('Invalid edit shape')
        fid=edit['findingId']
        if fid not in byid or fid in seen:raise ValueError('Unknown or duplicate finding')
        seen.add(fid);f=byid[fid];value=plain(edit['value'],240);plain(edit['reason'],600)
        path=confined(root,f['file']);text=path.read_text();tag=f['tag'];kind=f['kind']
        if sha(path)!=f['sourceSha256']:raise ValueError('Source changed since audit')
        if kind=='title':
            value=plain(value,120);span=title_span(text,Tags(text))
            if span:start,end,new=span[0],span[1],escape(value)
            else:start=end=head_end(text);new='<title>'+escape(value)+'</title>\n'
        elif kind=='description' and tag is None:
            start=end=head_end(text);new='<meta name="description" content="'+escape(value,quote=True)+'">\n'
        else:
            attrs=dict(tag['attrs']);attribute={'description':'content','image_alt':'alt','broken_link':'href'}[kind]
            if kind=='broken_link':
                u=urlsplit(value)
                if u.scheme or u.netloc or '\\' in value:raise ValueError('Link repair must stay local')
                target=local_target(root,f['file'],value)
                if target is None or not target.is_file():raise ValueError('Link repair target does not exist')
            attrs[attribute]=value;start=tag['start'];end=start+len(tag['raw'])
            if text[start:end]!=tag['raw']:raise ValueError('Source changed since audit')
            new='<'+tag['tag']+''.join(' '+k+(('="'+escape(v,quote=True)+'"') if v is not None else '') for k,v in attrs.items())+'>'
        changes.setdefault(path,[]).append((start,end,new))
    # Validate every operation before writing any file. Reverse offsets preserve source positions.
    for path,ops in changes.items():
        text=path.read_text()
        for start,end,new in sorted(ops,reverse=True):text=text[:start]+new+text[end:]
        write(path,text)
    return len(edits)
