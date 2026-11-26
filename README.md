# ParkAce IPA Store

`parkace-ipa/my-ios-source`용 한국어 IPA 소스 관리 도구입니다. 저장소: https://github.com/parkace-ipa/my-ios-source · 사이트: https://parkace-ipa.github.io/my-ios-source/

배포 결과는 저장소 Actions의 최신 실행에서 확인하세요.

## 최초 파일 준비 시 확인 결과 (2026-11-25 KST)

- NightFox `https://nightfox-proxy.kes158.workers.dev/source`: 실제 요청 HTTP 403. 설정에 후보로만 등록했으며 앱은 임의로 추가하지 않았습니다. 접근이 허용되면 목록 조회 및 선택이 가능합니다. 우회·인증을 제공하지 않습니다.
- GitHub 공개 API의 `parkace-ipa/my-ios-source`: HTTP 404. 저장소 부재 또는 비공개일 수 있습니다.
- 최초 준비 시 인증이 없었으나 이후 `parkace-ipa` GitHub CLI 로그인을 확인하여 공개 저장소와 Pages 설정을 생성했습니다.

## 완성된 기능

- 한국어 반응형 페이지, 외부 소스 추가·삭제·앱 선택, 선택 앱별 자동 갱신 켜기/끄기
- 공개 IPA URL 직접 등록, 로컬 IPA의 XML/바이너리 Info.plist 분석, GitHub Releases 업로드
- 일반 PNG 아이콘 자동 추출. Assets.car·CgBI만 있는 경우 기본 아이콘 사용 및 아이콘 URL 수동 지정
- Bundle ID 중복 처리: 직접 등록 우선, 이후 설정 소스 순서 우선
- 외부 소스 실패·앱 누락·잘못된 버전 데이터는 마지막 정상 데이터 유지. 선택 해제는 제거
- 수동 갱신, 매일 KST 06:00 예약, 변경 이력 커밋, Actions를 통한 Pages 배포

## 처음 배포하기 — Mac 터미널

Python 3와 Git이 필요합니다. GitHub CLI는 https://cli.github.com/ 안내로 설치하세요 (Homebrew가 있다면 `brew install gh`). 비밀번호·토큰을 채팅이나 저장소에 넣지 마세요.

1. 압축을 풀고 **my-ios-source 폴더 안에서** 터미널을 엽니다.
2. 본인 브라우저로 GitHub에 로그인합니다.

```bash
gh auth login --hostname github.com --git-protocol https --web
gh api user --jq .login
```

출력이 `parkace-ipa`인지 확인하세요. 다르면 `gh auth switch --hostname github.com --user parkace-ipa`로 전환합니다.

3. GitHub에서 기존 `my-ios-source` 저장소가 있는지 확인합니다. **아래 초기화 명령은 새 저장소용입니다.** 기존 저장소가 있다면 먼저 `gh repo clone parkace-ipa/my-ios-source`로 별도 폴더에 내려받고 변경 사항을 검토하며 이 파일들을 복사하세요. 강제 덮어쓰기나 강제 push를 하지 마세요.

새 저장소라면:

```bash
git init -b main
git add .
git commit -m "Create Korean IPA source manager"
gh repo create parkace-ipa/my-ios-source --public --source=. --remote=origin --push
```

커밋 시 이름·이메일 설정을 요구하면 본인의 Git 작성자 정보를 설정하고 다시 커밋합니다. 인증 비밀번호가 아닙니다.

4. `https://github.com/parkace-ipa/my-ios-source/settings/pages`에서 **Build and deployment → Source → GitHub Actions**를 선택합니다. Actions 사용과 워크플로의 쓰기 권한이 조직/계정 정책으로 차단되어 있다면 해당 정책 허용이 필요합니다.
5. Actions에서 **Update and publish IPA source → Run workflow → main → Run workflow**를 실행합니다. 두 작업(build/deploy)이 모두 성공했는지 확인합니다.
6. 아래 주소에서 응답을 확인합니다. 이는 **배포 후 사용할 예정 주소**이며 파일을 받은 것만으로 활성화되지 않습니다.

