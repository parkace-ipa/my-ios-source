import datetime, plistlib, zipfile
from core import BASE

def inspect_ipa(path):
    with zipfile.ZipFile(path) as z:
        entries=[n for n in z.namelist() if n.startswith('Payload/') and n.count('/')==2 and n.endswith('.app/Info.plist')]
        if len(entries)!=1: raise ValueError('Payload에 앱 Info.plist가 정확히 하나 있어야 합니다')
        info=z.getinfo(entries[0])
        if info.file_size>4*1024*1024: raise ValueError('Info.plist가 너무 큽니다')
        p=plistlib.loads(z.read(info)); prefix=entries[0].rsplit('/',1)[0]+'/'
        icons=p.get('CFBundleIcons',{}).get('CFBundlePrimaryIcon',{}).get('CFBundleIconFiles',p.get('CFBundleIconFiles',[]))
        icon=None
        for name in reversed(icons):
            candidates=[n for n in z.namelist() if n.startswith(prefix+name) and n.endswith('.png') and z.getinfo(n).file_size<4*1024*1024]
            if candidates:
                data=z.read(candidates[-1])
                # iOS CgBI PNGs need conversion. Do not publish a broken icon.
                if data.startswith(b'\x89PNG') and b'CgBI' not in data[:64]: icon=data
                break
        app={'name':p.get('CFBundleDisplayName',p.get('CFBundleName','App')),'bundleIdentifier':p['CFBundleIdentifier'],'developerName':'ParkAce','localizedDescription':'직접 등록한 앱','iconURL':BASE+'icon.png','versions':[{'version':str(p['CFBundleShortVersionString']),'buildVersion':str(p.get('CFBundleVersion','1')),'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'downloadURL':'','size':path.stat().st_size}]}
        if p.get('MinimumOSVersion'): app['versions'][0]['minOSVersion']=p['MinimumOSVersion']
        return app,icon
