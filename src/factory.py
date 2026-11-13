#!/usr/bin/env python3
"""Local WebOps run controller. Workers propose data; trusted code applies bounded edits."""
import argparse, functools, hashlib, json, os, re, shutil, subprocess, sys, threading, time, uuid
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from siteops import write,read,sha,confined,intake,audit,apply
ROOT=Path(__file__).resolve().parents[1];RUNTIME=ROOT/'.runtime';DEPS=RUNTIME/'deps';RUNS=RUNTIME/'runs';KUJO=DEPS/'kujo/target/release/kujo'
CSP="default-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; script-src 'none'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
SCHEMA={'type':'object','additionalProperties':False,'required':['edits'],'properties':{'edits':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['findingId','value','reason'],'properties':{k:{'type':'string'} for k in ['findingId','value','reason']}}}}}
REVIEW={'type':'object','additionalProperties':False,'required':['verdict','findings'],'properties':{'verdict':{'type':'string','enum':['pass','revise']},'findings':{'type':'array','items':{'type':'string'}}}}

class Preview(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def end_headers(self):
        self.send_header('Content-Security-Policy',CSP);self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
    def do_GET(self):
        name=unquote(urlsplit(self.path).path).lstrip('/') or 'index.html'
        try:
            p=confined(Path(self.directory),name)
            if p.is_dir():p=confined(Path(self.directory),name+'/index.html')
            if not p.is_file():raise ValueError('Not found')
        except ValueError:self.send_error(404);return
        super().do_GET()
    def do_HEAD(self):self.do_GET()

class Server:
    def __init__(self,root):self.server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Preview,directory=str(root)))
    def __enter__(self):threading.Thread(target=self.server.serve_forever,daemon=True).start();return 'http://127.0.0.1:'+str(self.server.server_port)
    def __exit__(self,*args):self.server.shutdown();self.server.server_close()

def command(args,cwd,log,timeout=180):
    started=time.monotonic();p=subprocess.run([str(x) for x in args],cwd=cwd,env={**os.environ,'KUJO_BIN':str(KUJO)},capture_output=True,text=True,timeout=timeout)
    write(log,{'command':[str(x) for x in args],'exitCode':p.returncode,'durationSeconds':round(time.monotonic()-started,3),'stdout':p.stdout[-60000:],'stderr':p.stderr[-12000:]})
    return p

def evidence(run,site,label):
    out=run/'evidence'/label;out.mkdir(parents=True)
    with Server(site) as url:
        p=command([DEPS/'siteprobe/siteprobe','crawl',url,'--out',out/'siteprobe','--allow-private-network','--max-pages','30','--max-depth','3','--max-output-bytes','10485760','--json'],DEPS/'siteprobe',out/'siteprobe-command.json')
        if p.returncode:raise ValueError('SiteProbe failed; inspect evidence receipt')
        p=command([DEPS/'siteprobe/siteprobe','verify',out/'siteprobe'],DEPS/'siteprobe',out/'siteprobe-verify.json')
        if p.returncode:raise ValueError('SiteProbe artifact verification failed')
        p=command([DEPS/'lens/lens','check',url,'--out',out/'lens','--check-links','--accessibility','--fail-on','error','--json'],DEPS/'lens',out/'lens-command.json',240)
        if p.returncode not in (0,1) or not (out/'lens/lens-report.json').exists():raise ValueError('Lens browser check failed; inspect evidence receipt')
    return {'siteprobe':'evidence/'+label+'/siteprobe','lens':'evidence/'+label+'/lens','lensExitCode':p.returncode}

def propose(run,key,role,task,data,schema,fixture=False):
    request={'role':role,'task':task,'data':data,'schema':schema};write(run/'requests'/f'{key}.json',request)
    if len(json.dumps(request))>150000:raise ValueError('Worker context exceeds 150 KB limit')
    if fixture:
        if schema==REVIEW:proposal={'verdict':'pass','findings':[]}
        else:
            values=read(run/'mission.json').get('fixtureValues',{});proposal={'edits':[{'findingId':f['id'],'value':values[f['file']+':'+f['kind']],'reason':'Explicit fixture repair for offline testing.'} for f in data['findings']]}
        response={'proposal':proposal,'provider':'fixture','role':role,'usage':[]}
    else:
        p=subprocess.run(['node',str(ROOT/'scripts/propose.mjs')],input=json.dumps(request),text=True,capture_output=True,timeout=510)
        if p.returncode:raise ValueError('Live worker failed; check login and model access')
        response=json.loads(p.stdout);proposal=response['proposal']
    write(run/'proposals'/f'{key}.json',response);return proposal