- 관리/공개 페이지: https://parkace-ipa.github.io/my-ios-source/
- 기본 소스: https://parkace-ipa.github.io/my-ios-source/source.json
- 엄격한 SideStore 구형 스키마용: https://parkace-ipa.github.io/my-ios-source/sidestore.json

## 평소 사용법

```bash
python3 scripts/manage.py
```

`http://127.0.0.1:8765`를 직접 엽니다. Mac에서는 `관리화면.command`를 실행해도 됩니다. 종료는 터미널에서 Ctrl+C입니다.

1. 외부 소스를 추가 → 앱 목록 조회 → 원하는 앱 체크 → **설정 저장 및 갱신**.
2. 직접 IPA 주소는 필수 메타데이터를 입력해 등록합니다. URL만으로 IPA 내용을 자동 다운로드/분석하지 않으며, 로컬 파일 업로드 시에는 내용을 분석합니다.
3. IPA 파일을 선택해 **선택 파일 업로드**하면 로컬 `gh` 인증으로 공개 Release에 업로드합니다. 실패하면 초안 Release가 남을 수 있으므로 GitHub Releases에서 확인하세요. 성공 후 앱 설정 저장이 필요합니다. 업로드한 파일은 앱 등록을 삭제해도 자동 삭제되지 않습니다.
4. **저장은 내 컴퓨터 파일에만 적용됩니다.** 공개 사이트에 반영하려면:

```bash
git add config.json source.json sidestore.json state.json status.json
git commit -m "Update IPA selections"
git pull --rebase origin main
git push origin main
```

충돌이 나면 GitHub의 자동 갱신 데이터와 본인 설정을 비교해 해결해야 합니다. 강제 push하지 마세요. 자동 생성 파일은 `config.json` 선택이 맞는지 확인한 후 `python3 scripts/core.py`로 다시 만들 수 있습니다.

공개 Pages에는 앱 목록과 IPA 다운로드만 표시됩니다. 관리 HTML·스크립트·config.json·status.json은 Pages 배포 파일에서 제외됩니다. 외부 소스 선택과 설정 저장·업로드는 로컬 관리 화면에서 진행하세요. 로컬 조회도 원본의 403·로그인·IP 차단을 해결하지는 못합니다.

## 공개 접근과 인증의 실제 범위

GitHub Pages는 정적 페이지입니다. 이 프로젝트에 GitHub 로그인 서버나 OAuth 앱이 포함된 것은 아닙니다. 공개 페이지에서 계정 쓰기 권한을 얻거나 Releases에 직접 업로드할 수 없습니다. 관리자 비밀을 브라우저에 심거나 공개 페이지의 버튼 숨김으로 보호하지 않습니다.

로컬 관리 서버는 127.0.0.1에만 연결되고 Host·Origin·세션별 요청 키를 확인합니다. GitHub 권한은 로컬 `gh` 인증 저장소에서 관리합니다. GitHub 토큰을 HTML·localStorage·설정·소스 JSON에 저장하지 않습니다. 이 로컬 도구는 같은 컴퓨터 사용자에게 신뢰를 두므로 공용 컴퓨터에서 실행하지 마세요.

무료 공개 저장소를 기준으로 구성했습니다. 사이트, 설정의 외부 소스 주소와 선택 목록, 앱 메타데이터, Actions 로그, Releases IPA 파일은 누구나 볼 수 있습니다. `state.json`은 Pages 배포에서 제외되지만 공개 저장소에서는 열람 가능합니다. 비공개 IPA를 이 방식으로 보호할 수 없습니다. 로그인·쿠키·만료 링크가 필요한 다운로드는 일반 SideStore/LiveContainer 클라이언트에서 작동하지 않을 수 있습니다. 배포 권한이 있는 파일을 사용하세요.

사이트에서 파일을 내려받는 것과 iPhone 설치/서명은 별개입니다. SideStore/LiveContainer 기기에서 실제 설치 테스트는 수행하지 않았습니다. AltStore PAL의 ADP/공증 배포는 이 프로젝트의 IPA 소스 대상이 아닙니다.

## 자동화와 형식

