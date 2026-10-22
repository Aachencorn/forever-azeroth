"""Reviewed SOOP profile URL resolver. Disabled until provider policy/config is verified.
No image bytes are saved. No scraper, thumbnail fallback or inferred LOGO URL.
"""
import argparse, hashlib, json, os, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
ROOT=Path(__file__).resolve().parents[1]
PROFILE_HOSTS={'profile.img.sooplive.co.kr','profile.img.sooplive.com','stimg.sooplive.co.kr','stimg.sooplive.com','profile.img.afreecatv.com'}
API_HOSTS={'openapi.sooplive.co.kr','openapi.sooplive.com'}
ID=re.compile(r'^[a-z0-9_]{2,25}$')
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args):return None

def valid_image(value,aid):
 if not isinstance(value,str):return ''
 if value.startswith('//'):value='https:'+value
 u=urlsplit(value)
 return value if u.scheme=='https' and u.hostname in PROFILE_HOSTS and not u.username and not u.password and not u.port and re.fullmatch(r'/LOGO/'+aid[:2]+'/'+aid+r'/(?:m/)?'+aid+r'\.(?:jpg|jpeg|png|webp|gif)',u.path,re.I) else ''

def fingerprint(config):return hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
def field(payload,path):
 for key in path.split('.'):
  if not isinstance(payload,dict):return None
  payload=payload.get(key)
 return payload

def check_provider(c):
 if not all(c.get(k) is True for k in ['enabled','policyReviewed','profileLinkingPermitted']):raise ValueError('SOOP 문서·권한·이미지 링크 이용 조건 확인 전입니다. 자동 조회를 활성화하지 않았습니다.')
 if not c.get('reviewReference') or not c.get('documentationUrl'):raise ValueError('이용 조건 검토 근거가 필요합니다.')
 if c.get('sourceType')!='station-profile':raise ValueError('방송국 프로필 소스만 허용합니다.')
 if not c.get('accountIdPath') or not c.get('profileImagePath'):raise ValueError('공식 응답의 계정/프로필 필드 설정이 필요합니다.')
 endpoint=c.get('endpointTemplate','')
 if endpoint.count('{accountId}')!=1:raise ValueError('엔드포인트에는 계정 ID 자리 하나가 필요합니다.')
 u=urlsplit(endpoint.replace('{accountId}','example'))
 if u.scheme!='https' or u.hostname not in API_HOSTS or u.username or u.password or u.port:raise ValueError('공식 Open API HTTPS 호스트만 허용합니다. 공개 웹 API를 임의로 사용하지 않습니다.')

def pilot_valid(proof,c,now=None):
 now=now or time.time()
 if proof.get('schema')!='wapobook-soop-profiles-v1' or proof.get('mode')!='pilot' or proof.get('configFingerprint')!=fingerprint(c):return False
 try:age=now-datetime.fromisoformat(proof['generatedAt']).timestamp()
 except (ValueError,KeyError):return False
 rows=proof.get('results',[])
 return 0<=age<7*86400 and len({r.get('accountId') for r in rows if r.get('status')=='success' and valid_image(r.get('imageUrl'),r.get('accountId',''))})>=5

