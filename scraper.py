#!/usr/bin/env python3
"""
육아 아이템 공동구매 스크래퍼
- 인스타그램 프로필/포스트에서 공구 키워드 탐지
- 네이버 블로그에서 공구 게시글 수집
- 결과를 JSON으로 저장하고 HTML을 생성
"""

import json
import re
import os
import sys
import time
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urljoin

# === 설정 ===
BASE_DIR = Path(__file__).parent
INFLUENCERS_FILE = BASE_DIR / "influencers.json"
DATA_DIR = BASE_DIR / "data"
OUTPUT_HTML = BASE_DIR / "index.html"

# 공구 관련 키워드
GONGGU_KEYWORDS = [
    "공구", "공동구매", "공구오픈", "공구진행", "공구중",
    "공구마감", "공구링크", "단독특가", "특가", "할인",
    "오픈예정", "마감임박", "한정수량", "선착순", "최저가",
    "공구가", "육아템", "아기용품", "유아용품", "베이비",
    "신생아", "이유식", "젖병", "기저귀", "유모차",
    "카시트", "장난감", "놀이매트", "아기옷", "출산",
    "group buy", "deal", "sale"
]

# 카테고리 분류 키워드
CATEGORY_MAP = {
    "이유식/식품": ["이유식", "간식", "분유", "식품", "유기농", "쌀과자", "퓨레"],
    "기저귀/위생": ["기저귀", "물티슈", "세제", "살균", "소독", "위생"],
    "의류/패션": ["옷", "의류", "신발", "양말", "모자", "패션", "아기옷", "우주복"],
    "장난감/교구": ["장난감", "교구", "놀이", "블록", "퍼즐", "인형", "레고"],
    "가구/인테리어": ["가구", "침대", "매트", "놀이매트", "범퍼", "인테리어"],
    "외출용품": ["유모차", "카시트", "힙시트", "아기띠", "보행기", "웨건"],
    "수유/젖병": ["젖병", "수유", "쪽쪽이", "공갈", "유축기", "젖꼭지"],
    "스킨케어": ["로션", "크림", "오일", "스킨케어", "선크림", "보습"],
    "교육/도서": ["책", "도서", "교육", "학습", "영어", "한글", "수학"],
    "기타": []
}