- `.github/workflows/publish.yml`: cron `0 21 * * *` = 매일 KST 06:00. GitHub 예약 작업은 지연되거나 생략될 수 있으며 정확한 시각 보장은 없습니다. 기본 브랜치에 워크플로가 있어야 합니다. 공개 저장소의 장기 비활동 시 예약 실행이 비활성화될 수 있습니다.
- push·수동 실행·예약 실행 모두 갱신 후 같은 워크플로에서 Pages를 배포합니다. 봇 커밋이 새 워크플로를 트리거하지 않아도 배포됩니다.
- 최신 AltStore 공식 문서의 `versions` 배열을 사용하고 원본 순서를 보존합니다. `version`과 `buildVersion`을 보존하며 index 0을 최신 호환 버전으로 사용합니다. 원본이 예전 최상위 version 필드를 사용하면 배열로 변환합니다.
- `source.json`은 현대 AltStore 필드(`buildVersion`, 명시된 `appPermissions`)를 보존합니다. SideStore 공개 JSON Schema는 이 필드들을 허용하지 않아 `sidestore.json`에서는 제거합니다. 이 구형 호환 파일은 같은 version 내 buildVersion만 바뀌는 업데이트 구분에 한계가 있습니다. 원본 권한·스크린샷 전체의 완전한 변환은 지원하지 않습니다.
- 스키마 사본: `vendor/sidestore.schema.json` (2026-11-25 다운로드). SideStore 형식은 전체 JSON Schema 검증 테스트를 수행합니다. AltStore/LiveContainer 실제 기기 호환 보장은 아닙니다.
- 직접 URL의 실제 다운로드 가능 여부·서명·IPA 내부 값은 자동 검증하지 않습니다. 입력 값의 형식과 필수 항목을 확인합니다.

공식 근거:
- https://faq.altstore.io/developers/make-a-source
- https://faq.altstore.io/developers/updating-apps
- https://github.com/SideStore/sidestore-source-types/blob/main/schema.json
- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

## 검증 및 빌드

운영 도구는 Python 표준 라이브러리만 사용합니다. 테스트에는 jsonschema가 필요합니다.

```bash
python3 -m pip install -r requirements-test.txt
python3 -m unittest discover -s tests -v
python3 scripts/core.py
python3 scripts/build.py
```

`dist/`가 Pages 배포용 결과입니다. GitHub 설정의 Pages 소스는 GitHub Actions여야 합니다. 빈 앱 목록은 초기 상태로 의도한 것입니다. NightFox는 403 때문에 앱을 선택하지 않았습니다.

## 검색 노출 억제

공개 HTML 페이지에는 `noindex, nofollow`를 적용했습니다. 이를 준수하는 검색엔진이 페이지를 수집하면 검색 결과에서 제외합니다. 기존 검색 결과의 제거는 즉시 처리되지 않을 수 있습니다. 검색엔진이 noindex를 읽을 수 있도록 robots.txt로 크롤링을 막지 않습니다.

GitHub Pages에서는 이 프로젝트가 임의의 HTTP 응답 헤더를 설정할 수 없으므로 JSON·IPA 파일에 X-Robots-Tag를 적용하지 못합니다. 공개 GitHub 저장소와 Releases도 별도로 발견될 수 있습니다. 이는 링크 공유를 위한 검색 노출 억제이며, 완전한 검색 차단이나 접근 인증을 보장하지 않습니다.

## 공개 화면과 관리 화면 분리

`web/`은 공개 앱 목록·다운로드 화면, `admin/`은 로컬 관리 화면입니다. 관리 서버는 로컬 전용 파일을 직접 제공하며 공개 빌드에는 포함하지 않습니다. 공개 GitHub 저장소의 소스 코드와 설정 파일은 여전히 열람 가능합니다.

## 관리 화면에서 바로 배포

앱 선택·등록 후 **저장하고 공개 배포**를 누르면 설정 저장, 갱신, GitHub 커밋·업로드와 배포 결과 확인을 진행합니다. 기존 **설정 저장 및 갱신**은 내 Mac에만 저장합니다. 배포 중에는 편집을 잠시 잠급니다. 충돌 시 강제로 덮어쓰지 않으며 설정은 로컬 커밋에 보관합니다. 결과 확인이 지연되면 **배포 진행 보기**에서 확인하세요.