def package(run):
    files=[]
    for area in ['before','candidate','evidence','proposals','requests','patches']:
        for p in sorted((run/area).rglob('*')):
            if p.is_file():files.append({'path':p.relative_to(run).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
    for name in ['mission.json','intake.json','before-findings.json','after-findings.json','review.json']:
        p=run/name;files.append({'path':name,'sha256':sha(p),'bytes':p.stat().st_size})
    return write(run/'package.json',{'schema':'kujo.webops-factory.package/v1','status':'approval_required','files':files,'productionMutation':False})

def verify(run):
    m=read(run/'package.json')
    if m.get('schema')!='kujo.webops-factory.package/v1' or not m.get('files'):raise ValueError('Invalid package')
    for f in m['files']:
        if sha(confined(run,f['path']))!=f['sha256']:raise ValueError('Package drift: '+f['path'])
    return {'ok':True,'files':len(m['files']),'packageSha256':sha(run/'package.json')}

def import_example():
    source=ROOT/'docs/example-run';verify(source);state=read(source/'state.json');rid=state['id']
    if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}',rid):raise ValueError('Invalid recorded run ID')
    target=confined(RUNS,rid)
    if target.exists():
        verify(target)
        if sha(target/'package.json')!=sha(source/'package.json'):raise ValueError('Existing run differs from recorded example')
    else:
        target.mkdir(parents=True)
        try:
            for name in [f['path'] for f in read(source/'package.json')['files']]+['package.json','state.json']:
                src=confined(source,name);dst=confined(target,name);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
            verify(target)
        except Exception:
            shutil.rmtree(target);raise
    print('Imported recorded live example: '+rid+' (no new model execution)')
    return 0

def execute(mission_path,fixture=False):
    mission_path=Path(mission_path).resolve();m=read(mission_path)
    if set(m)-{'title','site','objective','fixtureValues'} or not all(isinstance(m.get(k),str) and m[k].strip() for k in ['title','site','objective']):raise ValueError('Mission needs title, site and objective')
    if len(m['title'])>160 or len(m['objective'])>4000:raise ValueError('Mission text exceeds limits')
    source=(mission_path.parent/m['site']).resolve();rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8];run=RUNS/rid;run.mkdir(parents=True);start=time.monotonic()
    state={'id':rid,'title':m['title'],'status':'running','mode':'fixture' if fixture else 'live','stage':0,'stages':[],'counts':{},'providerCalls':0};write(run/'mission.json',m)
    def stage(n,name):state['stage']=n;state['stages'].append({'name':name,'startedAt':datetime.now(timezone.utc).isoformat()});write(run/'state.json',state);print(name,flush=True)
    try:
        stage(0,'Snapshot');manifest=intake(source,run/'before');write(run/'intake.json',manifest);shutil.copytree(run/'before',run/'candidate')
        stage(1,'Inspect');before=audit(run/'before');write(run/'before-findings.json',before);state['counts']={'before':len(before),'after':None,'pages':len(list((run/'before').rglob('*.html')))};write(run/'state.json',state);evidence(run,run/'before','before')
        stage(2,'Propose');edits=[]
        for role,kinds in [('metadata-auditor',['title','description']),('link-health-auditor',['broken_link']),('accessibility-auditor',['image_alt'])]:
            findings=[f for f in before if f['kind'] in kinds]
            if not findings:continue
            data={'objective':m['objective'],'findings':findings,'pages':{p.relative_to(run/'before').as_posix():p.read_text() for p in (run/'before').rglob('*.html')},'availableFiles':[f['path'] for f in manifest],'illustrations':{p.name:p.read_text() for p in (run/'before').rglob('*.svg') if p.stat().st_size<20000}}
            proposal=propose(run,role,role,'Propose one repair for each supplied finding. Use only its findingId, a plain-text value, and reason. Titles and descriptions must fit the actual page. Image alternatives must describe only clearly identifiable elements in the supplied SVG/content. Prefer a short conservative description; omit ambiguous objects rather than guessing tools, people, or activities. Link targets must be existing local HTML paths. No markup, commands, new files, or external URLs. The trusted controller applies values only to a disposable candidate copy.',data,SCHEMA,fixture)
            if set(proposal)!={'edits'} or not isinstance(proposal['edits'],list):raise ValueError('Invalid proposal')
            allowed={f['id'] for f in findings}
            if any(e.get('findingId') not in allowed for e in proposal['edits']):raise ValueError('Worker exceeded assigned finding scope')
            edits+=proposal['edits'];state['providerCalls']+=0 if fixture else 1;write(run/'state.json',state)
        stage(3,'Repair');apply(run/'candidate',before,edits)
        import difflib
        patch=''
        for entry in manifest:
            rel=entry['path'];a=confined(run/'before',rel);b=confined(run/'candidate',rel)
            if sha(a)!=sha(b):patch+=''.join(difflib.unified_diff(a.read_text().splitlines(True),b.read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
        write(run/'patches/repairs.diff',patch);write(run/'patches/edits.json',edits)
        stage(4,'Verify');after=audit(run/'candidate');write(run/'after-findings.json',after);state['counts']['after']=len(after);state['counts']['repaired']=len(before)-len(after);write(run/'state.json',state);proof=evidence(run,run/'candidate','after')
        if after:raise ValueError('Candidate still has supported findings; no approval package produced')
        if proof['lensExitCode']!=0:raise ValueError('Candidate browser checks still report errors; no approval package produced')
        review=propose(run,'independent-review','site-qa-operator','Independently review the proposed text and exact diff for unsupported claims, wrong link targets, invented image descriptions, loss of meaning or harmful changes. Deterministic checks already passed. Return pass only if no substantive issue remains; this is model review, not human approval.',{'objective':m['objective'],'diff':patch,'beforeFindings':before,'afterFindings':after,'edits':edits,'sourcePages':{p.relative_to(run/'before').as_posix():p.read_text() for p in (run/'before').rglob('*.html')},'availableFiles':[f['path'] for f in manifest],'illustrations':{p.name:p.read_text() for p in (run/'before').rglob('*.svg') if p.stat().st_size<20000}},REVIEW,fixture)
        if set(review)!={'verdict','findings'} or review['verdict'] not in ['pass','revise'] or not isinstance(review['findings'],list) or any(not isinstance(x,str) for x in review['findings']):raise ValueError('Invalid review')
        write(run/'review.json',review);state['providerCalls']+=0 if fixture else 1
        if review['verdict']!='pass' or review['findings']:raise ValueError('Independent reviewer requested revision; inspect review.json and rerun with clarified mission')
        for entry in manifest:
            if sha(confined(source,entry['path']))!=entry['sha256']:raise ValueError('Original source changed during run')
        stage(5,'Package');package(run);result=verify(run);state['packageSha256']=result['packageSha256'];state['status']='approval_required';state['stage']=6
    except Exception as e:state['status']='blocked';state['error']=str(e)
    state['durationSeconds']=round(time.monotonic()-start,3);write(run/'state.json',state);print(json.dumps(state,indent=2));return 0 if state['status']=='approval_required' else 1

class Floor(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        path=unquote(urlsplit(self.path).path)
        if path=='/api/runs':
            records=[read(p) for p in sorted(RUNS.glob('*/state.json'),reverse=True)];payload=json.dumps(records).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(payload);return
        if path=='/':p=ROOT/'web/index.html'
        elif path.startswith('/artifact/'):
            try:p=confined(RUNS,path[len('/artifact/'):])
            except ValueError:self.send_error(404);return
        else:self.send_error(404);return
        if not p.is_file():self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',self.guess_type(str(p)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        if path.startswith('/artifact/'):self.send_header('Content-Security-Policy',CSP)
        self.end_headers();self.wfile.write(p.read_bytes())

def doctor():
    required=[KUJO,ROOT/'node_modules/.bin/codex',DEPS/'siteprobe/siteprobe',DEPS/'lens/lens',DEPS/'lens/bridge/node_modules/playwright-core/package.json',DEPS/'kujo-agents/webops/site-qa-operator/AGENT.md']
    missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:print(json.dumps({'ok':False,'missing':missing}));return 1
    browser=subprocess.run(['node',str(ROOT/'scripts/check-browser.mjs')],capture_output=True,text=True,timeout=30)
    if browser.returncode:print(json.dumps({'ok':False,'error':'Chromium could not launch. Run npm run setup; on Linux install Playwright system dependencies.'}));return 1
    p=subprocess.run([str(DEPS/'siteprobe/siteprobe'),'doctor'],env={**os.environ,'KUJO_BIN':str(KUJO)},capture_output=True,text=True,timeout=30)
    print(json.dumps({'ok':p.returncode==0,'runtime':p.stdout.strip(),'providerAuthenticated':(RUNTIME/'provider/auth.json').exists()}));return 0 if p.returncode==0 else 1

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True);sub.add_parser('doctor');sub.add_parser('import-example');s=sub.add_parser('serve');s.add_argument('--port',type=int,default=4383);s=sub.add_parser('run');s.add_argument('mission');mode=s.add_mutually_exclusive_group(required=True);mode.add_argument('--live',action='store_true');mode.add_argument('--fixture',action='store_true');s=sub.add_parser('verify');s.add_argument('run');args=p.parse_args()
    if args.command=='doctor':return doctor()
    if args.command=='import-example':return import_example()
    if args.command=='run':return execute(args.mission,args.fixture)
    if args.command=='verify':print(json.dumps(verify(confined(RUNS,args.run)),indent=2));return 0
    print('Factory floor: http://127.0.0.1:'+str(args.port),flush=True);ThreadingHTTPServer(('127.0.0.1',args.port),Floor).serve_forever()
if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as e:print(str(e),file=sys.stderr);sys.exit(1)
