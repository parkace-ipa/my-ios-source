"""Loopback-only manager. GitHub authentication stays in the local gh credential store."""
import http.server, json, secrets, subprocess, tempfile, urllib.parse
from pathlib import Path
from core import ROOT, BASE, load, write, fetch, config_valid, normalize, update
from ipa import inspect_ipa
import publish
NONCE=secrets.token_urlsafe(32)
PORT=8765
REPO='parkace-ipa/my-ios-source'

def gh(*args):
    r=subprocess.run(['gh',*args],capture_output=True,text=True,timeout=600)
    if r.returncode: raise ValueError(r.stderr[:1000])
    return r.stdout

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT/'dist'),**kwargs)
    def allowed(self):
        return self.headers.get('Host')==f'127.0.0.1:{PORT}'
    def reply(self,value,code=200):
        data=json.dumps(value,ensure_ascii=False).encode(); self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if not self.allowed(): return self.send_error(403)
        path=urllib.parse.urlsplit(self.path).path
        if path in ('/', '/index.html'):
            data=(ROOT/'admin/index.html').read_text().replace('<!--LOCAL-->','<meta name="local-key" content="'+NONCE+'">').encode()
            mime='text/html; charset=utf-8'
        else:
            files={'/app.js':(ROOT/'admin/app.js','text/javascript; charset=utf-8'),
                   '/style.css':(ROOT/'admin/style.css','text/css; charset=utf-8'),
                   '/config.json':(ROOT/'config.json','application/json; charset=utf-8'),
                   '/source.json':(ROOT/'source.json','application/json; charset=utf-8'),
                   '/status.json':(ROOT/'status.json','application/json; charset=utf-8'),
                   '/icon.png':(ROOT/'web/icon.png','image/png')}
            if path not in files: return self.send_error(404)
            file,mime=files[path]; data=file.read_bytes()
        self.send_response(200); self.send_header('Content-Type',mime)
        self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        if not self.allowed() or self.headers.get('X-Local-Key')!=NONCE: return self.send_error(403)
        if self.headers.get('Origin') not in (None,f'http://127.0.0.1:{PORT}'): return self.send_error(403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>2_000_000_000: raise ValueError('파일은 2GB 이하만 지원합니다')
            if self.path=='/api/upload':
                # Authenticate before receiving a potentially large IPA.
                gh('api','user','--jq','.login')
                with tempfile.TemporaryDirectory() as temp:
                    path=Path(temp)/'app.ipa'
                    with path.open('wb') as f:
                        left=size
                        while left:
                            chunk=self.rfile.read(min(left,1024*1024))
                            if not chunk: raise ValueError('업로드 연결 중단')
                            f.write(chunk); left-=len(chunk)
                    app,icon=inspect_ipa(path)
                    tag='ipa-'+secrets.token_hex(8)
                    # Draft first; only publish after both assets are successfully uploaded.
                    gh('release','create',tag,'--repo',REPO,'--draft','--title',app['name']+' '+app['versions'][0]['version'],'--notes','Uploaded with local ParkAce manager')
                    gh('release','upload',tag,str(path),'--repo',REPO)
                    if icon:
                        ip=Path(temp)/'icon.png'; ip.write_bytes(icon); gh('release','upload',tag,str(ip),'--repo',REPO)
                        app['iconURL']=f'https://github.com/{REPO}/releases/download/{tag}/icon.png'
                    gh('release','edit',tag,'--repo',REPO,'--draft=false')
                    app['versions'][0]['downloadURL']=f'https://github.com/{REPO}/releases/download/{tag}/app.ipa'
                    return self.reply({'app':app,'note':'Release 업로드 완료. 앱 등록 후 설정을 저장하고 GitHub에 반영하세요. 아이콘 추출 실패 시 기본 아이콘을 사용합니다.'})
            if size>10*1024*1024: raise ValueError('요청은 10MB 이하만 지원합니다')
            body=json.loads(self.rfile.read(size))
            if self.path=='/api/browse': return self.reply(fetch(body['url']))
            if self.path=='/api/deploy-status': return self.reply(publish.status(body['sha'],body['startedAt']))
            if self.path=='/api/deploy':
                config_valid(body); publish.preflight()
                write('config.json',body); update()
                subprocess.run(['python3',str(ROOT/'scripts/build.py')],check=True)
                return self.reply(publish.publish())
            if self.path=='/api/save':
                config_valid(body); write('config.json',body); update()
            elif self.path=='/api/refresh': update()
            else: return self.send_error(404)
            subprocess.run(['python3',str(ROOT/'scripts/build.py')],check=True)
            self.reply({'ok':True,'message':'내 컴퓨터에 저장했습니다. GitHub 반영에는 commit/push가 필요합니다.'})
        except Exception as e: self.reply({'error':str(e)},400)

if __name__=='__main__':
    subprocess.run(['python3',str(ROOT/'scripts/build.py')],check=True)
    print(f'한국어 관리 화면: http://127.0.0.1:{PORT} (종료: Ctrl+C)',flush=True)
    http.server.HTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