class Resolver:
 def __init__(self,config,cache=None,request=None,sleep=time.sleep,clock=time.time):
  self.config=config;self.cache=cache if cache is not None else {};self.opener=build_opener(NoRedirect());self.request=request or self.opener.open;self.sleep=sleep;self.clock=clock;self.last=None;self.blocked=False
 def pace(self):
  interval=max(2,float(self.config.get('requestIntervalSeconds',2)))
  if self.last is not None:self.sleep(max(0,interval-(self.clock()-self.last)))
  self.last=self.clock()
 def fetch(self,url,headers=None,method='GET'):
  for attempt in range(3):
   self.pace()
   try:return self.request(Request(url,headers=headers or {},method=method),timeout=15)
   except HTTPError as e:
    if e.code in [401,403]:self.blocked=True;raise
    if e.code!=429 and e.code<500:raise
    if attempt==2:raise
    retry=e.headers.get('Retry-After','') if e.headers else ''
    self.sleep(min(60,max(2**(attempt+1),int(retry) if retry.isdigit() else 0)))
   except (URLError,TimeoutError):
    if attempt==2:raise
    self.sleep(2**(attempt+1))
 def resolve(self,aid):
  check_provider(self.config)
  key=fingerprint(self.config)+':'+aid;cached=self.cache.get(key)
  if cached and 0<=self.clock()-cached.get('timestamp',0)<min(24,float(self.config.get('cacheHours',24)))*3600:return dict(cached['result'],cached=True)
  result={'accountId':aid,'sourceType':'station-profile','status':'failed','imageUrl':''}
  if self.blocked:return dict(result,message='앞선 권한 오류로 추가 요청을 중단했습니다.')
  try:
   headers={'Accept':'application/json','User-Agent':'WapoBook-ProfileSync/1.0'}
   for name,setting in self.config.get('secretHeaders',{}).items():
    env=setting.get('env','');value=os.environ.get(env,'')
    if not value:raise ValueError('필요한 API 인증 설정이 없습니다.')
    headers[name]=setting.get('prefix','')+value
   url=self.config['endpointTemplate'].replace('{accountId}',aid)
   with self.fetch(url,headers) as r:
    body=r.read(2*1024*1024+1)
    if len(body)>2*1024*1024:raise ValueError('프로필 응답이 너무 큽니다.')
    payload=json.loads(body)
   if str(field(payload,self.config['accountIdPath']) or '').lower()!=aid:raise ValueError('응답 계정 ID가 요청과 다릅니다.')
   raw=field(payload,self.config['profileImagePath'])
   if not raw:result.update(status='no_image',message='공식 프로필 필드가 비어 있습니다.')
   else:
    image=valid_image(raw,aid)
    if not image:raise ValueError('확인된 방송국 프로필 경로가 아닙니다. 썸네일로 대체하지 않습니다.')
    # Only inspect headers. Do not download/rehost profile image files.
    with self.fetch(image,method='HEAD') as r:
     if not r.headers.get('Content-Type','').lower().startswith('image/'):raise ValueError('프로필 URL의 이미지 응답을 확인하지 못했습니다.')
    result.update(status='success',imageUrl=image,message='공식 응답의 프로필 URL 확인')
  except (HTTPError,URLError,TimeoutError):result.update(message='프로필 요청 실패 또는 접근 제한. 기본 이미지 유지.')
  except (ValueError,TypeError,KeyError):result.update(message='프로필 필드 또는 인증 설정을 검증하지 못했습니다. 기본 이미지 유지.')
  if result['status'] in ['success','no_image']:self.cache[key]={'timestamp':self.clock(),'result':result}
  return result

def run(requests,config,mode='pilot',cache=None,proof=None,resolver=None):
 if requests.get('schema')!='wapobook-soop-requests-v1' or not isinstance(requests.get('accounts'),list):raise ValueError('조회 요청 형식을 확인하세요.')
 rows=requests['accounts'];unique=list(dict.fromkeys(str(r.get('accountId','')).lower() for r in rows))
 if mode=='pilot' and len(unique)!=5:raise ValueError('시험 조회는 서로 다른 방송국 5개여야 합니다.')
 error=''
 try:
  check_provider(config)
  if mode=='batch' and not pilot_valid(proof or {},config):raise ValueError('같은 설정으로 7일 이내 성공한 5개 시험 결과가 필요합니다.')
 except ValueError as e:error=str(e)
 results=[];seen=set();resolver=resolver or Resolver(config,cache)
 for r in rows:
  aid=str(r.get('accountId','')).lower()
  if not ID.fullmatch(aid):result={'accountId':aid,'status':'failed','message':'잘못된 계정 ID'}
  elif aid in seen:result={'accountId':aid,'status':'duplicate','message':'중복 계정 요청 생략'}
  elif error:result={'accountId':aid,'status':'blocked','message':error}
  else:result=resolver.resolve(aid)
  seen.add(aid);results.append(result)
 return {'schema':'wapobook-soop-profiles-v1','mode':mode,'generatedAt':datetime.now(timezone.utc).isoformat(),'configFingerprint':fingerprint(config),'results':results}

def main():
 p=argparse.ArgumentParser();p.add_argument('--requests',required=True);p.add_argument('--config',default='sync/soop-provider.json');p.add_argument('--mode',choices=['pilot','batch'],default='pilot');p.add_argument('--pilot-proof');p.add_argument('--cache',default='.cache/soop-profiles.json');p.add_argument('--output',default='artifacts/soop-profiles.json');args=p.parse_args()
 cache_path=Path(args.cache);cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}
 report=run(json.loads(Path(args.requests).read_text()),json.loads(Path(args.config).read_text()),args.mode,cache,json.loads(Path(args.pilot_proof).read_text()) if args.pilot_proof else None)
 output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 cache_path.parent.mkdir(parents=True,exist_ok=True);cache_path.write_text(json.dumps(cache,ensure_ascii=False))
 counts={s:sum(r['status']==s for r in report['results']) for s in sorted({r['status'] for r in report['results']})};print(json.dumps(counts,ensure_ascii=False))
 if any(r['status']=='blocked' for r in report['results']):raise SystemExit(2)
if __name__=='__main__':main()
