"""Publish only the source settings; never force-push or include unrelated edits."""
import datetime, json, re, subprocess
from core import ROOT
REPO='parkace-ipa/my-ios-source'
FILES=['config.json','source.json','sidestore.json','state.json','status.json']

def command(*args):
    r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=120)
    if r.returncode: raise ValueError(r.stderr.strip() or '명령 실행 실패')
    return r.stdout.strip()

def preflight():
    if command('git','branch','--show-current')!='main': raise ValueError('main 브랜치에서 실행하세요.')
    remote=command('git','remote','get-url','origin')
    if remote not in ('https://github.com/'+REPO+'.git','https://github.com/'+REPO,'git@github.com:'+REPO+'.git'):
        raise ValueError('배포 대상 저장소가 일치하지 않습니다.')
    if command('git','diff','--cached','--name-only'): raise ValueError('이미 준비된 다른 변경이 있습니다. 먼저 해당 작업을 완료한 뒤 배포하세요.')
    dirty=command('git','diff','--name-only').splitlines()
    if any(p not in FILES for p in dirty): raise ValueError('프로그램 파일에 저장하지 않은 변경이 있습니다. 해당 작업을 완료한 뒤 배포하세요.')
    if command('gh','api','user','--jq','.login')!='parkace-ipa': raise ValueError('parkace-ipa 계정으로 GitHub에 로그인하세요.')

def publish():
    started=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
    command('git','add','--',*FILES)
    if command('git','diff','--cached','--name-only'):
        command('git','commit','-m','Update apps from local manager','--',*FILES)
    command('git','fetch','origin','main')
    try: command('git','rebase','origin/main')
    except ValueError:
        command('git','rebase','--abort')
        raise ValueError('GitHub 변경과 충돌하여 배포를 중단했습니다. 설정은 내 Mac의 커밋에 보관했습니다. 충돌 해결이 필요합니다.')
    sha=command('git','rev-parse','HEAD')
    remote=command('git','rev-parse','origin/main')
    if sha!=remote: command('git','push','origin','main')
    else: command('gh','workflow','run','publish.yml','--repo',REPO,'--ref','main')
    return {'ok':True,'sha':sha,'startedAt':started,'message':'GitHub 반영 완료. 공개 페이지 배포를 확인하고 있습니다.'}

def status(sha,started):
    if not re.fullmatch(r'[0-9a-f]{40}',sha): raise ValueError('배포 식별자가 올바르지 않습니다.')
    datetime.datetime.fromisoformat(started.replace('Z','+00:00'))
    runs=json.loads(command('gh','run','list','--repo',REPO,'--workflow','publish.yml','--commit',sha,'--limit','10','--json','status,conclusion,url,createdAt'))
    matches=[r for r in runs if r['createdAt']>=started]
    return matches[0] if matches else {'status':'queued','conclusion':'','url':'https://github.com/'+REPO+'/actions'}
