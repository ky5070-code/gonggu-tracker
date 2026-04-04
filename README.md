# 🍼 육아 공구 모아보기

육아 인플루언서 공동구매 정보를 한눈에 모아보는 사이트입니다.

**[👉 사이트 바로가기](https://[깃허브아이디].github.io/[저장소이름])**

---

## 🚀 GitHub Pages 배포 방법

### 1단계 — 저장소 만들기
1. [github.com](https://github.com) 로그인
2. 오른쪽 상단 **+** → **New repository**
3. Repository name: `gonggu-tracker` (원하는 이름)
4. **Public** 선택 → **Create repository**

### 2단계 — 파일 업로드
저장소 페이지에서 **uploading an existing file** 클릭 후
이 폴더 안의 **모든 파일**을 드래그 업로드 (`.github` 폴더 포함)

> 💡 또는 터미널 사용:
> ```bash
> git init
> git add .
> git commit -m "첫 배포"
> git remote add origin https://github.com/[아이디]/gonggu-tracker.git
> git push -u origin main
> ```

### 3단계 — GitHub Pages 활성화
1. 저장소 → **Settings** 탭
2. 왼쪽 메뉴 **Pages**
3. Source: **Deploy from a branch**
4. Branch: **gh-pages** / **/ (root)** 선택
5. **Save**

> ⚠️ 처음 배포는 Actions가 한 번 실행된 뒤에 gh-pages 브랜치가 생겨요.
> Actions 탭 → **매일 공구 데이터 갱신 & 배포** → **Run workflow** 로 수동 실행!

### 4단계 — 완료!
`https://[깃허브아이디].github.io/gonggu-tracker` 주소로 접속 가능

---

## ⏰ 자동 업데이트

매일 **오전 8시 (한국시간)** GitHub Actions가 자동으로:
1. `build_site.py` 실행 → 새 공구 데이터 생성
2. `index.html` 업데이트
3. GitHub Pages에 자동 배포

수동으로 즉시 갱신하려면:
**Actions** 탭 → **매일 공구 데이터 갱신 & 배포** → **Run workflow**

---

## 📁 파일 구조

```
gonggu-tracker/
├── index.html          ← 메인 사이트 (자동 생성)
├── build_site.py       ← 데이터 빌드 스크립트
├── influencers.json    ← 인플루언서 목록
├── data/
│   └── latest.json     ← 최신 공구 데이터
└── .github/
    └── workflows/
        └── daily-deploy.yml  ← 자동 배포 설정
```
