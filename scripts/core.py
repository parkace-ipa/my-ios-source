"""Source normalization, bounded public HTTPS fetches, and atomic publication."""
import copy, datetime, ipaddress, json, os, socket, tempfile, urllib.request, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://parkace-ipa.github.io/my-ios-source/'

def load(path, default=None):
    p = ROOT / path
    return json.loads(p.read_text()) if p.exists() else copy.deepcopy(default)

def write(path, data):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=p.parent, delete=False) as f:
        json.dump(data, f, ensure_ascii=False, indent=2); f.write('\n'); tmp = f.name
    os.replace(tmp, p)

def url(value):
    u = urllib.parse.urlsplit(value)
    if u.scheme != 'https' or not u.hostname or u.username or u.password:
        raise ValueError('공개 HTTPS 주소가 필요합니다')
    return value

def public_url(value):
    url(value)
    u = urllib.parse.urlsplit(value)
    for address in socket.getaddrinfo(u.hostname, u.port or 443, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(address[4][0]).is_global:
            raise ValueError('내부 네트워크 주소는 사용할 수 없습니다')
    return value

class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def fetch(address):
    public_url(address)
    req = urllib.request.Request(address, headers={'User-Agent':'ParkAce-IPA-Source/1.0','Accept':'application/json'})
    with urllib.request.build_opener(Redirect).open(req, timeout=25) as r:
        data = r.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024: raise ValueError('소스 JSON은 10MB 이하만 지원합니다')
    result = json.loads(data)
    if not isinstance(result, dict) or not isinstance(result.get('apps'), list): raise ValueError('apps 배열이 없습니다')
    return result

def normalize(app):
    a = {k: copy.deepcopy(app[k]) for k in ('name','bundleIdentifier','developerName','localizedDescription','iconURL','subtitle','tintColor') if k in app}
    for k in ('name','bundleIdentifier','developerName','localizedDescription','iconURL'):
        if not isinstance(a.get(k), str) or not a[k].strip(): raise ValueError('앱 필수 항목 누락: '+k)
    url(a['iconURL'])
    versions = app.get('versions')
    if versions is None:
        versions = [{'version':app.get('version'),'date':app.get('versionDate'),'downloadURL':app.get('downloadURL'),'size':app.get('size')}]
    if not isinstance(versions, list) or not versions: raise ValueError('버전 정보가 없습니다')
    a['versions'] = []
    for v in versions:
        for k in ('version','date','downloadURL'):
            if not isinstance(v.get(k), str) or not v[k]: raise ValueError('버전 필수 항목 누락: '+k)
        datetime.datetime.fromisoformat(v['date'].replace('Z','+00:00'))
        url(v['downloadURL'])
        if type(v.get('size')) is not int or v['size'] <= 0: raise ValueError('IPA 크기는 실제 양의 정수 바이트여야 합니다')
        # Keep upstream order: AltStore considers index 0 the newest compatible version.
        a['versions'].append({k:copy.deepcopy(v[k]) for k in ('version','buildVersion','date','downloadURL','size','minOSVersion','maxOSVersion','localizedDescription') if k in v})
    # Modern AltStore permissions are retained only if explicitly supplied; never fabricate them.
    if 'appPermissions' in app: a['appPermissions'] = copy.deepcopy(app['appPermissions'])
    return a

def config_valid(c):
    if not isinstance(c.get('sources'), list) or not isinstance(c.get('manualApps'), list): raise ValueError('설정 형식 오류')
    seen = set()
    for s in c['sources']:
        if not isinstance(s.get('id'), str) or not s['id'] or s['id'] in seen: raise ValueError('소스 ID 중복 또는 누락')
        seen.add(s['id']); url(s['url'])
        if not isinstance(s.get('selected'), dict): raise ValueError('선택 목록 형식 오류')
        if any(type(v) is not bool for v in s['selected'].values()): raise ValueError('자동 갱신 값은 true/false여야 합니다')
    for a in c['manualApps']: normalize(a)

def update(fetcher=fetch):
    c = load('config.json'); config_valid(c)
    cache = load('state.json', {'apps':{}})['apps']; next_cache = {}; apps = {}; messages=[]
    # Explicit manual entries win over external duplicates.
    for app in c['manualApps']:
        a=normalize(app)
        if a['bundleIdentifier'] in apps: raise ValueError('직접 등록 앱 Bundle ID 중복')
        apps[a['bundleIdentifier']]=a
    for s in c['sources']:
        selected=s['selected']; remote={}
        if selected:
            try:
                for a in fetcher(s['url'])['apps']:
                    bid=a.get('bundleIdentifier')
                    if bid in remote: raise ValueError('원본 소스 Bundle ID 중복: '+bid)
                    remote[bid]=a
                messages.append({'source':s['id'],'ok':True})
            except Exception as e: messages.append({'source':s['id'],'ok':False,'message':str(e)})
        for bid, auto in selected.items():
            key=s['id']+'|'+bid; a=cache.get(key)
            if auto or a is None:
                try: a=normalize(remote[bid])
                except Exception as e: messages.append({'source':s['id'],'app':bid,'ok':False,'message':'기존 데이터 유지: '+str(e)})
            if a:
                next_cache[key]=a
                if bid not in apps: apps[bid]=a
                else: messages.append({'app':bid,'ok':False,'message':'중복: 직접 등록 앱 또는 앞선 소스 우선'})
    source={'name':'ParkAce IPA Store','identifier':'io.github.parkace-ipa.my-ios-source','apps':list(apps.values())}
    write('state.json',{'apps':next_cache}); write('source.json',source)
    side=copy.deepcopy(source)
    for a in side['apps']:
        a.pop('appPermissions',None)
        for v in a['versions']: v.pop('buildVersion',None)
    write('sidestore.json',side)
    write('status.json',{'updatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'messages':messages,'appCount':len(apps)})
    return source

if __name__ == '__main__':
    print('Published apps:',len(update()['apps']))
