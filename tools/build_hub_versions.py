"""Export pinned Git Hub interfaces, reject malformed HTML/JS, keep stable separate."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL)


def build(repo, output, stable, backend_version):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    versions = [{'id':'stable-deployed','label':'Estable implementada','version':backend_version,'available':True,'url':'/hub.html','reason':'Interfaz estable con panel master integrado'}]
    refs = git(repo,'for-each-ref','--format=%(refname)','refs/remotes/origin','refs/tags').decode().splitlines()
    for ref in refs:
        if ref.endswith('/HEAD'): continue
        try: raw = git(repo,'show',ref+':web/hub.html')
        except subprocess.CalledProcessError: continue
        short = ref.replace('refs/remotes/origin/','').replace('refs/tags/','tag/')
        identity = re.sub('[^a-z0-9]+','-',short.lower()).strip('-')
        html = raw.decode('utf-8-sig')
        html = re.sub(r'<script[^>]*src=[\"\x27]/hub-version-switcher\.js[^>]*></script>', '', html)
        commit = git(repo,'rev-parse',ref).decode().strip()
        try: config = git(repo,'show',ref+':core/config.py').decode('utf-8-sig')
        except subprocess.CalledProcessError: config = ''
        match = re.search(r'APP_VERSION\s*=\s*[\"\x27]([^\"\x27]+)',config)
        row = {'id':identity,'label':short,'ref':ref,'commit':commit,'version':match.group(1) if match else None,'htmlSha256':hashlib.sha256(raw).hexdigest(),'available':True,'url':f'/hub-releases/{identity}/hub.html'}
        reason = ''
        repaired = False
        legacy = re.search(r'<script>\s*const layouts\s*=', html)
        if legacy and len(re.findall(r'<!doctype\s+html',html,re.I)) > 1:
            html = html[:legacy.start()] + '</body></html>'
            repaired = True
        if len(re.findall(r'<!doctype\s+html',html,re.I)) != 1 or len(re.findall(r'<html\b',html,re.I)) != 1:
            reason = 'Bloqueada: documentos HTML concatenados; necesita reparación'
        if not reason:
            scripts=[]
            for attrs,body in re.findall(r'<script\b([^>]*)>(.*?)</script>',html,re.S|re.I):
                if not re.search(r'\bsrc\s*=',attrs,re.I) and not re.search(r'type\s*=\s*[\"\x27](?:application/ld\+json|application/json)',attrs,re.I): scripts.append(body)
            check=subprocess.run(['node','--check'],input='\n'.join(scripts).encode(),capture_output=True)
            if check.returncode: reason='Bloqueada: JavaScript inválido; necesita reparación'
        if not reason:
            folder=output/identity;folder.mkdir(exist_ok=True)
            for src in set(re.findall(r'<script[^>]+src=[\"\x27]([^\"\x27]+)',html)):
                if src.startswith(('https:','http:','//')): continue
                file=src.split('?')[0].lstrip('/')
                if '..' in Path(file).parts: reason='Bloqueada: ruta de recurso no admitida';break
                try: data=git(repo,'show',ref+':web/'+file)
                except subprocess.CalledProcessError: reason='Bloqueada: falta recurso '+file;break
                target=folder/file;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                html=html.replace(src,f'/hub-releases/{identity}/{file}')
            if not reason:
                html=html.replace('<head>','<head><base href="/">',1)
                html=html.replace('</body>',f'<script src="/hub-version-switcher.js?v=1" data-hub-version="{identity}"></script></body>')
                (folder/'hub.html').write_text(html,encoding='utf-8')
        row['available']=not bool(reason)
        row['reason']=reason or ('Selector antiguo anidado retirado; interfaz sobre motor estable' if repaired else 'Interfaz de GitHub; utiliza el motor estable, sin cambiar sus permisos')
        row['legacySelectorRemoved']=repaired
        versions.append(row)
    catalog={'schema':1,'backendVersion':backend_version,'versions':versions}
    (output/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    html=Path(stable).read_text(encoding='utf-8-sig')
    html=re.sub(r'<script[^>]*src=[\"\x27]/hub-version-switcher\.js[^>]*></script>', '', html)
    html=html.replace('</body>','<script src="/hub-version-switcher.js?v=1" data-hub-version="stable-deployed"></script></body>')
    (output.parent/'hub-stable-candidate.html').write_text(html,encoding='utf-8')
    return catalog


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--output',required=True);p.add_argument('--stable',required=True);p.add_argument('--backend-version',required=True)
    a=p.parse_args();catalog=build(a.repo,a.output,a.stable,a.backend_version)
    for row in catalog['versions']:print(row['label'],row['available'],row['reason'])