def load_influencers():
    """인플루언서 목록 로드"""
    with open(INFLUENCERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["influencers"]

def classify_category(text):
    """텍스트에서 카테고리 분류"""
    text_lower = text.lower()
    for category, keywords in CATEGORY_MAP.items():
        if category == "기타":
            continue
        for kw in keywords:
            if kw in text_lower:
                return category
    return "기타"

def detect_gonggu_info(text):
    """텍스트에서 공구 정보 추출"""
    info = {
        "is_gonggu": False,
        "keywords_found": [],
        "price": None,
        "discount": None,
        "period": None,
        "product_name": None
    }

    text_lower = text.lower()

    # 공구 키워드 탐지
    for kw in GONGGU_KEYWORDS:
        if kw in text_lower:
            info["keywords_found"].append(kw)
            info["is_gonggu"] = True

    # 가격 추출
    price_patterns = [
        r'(\d{1,3}[,.]?\d{3,})\s*원',
        r'₩\s*(\d{1,3}[,.]?\d{3,})',
        r'(\d+)%\s*(할인|OFF|off|세일)',
    ]
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            info["price"] = match.group(0)
            break

    # 할인율 추출
    discount_match = re.search(r'(\d+)\s*%', text)
    if discount_match:
        info["discount"] = f"{discount_match.group(1)}%"

    # 기간 추출
    period_patterns = [
        r'(\d{1,2})[/.]\s*(\d{1,2})\s*[~\-]\s*(\d{1,2})[/.]\s*(\d{1,2})',
        r'(\d{1,2})월\s*(\d{1,2})일.*?[~\-까지].*?(\d{1,2})월?\s*(\d{1,2})일',
        r'(오늘|내일|금일)\s*(마감|까지|종료)',
    ]
    for pattern in period_patterns:
        match = re.search(pattern, text)
        if match:
            info["period"] = match.group(0)
            break

    return info

def scrape_naver_blog(blog_id):
    """네이버 블로그 RSS/API로 최근 글 수집"""
    import urllib.request

    results = []

    # 네이버 블로그 RSS 피드 사용
    rss_url = f"https://rss.blog.naver.com/{blog_id}.xml"

    try:
        req = urllib.request.Request(
            rss_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8", errors="ignore")

        # 간단한 XML 파싱 (xml.etree 사용)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(content)

        channel = root.find("channel")
        if channel is None:
            return results

        for item in channel.findall("item")[:10]:  # 최근 10개
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            desc = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")

            # HTML 태그 제거
            desc_clean = re.sub(r"<[^>]+>", "", desc)
            full_text = f"{title} {desc_clean}"

            gonggu_info = detect_gonggu_info(full_text)

            if gonggu_info["is_gonggu"]:
                results.append({
                    "title": title,
                    "link": link,
                    "description": desc_clean[:200],
                    "date": pub_date,
                    "gonggu_info": gonggu_info,
                    "category": classify_category(full_text)
                })

    except Exception as e:
        print(f"  [WARN] 네이버 블로그 {blog_id} 스크래핑 실패: {e}")

    return results

def scrape_instagram_profile(handle):
    """인스타그램 프로필 페이지에서 공구 정보 추출 (공개 API 대안)"""
    import urllib.request

    results = []

    # 인스타그램은 로그인 없이 접근이 제한적이므로
    # 프로필 페이지 메타데이터에서 기본 정보 추출 시도
    url = f"https://www.instagram.com/{handle}/"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ko-KR,ko;q=0.9"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8", errors="ignore")

        # 프로필 설명(bio)에서 공구 정보 탐지
        # og:description 메타 태그에서 bio 추출
        bio_match = re.search(r'<meta\s+(?:property|name)="(?:og:description|description)"\s+content="([^"]*)"', content)
        if bio_match:
            bio = bio_match.group(1)
            gonggu_info = detect_gonggu_info(bio)

            if gonggu_info["is_gonggu"]:
                results.append({
                    "title": f"@{handle} 프로필 공구 안내",
                    "link": url,
                    "description": bio[:200],
                    "date": datetime.now().isoformat(),
                    "gonggu_info": gonggu_info,
                    "category": classify_category(bio),
                    "source": "instagram_bio"
                })

        # 링크트리 등의 외부 링크 감지
        linktree_match = re.search(r'(linktr\.ee/[^\s"<]+|link\.inbio[^\s"<]+|lnk\.bio/[^\s"<]+)', content)
        if linktree_match:
            results.append({
                "title": f"@{handle} 공구 링크",
                "link": f"https://{linktree_match.group(1)}",
                "description": "외부 링크 (공구 상세정보 가능)",
                "date": datetime.now().isoformat(),
                "gonggu_info": {"is_gonggu": True, "keywords_found": ["링크"]},
                "category": "링크",
                "source": "instagram_link"
            })

    except Exception as e:
        print(f"  [WARN] 인스타그램 @{handle} 스크래핑 실패: {e}")

    return results

def scrape_naver_search(influencer_name):
    """네이버 검색으로 인플루언서의 공구 정보 추가 수집"""
    import urllib.request

    results = []
    query = quote(f"{influencer_name} 공동구매 공구")
    search_url = f"https://search.naver.com/search.naver?where=blog&query={query}&sm=tab_opt&nso=so%3Add%2Cp%3A1d"

    try:
        req = urllib.request.Request(
            search_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "ko-KR,ko;q=0.9"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8", errors="ignore")

        # 검색 결과에서 제목과 링크 추출
        titles = re.findall(r'class="api_txt_lines[^"]*"[^>]*>([^<]+)', content)
        links = re.findall(r'href="(https?://blog\.naver\.com/[^"]+)"', content)

        for i, (title, link) in enumerate(zip(titles[:5], links[:5])):
            title_clean = re.sub(r'<[^>]+>', '', title)
            gonggu_info = detect_gonggu_info(title_clean)

            if gonggu_info["is_gonggu"]:
                results.append({
                    "title": title_clean,
                    "link": link,
                    "description": f"{influencer_name}의 공구 관련 게시글",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "gonggu_info": gonggu_info,
                    "category": classify_category(title_clean),
                    "source": "naver_search"
                })

    except Exception as e:
        print(f"  [WARN] 네이버 검색 실패 ({influencer_name}): {e}")

    return results

def run_scraper():
    """메인 스크래핑 실행"""
    print(f"\n{'='*60}")
    print(f"🍼 육아 공동구매 스크래퍼 시작")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    influencers = load_influencers()
    print(f"📋 총 {len(influencers)}명의 인플루언서를 스크래핑합니다.\n")

    all_results = []
    stats = {"total": 0, "instagram": 0, "naver": 0, "search": 0, "errors": 0}

    for idx, inf in enumerate(influencers, 1):
        name = inf["name"]
        platform = inf["platform"]
        handle = inf["handle"]

        print(f"[{idx}/{len(influencers)}] {name} (@{handle}) - {platform}")

        try:
            posts = []

            if platform == "instagram":
                # 인스타그램 프로필 스크래핑
                posts = scrape_instagram_profile(handle)
                stats["instagram"] += len(posts)

                # 네이버 검색으로 보충
                search_posts = scrape_naver_search(name)
                posts.extend(search_posts)
                stats["search"] += len(search_posts)

            elif platform == "naver_blog":
                # 네이버 블로그 RSS
                posts = scrape_naver_blog(handle)
                stats["naver"] += len(posts)

                # 네이버 검색으로 보충
                search_posts = scrape_naver_search(name)
                posts.extend(search_posts)
                stats["search"] += len(search_posts)

            # 결과에 인플루언서 정보 추가
            for post in posts:
                post["influencer"] = {
                    "id": inf["id"],
                    "name": name,
                    "handle": handle,
                    "platform": platform,
                    "url": inf["url"],
                    "followers": inf["followers"],
                    "category": inf.get("category", "육아")
                }
                # 고유 ID 생성
                post["uid"] = hashlib.md5(
                    f"{handle}_{post['title']}_{post.get('link', '')}".encode()
                ).hexdigest()[:12]

            all_results.extend(posts)
            stats["total"] += len(posts)

            if posts:
                print(f"  ✅ {len(posts)}건의 공구 정보 발견")
            else:
                print(f"  ⬜ 공구 정보 없음")

        except Exception as e:
            print(f"  ❌ 오류: {e}")
            stats["errors"] += 1

        # 요청 간격 (서버 부하 방지)
        time.sleep(random.uniform(0.5, 1.5))

    # 중복 제거
    seen = set()
    unique_results = []
    for r in all_results:
        if r["uid"] not in seen:
            seen.add(r["uid"])
            unique_results.append(r)

    # 날짜순 정렬 (최신 먼저)
    unique_results.sort(key=lambda x: x.get("date", ""), reverse=True)

    # 결과 저장
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    output_data = {
        "scraped_at": datetime.now().isoformat(),
        "date": today,
        "stats": stats,
        "total_gonggu_found": len(unique_results),
        "results": unique_results
    }

    # 오늘 날짜 파일
    daily_file = DATA_DIR / f"gonggu_{today}.json"
    with open(daily_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # 최신 결과 파일 (HTML에서 참조)
    latest_file = DATA_DIR / "latest.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"📊 스크래핑 완료!")
    print(f"  총 공구 정보: {len(unique_results)}건")
    print(f"  인스타그램: {stats['instagram']}건")
    print(f"  네이버 블로그: {stats['naver']}건")
    print(f"  네이버 검색: {stats['search']}건")
    print(f"  오류: {stats['errors']}건")
    print(f"  저장: {daily_file}")
    print(f"{'='*60}\n")

    # HTML 생성
    generate_html(output_data)

    return output_data

def generate_sample_data():
    """데모용 샘플 데이터 생성 (스크래핑 없이 HTML 미리보기용)"""
    influencers = load_influencers()

    sample_products = [
        {"name": "오가닉 이유식 세트 (6개월+)", "price": "29,900원", "original": "45,000원", "discount": "33%", "cat": "이유식/식품"},
        {"name": "프리미엄 기저귀 팬티형 3팩", "price": "32,500원", "original": "48,000원", "discount": "32%", "cat": "기저귀/위생"},
        {"name": "실리콘 이유식 식기 세트", "price": "18,900원", "original": "28,000원", "discount": "32%", "cat": "이유식/식품"},
        {"name": "아기 보습 로션 300ml 2+1", "price": "15,900원", "original": "24,000원", "discount": "34%", "cat": "스킨케어"},
        {"name": "접이식 유아 놀이매트 XL", "price": "45,000원", "original": "69,000원", "discount": "35%", "cat": "가구/인테리어"},
        {"name": "유아용 웜수트 겨울 점프수트", "price": "35,900원", "original": "55,000원", "discount": "35%", "cat": "의류/패션"},
        {"name": "전동 코세척기 + 식염수 세트", "price": "22,500원", "original": "35,000원", "discount": "36%", "cat": "기저귀/위생"},
        {"name": "몬테소리 원목 교구 세트", "price": "42,000원", "original": "65,000원", "discount": "35%", "cat": "장난감/교구"},
        {"name": "360도 회전 유모차 경량형", "price": "189,000원", "original": "289,000원", "discount": "35%", "cat": "외출용품"},
        {"name": "PPSU 젖병 세트 (160ml+280ml)", "price": "28,900원", "original": "42,000원", "discount": "31%", "cat": "수유/젖병"},
        {"name": "아기 첫 영어 전집 30권", "price": "55,000원", "original": "89,000원", "discount": "38%", "cat": "교육/도서"},
        {"name": "유아 선크림 SPF50+ 무기자차", "price": "12,900원", "original": "19,800원", "discount": "35%", "cat": "스킨케어"},
        {"name": "아기띠 힙시트 올인원", "price": "65,000원", "original": "99,000원", "discount": "34%", "cat": "외출용품"},
        {"name": "이유식 마스터 블렌더", "price": "49,900원", "original": "79,000원", "discount": "37%", "cat": "이유식/식품"},
        {"name": "유아 실내화 논슬립 2켤레", "price": "14,500원", "original": "22,000원", "discount": "34%", "cat": "의류/패션"},
        {"name": "아기 수면조끼 겉싸개", "price": "25,900원", "original": "39,000원", "discount": "34%", "cat": "의류/패션"},
        {"name": "무소음 전동 유축기 듀얼", "price": "78,000원", "original": "120,000원", "discount": "35%", "cat": "수유/젖병"},
        {"name": "유아 비타민D 드롭스 3개월분", "price": "18,500원", "original": "28,000원", "discount": "34%", "cat": "이유식/식품"},
        {"name": "LED 밤등 수유등 터치", "price": "9,900원", "original": "15,000원", "discount": "34%", "cat": "가구/인테리어"},
        {"name": "아기 자석퍼즐 동물 세트", "price": "16,900원", "original": "25,000원", "discount": "32%", "cat": "장난감/교구"},
    ]

    results = []
    now = datetime.now()

    # 랜덤으로 인플루언서와 상품 매칭
    random.seed(42)  # 재현 가능하도록
    used_combos = set()

    for i in range(min(40, len(influencers))):
        inf = influencers[i]
        # 각 인플루언서당 1~3개 공구
        num_products = random.randint(1, 3)
        products = random.sample(sample_products, min(num_products, len(sample_products)))

        for prod in products:
            combo = f"{inf['handle']}_{prod['name']}"
            if combo in used_combos:
                continue
            used_combos.add(combo)

            days_ago = random.randint(0, 2)
            post_date = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            end_date = (now + timedelta(days=random.randint(1, 7))).strftime("%m/%d")

            status = random.choice(["진행중", "진행중", "진행중", "오늘마감", "곧오픈"])

            results.append({
                "uid": hashlib.md5(combo.encode()).hexdigest()[:12],
                "title": f"[공구] {prod['name']}",
                "link": inf["url"],
                "description": f"{prod['name']} - 공구가 {prod['price']} (정가 {prod['original']}, {prod['discount']} 할인)",
                "date": post_date,
                "gonggu_info": {
                    "is_gonggu": True,
                    "keywords_found": ["공구", "특가"],
                    "price": prod["price"],
                    "discount": prod["discount"],
                    "period": f"~{end_date}",
                    "product_name": prod["name"],
                    "original_price": prod["original"],
                    "status": status
                },
                "category": prod["cat"],
                "influencer": {
                    "id": inf["id"],
                    "name": inf["name"],
                    "handle": inf["handle"],
                    "platform": inf["platform"],
                    "url": inf["url"],
                    "followers": inf["followers"],
                    "category": inf.get("category", "육아")
                }
            })

    output_data = {
        "scraped_at": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "stats": {"total": len(results), "instagram": 25, "naver": 10, "search": 5, "errors": 0},
        "total_gonggu_found": len(results),
        "results": results
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    latest_file = DATA_DIR / "latest.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    return output_data

def generate_html(data=None):
    """공구 정보를 표시하는 HTML 페이지 생성"""

    if data is None:
        latest_file = DATA_DIR / "latest.json"
        if latest_file.exists():
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = generate_sample_data()

    results = data.get("results", [])
    scraped_at = data.get("scraped_at", "")
    stats = data.get("stats", {})

    # 카테고리별 분류
    categories = {}
    for r in results:
        cat = r.get("category", "기타")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    # 카테고리 카운트 JSON
    cat_counts = {k: len(v) for k, v in sorted(categories.items(), key=lambda x: -len(x[1]))}

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>육아 공구 모아보기 | Baby Deal Tracker</title>
    <style>
        :root {{
            --primary: #FF6B6B;
            --primary-light: #FFE3E3;
            --secondary: #4ECDC4;
            --secondary-light: #E0FAF7;
            --accent: #FFE66D;
            --dark: #2C3E50;
            --gray: #95A5A6;
            --light: #F8F9FA;
            --white: #FFFFFF;
            --shadow: 0 2px 12px rgba(0,0,0,0.08);
            --shadow-hover: 0 8px 25px rgba(0,0,0,0.12);
            --radius: 16px;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
            background: var(--light);
            color: var(--dark);
            line-height: 1.6;
        }}

        /* 헤더 */
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, #FF8E8E 100%);
            color: white;
            padding: 2rem 1.5rem;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 4px 20px rgba(255,107,107,0.3);
        }}

        .header h1 {{
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }}

        .header .subtitle {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}

        .header .update-time {{
            font-size: 0.75rem;
            opacity: 0.7;
            margin-top: 0.5rem;
        }}

        /* 통계 바 */
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            padding: 1rem 1.5rem;
            background: white;
            border-bottom: 1px solid #eee;
            flex-wrap: wrap;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-item .number {{
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--primary);
        }}

        .stat-item .label {{
            font-size: 0.7rem;
            color: var(--gray);
            text-transform: uppercase;
        }}

        /* 검색 & 필터 */
        .search-section {{
            padding: 1rem 1.5rem;
            background: white;
            border-bottom: 1px solid #eee;
        }}

        .search-box {{
            display: flex;
            gap: 0.5rem;
            max-width: 600px;
            margin: 0 auto;
        }}

        .search-box input {{
            flex: 1;
            padding: 0.75rem 1rem;
            border: 2px solid #eee;
            border-radius: 12px;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }}

        .search-box input:focus {{
            border-color: var(--primary);
        }}

        /* 카테고리 필터 */
        .filter-section {{
            padding: 0.75rem 1.5rem;
            overflow-x: auto;
            white-space: nowrap;
            background: white;
            border-bottom: 1px solid #eee;
            -webkit-overflow-scrolling: touch;
        }}

        .filter-section::-webkit-scrollbar {{
            display: none;
        }}

        .filter-chip {{
            display: inline-block;
            padding: 0.4rem 1rem;
            margin: 0 0.3rem;
            border-radius: 20px;
            font-size: 0.82rem;
            cursor: pointer;
            border: 1.5px solid #ddd;
            background: white;
            color: var(--dark);
            transition: all 0.2s;
            font-weight: 500;
        }}

        .filter-chip:hover {{
            border-color: var(--primary);
            color: var(--primary);
        }}

        .filter-chip.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}

        .filter-chip .count {{
            font-size: 0.7rem;
            opacity: 0.7;
            margin-left: 2px;
        }}

        /* 정렬 */
        .sort-section {{
            padding: 0.5rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .sort-section .result-count {{
            font-size: 0.85rem;
            color: var(--gray);
        }}

        .sort-select {{
            padding: 0.4rem 0.8rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 0.82rem;
            outline: none;
            background: white;
        }}

        /* 카드 그리드 */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0.5rem 1rem 2rem;
        }}

        .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1rem;
        }}

        /* 카드 */
        .card {{
            background: white;
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }}

        .card:hover {{
            box-shadow: var(--shadow-hover);
            transform: translateY(-2px);
        }}

        .card-header {{
            padding: 1rem 1.2rem 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}

        .influencer-info {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }}

        .avatar {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 700;
            color: white;
            flex-shrink: 0;
        }}

        .avatar.instagram {{
            background: linear-gradient(135deg, #833AB4, #FD1D1D, #FCB045);
        }}

        .avatar.naver {{
            background: linear-gradient(135deg, #03C75A, #2DB400);
        }}

        .influencer-name {{
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--dark);
        }}

        .influencer-handle {{
            font-size: 0.72rem;
            color: var(--gray);
        }}

        .status-badge {{
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 700;
            white-space: nowrap;
        }}

        .status-badge.active {{
            background: #E8F5E9;
            color: #2E7D32;
        }}

        .status-badge.ending {{
            background: #FFF3E0;
            color: #E65100;
            animation: pulse 2s infinite;
        }}

        .status-badge.upcoming {{
            background: #E3F2FD;
            color: #1565C0;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}

        .card-body {{
            padding: 0.5rem 1.2rem 1rem;
        }}

        .product-name {{
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
            color: var(--dark);
            line-height: 1.4;
        }}

        .price-row {{
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
            margin-bottom: 0.4rem;
        }}

        .price {{
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--primary);
        }}

        .original-price {{
            font-size: 0.82rem;
            color: var(--gray);
            text-decoration: line-through;
        }}

        .discount-badge {{
            background: var(--primary);
            color: white;
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
        }}

        .card-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.6rem 1.2rem;
            border-top: 1px solid #f0f0f0;
            font-size: 0.75rem;
            color: var(--gray);
        }}

        .category-tag {{
            background: var(--secondary-light);
            color: #00897B;
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 600;
        }}

        /* 플랫폼 아이콘 필터 */
        .platform-filters {{
            display: flex;
            gap: 0.5rem;
            padding: 0 1.5rem 0.5rem;
        }}

        .platform-btn {{
            padding: 0.3rem 0.8rem;
            border-radius: 8px;
            font-size: 0.8rem;
            cursor: pointer;
            border: none;
            background: #f0f0f0;
            color: var(--dark);
            font-weight: 600;
            transition: all 0.2s;
        }}

        .platform-btn.active {{
            background: var(--dark);
            color: white;
        }}

        /* 빈 상태 */
        .empty-state {{
            text-align: center;
            padding: 3rem 1.5rem;
            color: var(--gray);
        }}

        .empty-state .emoji {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}

        /* 모달 */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 200;
            justify-content: center;
            align-items: center;
            padding: 1rem;
        }}

        .modal-overlay.show {{
            display: flex;
        }}

        .modal {{
            background: white;
            border-radius: var(--radius);
            max-width: 500px;
            width: 100%;
            max-height: 80vh;
            overflow-y: auto;
            padding: 1.5rem;
        }}

        .modal h3 {{
            margin-bottom: 1rem;
        }}

        .modal-close {{
            float: right;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--gray);
        }}

        /* 반응형 */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.4rem;
            }}

            .card-grid {{
                grid-template-columns: 1fr;
            }}

            .stats-bar {{
                gap: 1rem;
            }}
        }}

        /* 로딩 */
        .loading {{
            text-align: center;
            padding: 2rem;
        }}

        .loading .spinner {{
            width: 40px;
            height: 40px;
            border: 4px solid #f0f0f0;
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 1rem;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        /* 푸터 */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--gray);
            font-size: 0.8rem;
        }}

        .footer a {{
            color: var(--primary);
            text-decoration: none;
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>🍼 육아 공구 모아보기</h1>
    <p class="subtitle">인기 육아 인플루언서들의 공동구매를 한눈에</p>
    <p class="update-time" id="updateTime">마지막 업데이트: 로딩중...</p>
</div>

<div class="stats-bar" id="statsBar">
    <div class="stat-item">
        <div class="number" id="statTotal">-</div>
        <div class="label">총 공구</div>
    </div>
    <div class="stat-item">
        <div class="number" id="statInfluencer">-</div>
        <div class="label">인플루언서</div>
    </div>
    <div class="stat-item">
        <div class="number" id="statActive">-</div>
        <div class="label">진행중</div>
    </div>
    <div class="stat-item">
        <div class="number" id="statEnding">-</div>
        <div class="label">마감임박</div>
    </div>
</div>

<div class="search-section">
    <div class="search-box">
        <input type="text" id="searchInput" placeholder="상품명, 인플루언서 검색..." oninput="filterResults()">
    </div>
</div>

<div class="filter-section" id="filterSection">
    <span class="filter-chip active" data-category="all" onclick="setCategory('all')">전체</span>
</div>

<div class="sort-section">
    <span class="result-count" id="resultCount">0건</span>
    <select class="sort-select" id="sortSelect" onchange="sortResults()">
        <option value="latest">최신순</option>
        <option value="discount">할인율순</option>
        <option value="price_low">가격 낮은순</option>
        <option value="price_high">가격 높은순</option>
        <option value="ending">마감임박순</option>
    </select>
</div>

<div class="container">
    <div class="card-grid" id="cardGrid">
        <div class="loading">
            <div class="spinner"></div>
            <p>공구 정보를 불러오는 중...</p>
        </div>
    </div>
</div>

<div class="footer">
    <p>매일 오전 8시 자동 업데이트 · 총 100명 인플루언서 모니터링</p>
    <p style="margin-top:0.3rem;">문의: 육아 공구 모아보기</p>
</div>

<!-- 상세 모달 -->
<div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
    <div class="modal" id="modalContent">
    </div>
</div>

<script>
// === 데이터 ===
const GONGGU_DATA = {json.dumps(results, ensure_ascii=False)};

let filteredData = [...GONGGU_DATA];
let currentCategory = 'all';
let currentPlatform = 'all';

// === 초기화 ===
function init() {{
    updateStats();
    buildCategoryFilters();
    renderCards(GONGGU_DATA);

    const scraped = "{scraped_at}";
    if (scraped) {{
        const d = new Date(scraped);
        document.getElementById('updateTime').textContent =
            `마지막 업데이트: ${{d.getFullYear()}}년 ${{d.getMonth()+1}}월 ${{d.getDate()}}일 ${{String(d.getHours()).padStart(2,'0')}}:${{String(d.getMinutes()).padStart(2,'0')}}`;
    }}
}}

function updateStats() {{
    document.getElementById('statTotal').textContent = GONGGU_DATA.length;

    const influencers = new Set(GONGGU_DATA.map(d => d.influencer?.handle)).size;
    document.getElementById('statInfluencer').textContent = influencers;

    const active = GONGGU_DATA.filter(d =>
        d.gonggu_info?.status === '진행중' || d.gonggu_info?.status === '오늘마감'
    ).length;
    document.getElementById('statActive').textContent = active;

    const ending = GONGGU_DATA.filter(d =>
        d.gonggu_info?.status === '오늘마감'
    ).length;
    document.getElementById('statEnding').textContent = ending;
}}

function buildCategoryFilters() {{
    const cats = {{}};
    GONGGU_DATA.forEach(d => {{
        const c = d.category || '기타';
        cats[c] = (cats[c] || 0) + 1;
    }});

    const section = document.getElementById('filterSection');
    const allChip = section.querySelector('.filter-chip');
    allChip.innerHTML = `전체 <span class="count">${{GONGGU_DATA.length}}</span>`;

    Object.entries(cats)
        .sort((a,b) => b[1] - a[1])
        .forEach(([cat, count]) => {{
            const chip = document.createElement('span');
            chip.className = 'filter-chip';
            chip.dataset.category = cat;
            chip.innerHTML = `${{cat}} <span class="count">${{count}}</span>`;
            chip.onclick = () => setCategory(cat);
            section.appendChild(chip);
        }});
}}

function setCategory(cat) {{
    currentCategory = cat;
    document.querySelectorAll('.filter-chip').forEach(c => {{
        c.classList.toggle('active', c.dataset.category === cat);
    }});
    filterResults();
}}

function filterResults() {{
    const query = document.getElementById('searchInput').value.toLowerCase();

    filteredData = GONGGU_DATA.filter(d => {{
        // 카테고리 필터
        if (currentCategory !== 'all' && d.category !== currentCategory) return false;

        // 검색어 필터
        if (query) {{
            const text = `${{d.title}} ${{d.description}} ${{d.influencer?.name}} ${{d.influencer?.handle}} ${{d.gonggu_info?.product_name || ''}}`.toLowerCase();
            if (!text.includes(query)) return false;
        }}

        return true;
    }});

    sortResults();
}}

function sortResults() {{
    const sort = document.getElementById('sortSelect').value;

    filteredData.sort((a, b) => {{
        switch(sort) {{
            case 'latest':
                return (b.date || '').localeCompare(a.date || '');
            case 'discount':
                const dA = parseInt(a.gonggu_info?.discount) || 0;
                const dB = parseInt(b.gonggu_info?.discount) || 0;
                return dB - dA;
            case 'price_low':
                const pA = parseInt((a.gonggu_info?.price || '0').replace(/[^0-9]/g, ''));
                const pB = parseInt((b.gonggu_info?.price || '0').replace(/[^0-9]/g, ''));
                return pA - pB;
            case 'price_high':
                const phA = parseInt((a.gonggu_info?.price || '0').replace(/[^0-9]/g, ''));
                const phB = parseInt((b.gonggu_info?.price || '0').replace(/[^0-9]/g, ''));
                return phB - phA;
            case 'ending':
                const sOrder = {{'오늘마감': 0, '곧오픈': 1, '진행중': 2}};
                return (sOrder[a.gonggu_info?.status] ?? 3) - (sOrder[b.gonggu_info?.status] ?? 3);
            default:
                return 0;
        }}
    }});

    renderCards(filteredData);
}}

function renderCards(data) {{
    const grid = document.getElementById('cardGrid');
    document.getElementById('resultCount').textContent = `${{data.length}}건`;

    if (data.length === 0) {{
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <div class="emoji">🔍</div>
                <p>검색 결과가 없습니다</p>
            </div>
        `;
        return;
    }}

    grid.innerHTML = data.map(d => {{
        const inf = d.influencer || {{}};
        const gi = d.gonggu_info || {{}};
        const platform = inf.platform || 'instagram';
        const initial = (inf.name || '?')[0];

        let statusClass = 'active';
        let statusText = gi.status || '진행중';
        if (statusText === '오늘마감') statusClass = 'ending';
        if (statusText === '곧오픈') statusClass = 'upcoming';

        const price = gi.price || '';
        const originalPrice = gi.original_price || '';
        const discount = gi.discount || '';
        const period = gi.period || '';

        return `
            <div class="card" onclick="openDetail('${{d.uid}}')">
                <div class="card-header">
                    <div class="influencer-info">
                        <div class="avatar ${{platform}}">${{initial}}</div>
                        <div>
                            <div class="influencer-name">${{inf.name || ''}}</div>
                            <div class="influencer-handle">@${{inf.handle || ''}} · ${{inf.followers || ''}}</div>
                        </div>
                    </div>
                    <span class="status-badge ${{statusClass}}">${{statusText}}</span>
                </div>
                <div class="card-body">
                    <div class="product-name">${{gi.product_name || d.title || ''}}</div>
                    <div class="price-row">
                        ${{price ? `<span class="price">${{price}}</span>` : ''}}
                        ${{originalPrice ? `<span class="original-price">${{originalPrice}}</span>` : ''}}
                        ${{discount ? `<span class="discount-badge">${{discount}} OFF</span>` : ''}}
                    </div>
                </div>
                <div class="card-meta">
                    <span class="category-tag">${{d.category || '기타'}}</span>
                    <span>${{period ? `${{period}} 까지` : d.date || ''}}</span>
                </div>
            </div>
        `;
    }}).join('');
}}

function openDetail(uid) {{
    const item = GONGGU_DATA.find(d => d.uid === uid);
    if (!item) return;

    const inf = item.influencer || {{}};
    const gi = item.gonggu_info || {{}};
    const platform = inf.platform === 'naver_blog' ? '네이버 블로그' : '인스타그램';

    document.getElementById('modalContent').innerHTML = `
        <button class="modal-close" onclick="closeModal()">&times;</button>
        <h3>${{gi.product_name || item.title}}</h3>
        <p style="margin-bottom:1rem;color:var(--gray);font-size:0.9rem;">${{item.description || ''}}</p>

        <div style="background:var(--light);padding:1rem;border-radius:12px;margin-bottom:1rem;">
            <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
                <span>공구가</span>
                <strong style="color:var(--primary);font-size:1.1rem;">${{gi.price || '-'}}</strong>
            </div>
            ${{gi.original_price ? `
            <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
                <span>정가</span>
                <span style="text-decoration:line-through;color:var(--gray);">${{gi.original_price}}</span>
            </div>` : ''}}
            ${{gi.discount ? `
            <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
                <span>할인율</span>
                <strong style="color:var(--primary);">${{gi.discount}}</strong>
            </div>` : ''}}
            ${{gi.period ? `
            <div style="display:flex;justify-content:space-between;">
                <span>기간</span>
                <span>${{gi.period}}</span>
            </div>` : ''}}
        </div>

        <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:1rem;padding:0.8rem;background:#f8f8f8;border-radius:12px;">
            <div class="avatar ${{inf.platform || 'instagram'}}" style="width:40px;height:40px;">${{(inf.name||'?')[0]}}</div>
            <div>
                <div style="font-weight:700;">${{inf.name || ''}}</div>
                <div style="font-size:0.8rem;color:var(--gray);">@${{inf.handle || ''}} · ${{platform}} · ${{inf.followers || ''}}</div>
            </div>
        </div>

        <a href="${{item.link || inf.url || '#'}}" target="_blank" rel="noopener"
           style="display:block;text-align:center;background:var(--primary);color:white;padding:0.8rem;border-radius:12px;text-decoration:none;font-weight:700;font-size:0.95rem;">
            공구 페이지로 이동 →
        </a>
    `;

    document.getElementById('modalOverlay').classList.add('show');
}}

function closeModal(e) {{
    if (!e || e.target === e.currentTarget) {{
        document.getElementById('modalOverlay').classList.remove('show');
    }}
}}

// 키보드 ESC로 모달 닫기
document.addEventListener('keydown', e => {{
    if (e.key === 'Escape') closeModal();
}});

// 초기화 실행
init();
</script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML 생성 완료: {OUTPUT_HTML}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("🎨 데모 모드: 샘플 데이터로 HTML 생성")
        data = generate_sample_data()
        generate_html(data)
    else:
        run_scraper()
