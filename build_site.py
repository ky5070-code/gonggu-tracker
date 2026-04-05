#!/usr/bin/env python3
"""
육아 공동구매 모아보기 - 사이트 빌더
실제 인플루언서 + 실제 브랜드 기반 데이터 생성 및 HTML 빌드
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────
# 실제 확인된 인플루언서 목록 (Instagram + Naver Blog)
# ──────────────────────────────────────────
INFLUENCERS = [
    # === 인스타그램 ===
    {"id":1,  "name":"우니동동",       "handle":"unidongdong",      "platform":"instagram","followers":"239K","url":"https://instagram.com/unidongdong",     "category":"육아/재테크"},
    {"id":2,  "name":"소을맘",         "handle":"zzu_ni",           "platform":"instagram","followers":"136K","url":"https://instagram.com/zzu_ni",           "category":"육아/라이프"},
    {"id":3,  "name":"제시맘",         "handle":"likejinseo",       "platform":"instagram","followers":"80K", "url":"https://instagram.com/likejinseo",       "category":"육아"},
    {"id":4,  "name":"일리맘",         "handle":"ily__diary",       "platform":"instagram","followers":"70K", "url":"https://instagram.com/ily__diary",       "category":"육아/일상"},
    {"id":5,  "name":"showme공구",     "handle":"showme_09",        "platform":"instagram","followers":"65K", "url":"https://instagram.com/showme_09",        "category":"공구전문"},
    {"id":6,  "name":"사랑댁",         "handle":"peach0724s2",      "platform":"instagram","followers":"94K", "url":"https://instagram.com/peach0724s2",      "category":"육아/키즈"},
    {"id":7,  "name":"메이민맘",       "handle":"may__miin",        "platform":"instagram","followers":"65K", "url":"https://instagram.com/may__miin",        "category":"키즈/육아"},
    {"id":8,  "name":"꿀단지맘",       "handle":"honey_momlog",     "platform":"instagram","followers":"58K", "url":"https://instagram.com/honey_momlog",     "category":"육아/공구"},
    {"id":9,  "name":"달달이네",       "handle":"daldal_home",      "platform":"instagram","followers":"52K", "url":"https://instagram.com/daldal_home",      "category":"육아/인테리어"},
    {"id":10, "name":"도담맘",         "handle":"dodam_momlife",    "platform":"instagram","followers":"48K", "url":"https://instagram.com/dodam_momlife",    "category":"육아"},
    {"id":11, "name":"맘스클로젯",     "handle":"moms_closet_kr",   "platform":"instagram","followers":"45K", "url":"https://instagram.com/moms_closet_kr",   "category":"키즈패션"},
    {"id":12, "name":"봄이네공구",     "handle":"bom_gonggu",       "platform":"instagram","followers":"42K", "url":"https://instagram.com/bom_gonggu",       "category":"공구전문"},
    {"id":13, "name":"초롱맘",         "handle":"chorong_mama_",    "platform":"instagram","followers":"39K", "url":"https://instagram.com/chorong_mama_",    "category":"육아"},
    {"id":14, "name":"하윤맘",         "handle":"hayoon_mama_log",  "platform":"instagram","followers":"36K", "url":"https://instagram.com/hayoon_mama_log",  "category":"육아/교육"},
    {"id":15, "name":"루미맘",         "handle":"rumi_mom_daily",   "platform":"instagram","followers":"33K", "url":"https://instagram.com/rumi_mom_daily",   "category":"육아"},
    # === 네이버 블로그 ===
    {"id":16, "name":"꿀육아로그",     "handle":"honey_ug_log",     "platform":"naver_blog","followers":"일방문 8천+","url":"https://blog.naver.com/honey_ug_log",    "category":"육아/공구"},
    {"id":17, "name":"알뜰살뜰맘",    "handle":"save_mom_life",    "platform":"naver_blog","followers":"일방문 6천+","url":"https://blog.naver.com/save_mom_life",   "category":"육아/절약"},
    {"id":18, "name":"초록이네육아",   "handle":"green_baby_log",   "platform":"naver_blog","followers":"일방문 5천+","url":"https://blog.naver.com/green_baby_log",  "category":"육아"},
    {"id":19, "name":"소나기맘",       "handle":"sonagi_mama_kr",   "platform":"naver_blog","followers":"일방문 5천+","url":"https://blog.naver.com/sonagi_mama_kr",  "category":"육아/리뷰"},
    {"id":20, "name":"하루하나육아",   "handle":"haru_one_mom",     "platform":"naver_blog","followers":"일방문 4천+","url":"https://blog.naver.com/haru_one_mom",    "category":"육아"},
]

# ──────────────────────────────────────────
# 실제 한국 육아 브랜드 & 상품 데이터
# ──────────────────────────────────────────
REAL_PRODUCTS = [
    # 기저귀/위생
    {"name":"하기스 네이처메이드 기저귀 팬티형 L 4팩",        "brand":"하기스",     "cat":"기저귀/위생",   "price":47900,  "orig":68000,  "unit":"세트"},
    {"name":"보솜이 프리미엄 기저귀 점보팩 M",                "brand":"보솜이",     "cat":"기저귀/위생",   "price":26900,  "orig":38000,  "unit":"팩"},
    {"name":"마미포코 팬티기저귀 XL 2팩+물티슈 10팩",         "brand":"마미포코",   "cat":"기저귀/위생",   "price":35500,  "orig":54000,  "unit":"세트"},
    {"name":"베베숲 순수 무향 물티슈 캡형 10팩",              "brand":"베베숲",     "cat":"기저귀/위생",   "price":14900,  "orig":22000,  "unit":"10팩"},
    {"name":"그린핑거 베이비 세탁세제 2.3L+섬유유연제",       "brand":"그린핑거",   "cat":"기저귀/위생",   "price":19800,  "orig":29800,  "unit":"세트"},
    {"name":"수오미 코세척기 + 식염수 3개월분",               "brand":"수오미",     "cat":"기저귀/위생",   "price":28500,  "orig":42000,  "unit":"세트"},
    # 이유식/식품
    {"name":"오가닉 당근 단호박 이유식 파우치 10팩",          "brand":"베이비본죽", "cat":"이유식/식품",   "price":18900,  "orig":28000,  "unit":"10팩"},
    {"name":"함소아 유기농 쌀과자 3박스",                     "brand":"함소아",     "cat":"이유식/식품",   "price":15900,  "orig":24000,  "unit":"3박스"},
    {"name":"아이꼼마 초기 이유식 쌀가루 500g×3",            "brand":"아이꼼마",   "cat":"이유식/식품",   "price":22500,  "orig":33000,  "unit":"3개"},
    {"name":"엘빈즈 아기밥솥 이유식 메이커",                  "brand":"엘빈즈",     "cat":"이유식/식품",   "price":64900,  "orig":99000,  "unit":"1개"},
    {"name":"압착 과일즙 사과+배 혼합 30팩",                  "brand":"아이배냇",   "cat":"이유식/식품",   "price":24900,  "orig":36000,  "unit":"30팩"},
    {"name":"분유 NAN 3단계 800g×2캔 세트",                   "brand":"네슬레",     "cat":"이유식/식품",   "price":58000,  "orig":82000,  "unit":"2캔"},
    # 스킨케어
    {"name":"베베드피노 순한 아기 로션 400ml×2",              "brand":"베베드피노", "cat":"스킨케어",      "price":22900,  "orig":34000,  "unit":"2개"},
    {"name":"닥터노 베이비 선크림 SPF50+ PA++++ 50ml×3",     "brand":"닥터노",     "cat":"스킨케어",      "price":28500,  "orig":42000,  "unit":"3개"},
    {"name":"아토팜 리얼 베리어 크림 80g×3+토너 150ml",      "brand":"아토팜",     "cat":"스킨케어",      "price":39900,  "orig":59800,  "unit":"세트"},
    {"name":"피부장벽 아기 에센스 100ml+보습크림 세트",       "brand":"위드맘",     "cat":"스킨케어",      "price":18900,  "orig":28000,  "unit":"세트"},
    # 수유/젖병
    {"name":"닥터브라운스 와이드넥 젖병 270ml 4개 세트",      "brand":"닥터브라운스","cat":"수유/젖병",    "price":42900,  "orig":64000,  "unit":"4개"},
    {"name":"피죤 모유실감 젖병 160ml+280ml 세트",            "brand":"피죤",       "cat":"수유/젖병",     "price":26900,  "orig":38000,  "unit":"세트"},
    {"name":"필립스 아벤트 SCF 전동 유축기",                  "brand":"아벤트",     "cat":"수유/젖병",     "price":129000, "orig":198000, "unit":"1개"},
    {"name":"미미월드 보온 젖병 가방+쿨러팩 세트",            "brand":"미미월드",   "cat":"수유/젖병",     "price":15900,  "orig":22000,  "unit":"세트"},
    # 외출용품
    {"name":"조이 라이더 카시트 신생아~18kg",                 "brand":"조이",       "cat":"외출용품",      "price":189000, "orig":289000, "unit":"1개"},
    {"name":"베이비뵨 하모니 바운서",                         "brand":"베이비뵨",   "cat":"외출용품",      "price":219000, "orig":"329000","unit":"1개"},
    {"name":"에르고베이비 옴니360 쿨에어 아기띠",             "brand":"에르고베이비","cat":"외출용품",     "price":168000, "orig":258000, "unit":"1개"},
    {"name":"리안 레인저 경량 절충형 유모차",                 "brand":"리안",       "cat":"외출용품",      "price":249000, "orig":389000, "unit":"1개"},
    {"name":"코지 다목적 힙시트 캐리어",                      "brand":"코지",       "cat":"외출용품",      "price":79000,  "orig":119000, "unit":"1개"},
    # 장난감/교구
    {"name":"레고 듀플로 동물 농장 10949",                    "brand":"레고",       "cat":"장난감/교구",   "price":35900,  "orig":52000,  "unit":"1개"},
    {"name":"원목 쌓기 블록 100pcs + 보관함",                 "brand":"몬테소리",   "cat":"장난감/교구",   "price":28900,  "orig":42000,  "unit":"세트"},
    {"name":"피셔프라이스 뮤직컵 모빌 침대부착형",            "brand":"피셔프라이스","cat":"장난감/교구",  "price":38500,  "orig":58000,  "unit":"1개"},
    {"name":"말랑 촉감 공 12종 세트",                         "brand":"사이언픽",   "cat":"장난감/교구",   "price":19900,  "orig":29800,  "unit":"12종"},
    # 가구/인테리어
    {"name":"유풍 퍼즐 놀이매트 두께4cm 200×140",             "brand":"유풍",       "cat":"가구/인테리어", "price":52900,  "orig":79000,  "unit":"1장"},
    {"name":"이케아 SUNDVIK 유아 침대 + 매트리스",            "brand":"이케아",     "cat":"가구/인테리어", "price":139000, "orig":199000, "unit":"세트"},
    {"name":"안전문 계단/문 울타리 철제형 140cm",             "brand":"베이비세이프","cat":"가구/인테리어", "price":45900,  "orig":68000,  "unit":"1개"},
    {"name":"핫팩 보온 속싸개 + 겉싸개 세트",                 "brand":"아가방",     "cat":"가구/인테리어", "price":29900,  "orig":44000,  "unit":"세트"},
    # 의류/패션
    {"name":"BDZ 아동 사계절 내의 5종 세트 (90-130)",         "brand":"블루독",     "cat":"의류/패션",     "price":38900,  "orig":58000,  "unit":"5종"},
    {"name":"로가디스 남아 봄 바람막이 점퍼",                 "brand":"로가디스",   "cat":"의류/패션",     "price":42000,  "orig":65000,  "unit":"1개"},
    {"name":"알로앤루 우주복 신생아 3종 세트",                "brand":"알로앤루",   "cat":"의류/패션",     "price":35900,  "orig":52000,  "unit":"3종"},
    {"name":"미니미니 여아 드레스 원피스 2종",                "brand":"미니미니",   "cat":"의류/패션",     "price":28500,  "orig":42000,  "unit":"2개"},
    # 교육/도서
    {"name":"한글이 야호 시즌2 전집 30권+DVD",               "brand":"EBS미디어",  "cat":"교육/도서",     "price":79000,  "orig":129000, "unit":"세트"},
    {"name":"아이챌린지 B단계 (2세) 4개월 구독",              "brand":"샘토이",     "cat":"교육/도서",     "price":68000,  "orig":98000,  "unit":"4개월"},
    {"name":"뽀로로 영어 전집 20권 + 오디오펜",              "brand":"아이코닉스",  "cat":"교육/도서",     "price":89000,  "orig":138000, "unit":"세트"},
]

STATUSES = ["진행중","진행중","진행중","진행중","오늘마감","마감임박","오픈예정"]

def load_real_data():
    """real_gonggu.json에서 직접 입력한 실제 공구 데이터를 읽어 기존 형식으로 변환"""
    real_path = DATA_DIR / "real_gonggu.json"
    if not real_path.exists():
        return []
    try:
        with open(real_path, encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        return []

    results = []
    for item in items:
        end_str = item.get("end_date", "")
        # end_date가 "YYYY-MM-DD" 형식이면 MM/DD로 변환
        if len(end_str) == 10 and "-" in end_str:
            end_display = end_str[5:].replace("-", "/")
        else:
            end_display = end_str

        orig  = int(item.get("original_price", 0) or 0)
        sale  = int(item.get("sale_price", 0) or 0)
        disc  = item.get("discount_rate") or (round((1 - sale/orig)*100) if orig > 0 else 0)

        handle = item.get("handle", "").lstrip("@")
        platform = item.get("platform", "instagram")
        if platform == "instagram":
            inf_url = f"https://instagram.com/{handle}"
        else:
            inf_url = f"https://blog.naver.com/{handle}"

        results.append({
            "uid": item.get("id", f"real_{hash(item.get('product_name',''))}"),
            "title": f"[공구] {item.get('product_name','')}",
            "link": item.get("link", inf_url),
            "description": item.get("description", ""),
            "date": item.get("created_at", datetime.now().strftime("%Y-%m-%d")),
            "is_real": True,
            "gonggu_info": {
                "is_gonggu":      True,
                "product_name":   item.get("product_name", ""),
                "brand":          item.get("brand", ""),
                "price":          f"{sale:,}원",
                "original_price": f"{orig:,}원",
                "discount":       f"{disc}%",
                "period":         end_display,
                "status":         item.get("status", "진행중"),
                "keywords_found": ["공구", "실제공구"]
            },
            "category": item.get("category", "기타"),
            "influencer": {
                "id":        0,
                "name":      item.get("influencer", ""),
                "handle":    handle,
                "platform":  platform,
                "url":       inf_url,
                "followers": item.get("followers", ""),
                "category":  "육아"
            }
        })
    return results


def build_data():
    now = datetime.now()

    # 북마크릿으로 직접 입력한 실제 공구 데이터만 사용
    results = load_real_data()

    # 최신순 정렬
    results.sort(key=lambda x: x["date"], reverse=True)

    inf_names = set(r["influencer"]["name"] for r in results if r["influencer"]["name"])

    output = {
        "scraped_at":        now.isoformat(),
        "date":              now.strftime("%Y-%m-%d"),
        "stats": {
            "total":       len(results),
            "influencers": len(inf_names),
            "instagram":   sum(1 for r in results if r["influencer"]["platform"]=="instagram"),
            "naver":       sum(1 for r in results if r["influencer"]["platform"]=="naver_blog"),
            "errors":      0
        },
        "total_gonggu_found": len(results),
        "results": results
    }
    return output

# ──────────────────────────────────────────
# HTML 생성
# ──────────────────────────────────────────
def build_html(data):
    results    = data["results"]
    stats      = data["stats"]
    scraped_at = data["scraped_at"]

    PLATFORM_ICON = {"instagram":"📸", "naver_blog":"📝"}
    STATUS_COLOR  = {"진행중":"#00C851","마감임박":"#FF6900","오늘마감":"#FF0000","오픈예정":"#0066CC"}

    # 전체 데이터 JSON
    results_json = json.dumps(results, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>🍼 육아 공구 모아보기</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --pink:#FF6B9D;--pink-light:#FFF0F5;
  --teal:#00BFA5;--teal-light:#E0F7F4;
  --yellow:#FFD93D;--orange:#FF6900;
  --dark:#1A1A2E;--gray:#6B7280;--light:#F7F8FC;
  --white:#fff;
  --r:14px;--shadow:0 2px 16px rgba(0,0,0,.07);--shadow2:0 8px 32px rgba(0,0,0,.13)
}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Noto Sans KR',sans-serif;background:var(--light);color:var(--dark)}}

/* ── HEADER ── */
.header{{
  background:linear-gradient(135deg,#FF6B9D 0%,#FF8C69 100%);
  color:#fff;padding:1.25rem 1rem .8rem;text-align:center;
  position:sticky;top:0;z-index:200;
  box-shadow:0 4px 20px rgba(255,107,157,.35)
}}
.header h1{{font-size:1.6rem;font-weight:900;letter-spacing:-.5px}}
.header .sub{{font-size:.82rem;opacity:.88;margin-top:.2rem}}
.last-update{{font-size:.72rem;opacity:.7;margin-top:.35rem}}

/* ── STATS ── */
.stats{{display:flex;justify-content:center;gap:2rem;padding:.9rem 1rem;background:#fff;border-bottom:1px solid #f0f0f0;flex-wrap:wrap}}
.s-item{{text-align:center}}
.s-num{{font-size:1.55rem;font-weight:900;color:var(--pink)}}
.s-label{{font-size:.68rem;color:var(--gray);margin-top:.1rem;letter-spacing:.03em}}

/* ── SEARCH ── */
.search-wrap{{padding:.8rem 1rem;background:#fff;border-bottom:1px solid #f0f0f0}}
.search-inner{{max-width:600px;margin:0 auto;position:relative}}
.search-inner input{{
  width:100%;padding:.7rem 1rem .7rem 2.6rem;
  border:2px solid #e5e7eb;border-radius:40px;font-size:.92rem;outline:none;
  transition:border-color .2s
}}
.search-inner input:focus{{border-color:var(--pink)}}
.search-inner::before{{content:"🔍";position:absolute;left:.9rem;top:50%;transform:translateY(-50%);font-size:.9rem}}

/* ── PLATFORM TABS ── */
.platform-tabs{{display:flex;gap:.5rem;padding:.6rem 1rem;background:#fff;border-bottom:1px solid #f0f0f0}}
.ptab{{padding:.35rem .9rem;border-radius:20px;font-size:.8rem;font-weight:700;cursor:pointer;border:1.5px solid #e0e0e0;background:#fff;transition:all .2s}}
.ptab.on{{background:var(--dark);color:#fff;border-color:var(--dark)}}

/* ── CATEGORY FILTER ── */
.cat-bar{{padding:.6rem 1rem;overflow-x:auto;white-space:nowrap;background:#fff;border-bottom:1px solid #f0f0f0;scrollbar-width:none}}
.cat-bar::-webkit-scrollbar{{display:none}}
.chip{{
  display:inline-block;padding:.35rem .9rem;margin-right:.4rem;
  border-radius:20px;font-size:.78rem;font-weight:600;cursor:pointer;
  border:1.5px solid #e0e0e0;background:#fff;color:#555;transition:all .2s
}}
.chip:hover{{border-color:var(--pink);color:var(--pink)}}
.chip.on{{background:var(--pink);color:#fff;border-color:var(--pink)}}
.chip .cnt{{font-size:.68rem;opacity:.75;margin-left:.15rem}}

/* ── SORT BAR ── */
.sort-bar{{display:flex;justify-content:space-between;align-items:center;padding:.5rem 1rem}}
.res-cnt{{font-size:.82rem;color:var(--gray)}}
.sort-sel{{padding:.35rem .7rem;border:1px solid #ddd;border-radius:8px;font-size:.78rem;background:#fff;outline:none}}

/* ── GRID ── */
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:.9rem;padding:.4rem 1rem 3rem;max-width:1240px;margin:0 auto}}

/* ── CARD ── */
.card{{
  background:#fff;border-radius:var(--r);box-shadow:var(--shadow);
  cursor:pointer;transition:all .25s;overflow:hidden;position:relative
}}
.card:hover{{box-shadow:var(--shadow2);transform:translateY(-3px)}}

.card-top{{padding:.9rem 1rem .5rem;display:flex;justify-content:space-between;align-items:flex-start}}
.inf-row{{display:flex;align-items:center;gap:.55rem}}
.avatar{{
  width:38px;height:38px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:.85rem;font-weight:800;color:#fff;flex-shrink:0
}}
.av-ig{{background:linear-gradient(135deg,#833AB4,#FD1D1D,#FCB045)}}
.av-nb{{background:linear-gradient(135deg,#03C75A,#00863C)}}
.inf-name{{font-size:.85rem;font-weight:800}}
.inf-handle{{font-size:.7rem;color:var(--gray)}}

.status{{
  padding:.2rem .55rem;border-radius:10px;font-size:.68rem;font-weight:800;
  white-space:nowrap;flex-shrink:0
}}
.st-진행중{{background:#E8F5E9;color:#2E7D32}}
.st-마감임박{{background:#FFF3E0;color:#E65100}}
.st-오늘마감{{background:#FFEBEE;color:#C62828;animation:blink 1.5s ease-in-out infinite}}
.st-오픈예정{{background:#E3F2FD;color:#1565C0}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}

.real-badge{{
  background:linear-gradient(135deg,#43A047,#00897B);color:#fff;
  padding:.15rem .45rem;border-radius:8px;font-size:.62rem;font-weight:800;
  white-space:nowrap;letter-spacing:.02em
}}
.real-card{{border:2px solid #A5D6A7 !important;box-shadow:0 2px 16px rgba(76,175,80,.18) !important}}

.card-body{{padding:.4rem 1rem .8rem}}
.prod-name{{font-size:.95rem;font-weight:800;line-height:1.4;margin-bottom:.45rem}}
.brand-tag{{
  display:inline-block;background:var(--teal-light);color:#00695C;
  padding:.1rem .45rem;border-radius:6px;font-size:.68rem;font-weight:700;margin-bottom:.4rem
}}
.price-row{{display:flex;align-items:baseline;gap:.45rem;flex-wrap:wrap}}
.price{{font-size:1.18rem;font-weight:900;color:var(--pink)}}
.orig{{font-size:.78rem;color:#aaa;text-decoration:line-through}}
.disc{{background:var(--pink);color:#fff;padding:.15rem .45rem;border-radius:6px;font-size:.72rem;font-weight:800}}

.card-foot{{
  display:flex;justify-content:space-between;align-items:center;
  padding:.55rem 1rem;border-top:1px solid #f5f5f5;font-size:.73rem;color:var(--gray)
}}
.cat-tag{{background:#F3F4F6;color:#555;padding:.15rem .5rem;border-radius:6px;font-size:.7rem;font-weight:600}}

/* ── MODAL ── */
.overlay{{
  display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);
  z-index:500;justify-content:center;align-items:center;padding:1rem
}}
.overlay.show{{display:flex}}
.modal{{
  background:#fff;border-radius:20px;max-width:480px;width:100%;
  max-height:88vh;overflow-y:auto;padding:1.5rem;
  box-shadow:0 20px 60px rgba(0,0,0,.2)
}}
.modal-head{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem}}
.modal-head h3{{font-size:1.05rem;font-weight:800;line-height:1.4;flex:1;padding-right:.5rem}}
.close-btn{{background:none;border:none;font-size:1.4rem;cursor:pointer;color:#aaa;flex-shrink:0}}
.info-box{{background:var(--light);border-radius:12px;padding:1rem;margin-bottom:1rem}}
.info-row{{display:flex;justify-content:space-between;align-items:center;padding:.35rem 0;border-bottom:1px solid #eee;font-size:.88rem}}
.info-row:last-child{{border:none}}
.info-val{{font-weight:700}}
.go-btn{{
  display:block;text-align:center;
  background:linear-gradient(135deg,var(--pink),#FF8C69);
  color:#fff;padding:.85rem;border-radius:12px;
  text-decoration:none;font-weight:800;font-size:.95rem;
  box-shadow:0 4px 15px rgba(255,107,157,.35)
}}
.inf-card{{display:flex;align-items:center;gap:.75rem;padding:.8rem;background:#f9f9f9;border-radius:12px;margin-bottom:1rem}}

/* ── EMPTY ── */
.empty{{grid-column:1/-1;text-align:center;padding:4rem 1rem;color:var(--gray)}}
.empty .ico{{font-size:3rem;margin-bottom:1rem}}

/* ── FOOTER ── */
footer{{text-align:center;padding:1.5rem 1rem;font-size:.75rem;color:#bbb}}

@media(max-width:640px){{
  .header h1{{font-size:1.35rem}}
  .stats{{gap:1.2rem}}
  .s-num{{font-size:1.3rem}}
  .grid{{grid-template-columns:1fr;padding:.4rem .75rem 3rem}}
}}
</style>
</head>
<body>

<div class="header">
  <h1>🍼 육아 공구 모아보기</h1>
  <p class="sub">인기 육아 인플루언서들의 공동구매 한눈에 보기</p>
  <p class="last-update" id="lu">업데이트 로딩중...</p>
</div>

<div class="stats">
  <div class="s-item"><div class="s-num" id="sTotal">-</div><div class="s-label">TODAY 공구</div></div>
  <div class="s-item"><div class="s-num" id="sInf">-</div><div class="s-label">참여 인플루언서</div></div>
  <div class="s-item"><div class="s-num" id="sActive">-</div><div class="s-label">진행중</div></div>
  <div class="s-item"><div class="s-num" id="sEnd">-</div><div class="s-label">오늘마감</div></div>
</div>

<div class="search-wrap">
  <div class="search-inner">
    <input type="text" id="q" placeholder="브랜드·상품명·인플루언서 검색..." oninput="render()">
  </div>
</div>

<div class="platform-tabs">
  <button class="ptab on" data-p="all"   onclick="setPlatform('all')">전체</button>
  <button class="ptab"    data-p="instagram"  onclick="setPlatform('instagram')">📸 인스타그램</button>
  <button class="ptab"    data-p="naver_blog" onclick="setPlatform('naver_blog')">📝 블로그</button>
</div>

<div class="cat-bar" id="catBar">
  <span class="chip on" data-c="all" onclick="setCat('all')">전체</span>
</div>

<div class="sort-bar">
  <span class="res-cnt" id="resCnt">0건</span>
  <select class="sort-sel" id="sortSel" onchange="render()">
    <option value="latest">최신순</option>
    <option value="discount">할인율 높은순</option>
    <option value="ending">마감임박순</option>
    <option value="price_lo">가격 낮은순</option>
    <option value="price_hi">가격 높은순</option>
  </select>
</div>

<div class="grid" id="grid"></div>

<footer>
  매일 오전 8시 자동 업데이트 · 북마크릿으로 직접 추가하는 실제 공구만 표시<br>
  📸 인스타그램 + 📝 블로그
</footer>

<div class="overlay" id="ov" onclick="closeModal(event)">
  <div class="modal" id="modal"></div>
</div>

<script>
const D = {results_json};
const SCRAPED_AT = "{scraped_at}";

let curCat = 'all', curPlat = 'all';

function init(){{
  // 업데이트 시간
  const d = new Date(SCRAPED_AT);
  document.getElementById('lu').textContent =
    `마지막 업데이트: ${{d.getFullYear()}}.${{d.getMonth()+1}}.${{d.getDate()}} ${{String(d.getHours()).padStart(2,'0')}}:${{String(d.getMinutes()).padStart(2,'0')}}`;

  // 통계
  document.getElementById('sTotal').textContent  = D.length;
  document.getElementById('sInf').textContent    = new Set(D.map(x=>x.influencer.handle)).size;
  document.getElementById('sActive').textContent = D.filter(x=>x.gonggu_info.status==='진행중').length;
  document.getElementById('sEnd').textContent    = D.filter(x=>x.gonggu_info.status==='오늘마감').length;

  buildCatChips();
  render();
}}

function buildCatChips(){{
  const cnt={{}};
  D.forEach(d=>{{ const c=d.category||'기타'; cnt[c]=(cnt[c]||0)+1; }});
  const bar=document.getElementById('catBar');
  Object.entries(cnt).sort((a,b)=>b[1]-a[1]).forEach(([c,n])=>{{
    const s=document.createElement('span');
    s.className='chip'; s.dataset.c=c;
    s.innerHTML=`${{c}} <span class="cnt">${{n}}</span>`;
    s.onclick=()=>setCat(c);
    bar.appendChild(s);
  }});
}}

function setCat(c){{
  curCat=c;
  document.querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',x.dataset.c===c));
  render();
}}

function setPlatform(p){{
  curPlat=p;
  document.querySelectorAll('.ptab').forEach(x=>x.classList.toggle('on',x.dataset.p===p));
  render();
}}

function getFiltered(){{
  const q=document.getElementById('q').value.toLowerCase();
  return D.filter(d=>{{
    if(curCat!=='all'&&d.category!==curCat) return false;
    if(curPlat!=='all'&&d.influencer.platform!==curPlat) return false;
    if(q){{
      const t=[d.gonggu_info.product_name,d.gonggu_info.brand,d.influencer.name,d.influencer.handle,d.category]
        .join(' ').toLowerCase();
      if(!t.includes(q)) return false;
    }}
    return true;
  }});
}}

function sorted(arr){{
  const s=document.getElementById('sortSel').value;
  return [...arr].sort((a,b)=>{{
    switch(s){{
      case 'latest':   return b.date.localeCompare(a.date);
      case 'discount': return parseInt(b.gonggu_info.discount)-parseInt(a.gonggu_info.discount);
      case 'ending':   const o={{'오늘마감':0,'마감임박':1,'진행중':2,'오픈예정':3}};
                       return (o[a.gonggu_info.status]??4)-(o[b.gonggu_info.status]??4);
      case 'price_lo': return numPrice(a)-numPrice(b);
      case 'price_hi': return numPrice(b)-numPrice(a);
      default: return 0;
    }}
  }});
}}
const numPrice=d=>parseInt((d.gonggu_info.price||'0').replace(/[^0-9]/g,''))||0;

function render(){{
  const data=sorted(getFiltered());
  document.getElementById('resCnt').textContent=`${{data.length}}건`;
  const grid=document.getElementById('grid');
  if(!data.length){{
    grid.innerHTML=`<div class="empty"><div class="ico">🔍</div><p>검색 결과가 없습니다</p></div>`;
    return;
  }}
  grid.innerHTML=data.map(d=>{{
    const i=d.influencer, g=d.gonggu_info;
    const av=i.platform==='instagram'?'av-ig':'av-nb';
    const ic=i.platform==='instagram'?'📸':'📝';
    return `<div class="card${{d.is_real?' real-card':''}}" onclick="openModal('${{d.uid}}')">
      <div class="card-top">
        <div class="inf-row">
          <div class="avatar ${{av}}">${{i.name[0]}}</div>
          <div>
            <div class="inf-name">${{i.name}}</div>
            <div class="inf-handle">${{ic}} @${{i.handle}} · ${{i.followers}}</div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
          ${{d.is_real?'<span class="real-badge">✅ 실제 공구</span>':''}}
          <span class="status st-${{g.status}}">${{g.status}}</span>
        </div>
      </div>
      <div class="card-body">
        ${{g.brand?`<div class="brand-tag">${{g.brand}}</div>`:''}}
        <div class="prod-name">${{(g.product_name||d.title).replace(new RegExp('^'+g.brand+'\\\\s*'),'').trim()||g.product_name||d.title}}</div>
        <div class="price-row">
          <span class="price">${{g.price}}</span>
          <span class="orig">${{g.original_price}}</span>
          <span class="disc">${{g.discount}} OFF</span>
        </div>
      </div>
      <div class="card-foot">
        <span class="cat-tag">${{d.category}}</span>
        <span>~${{g.period||''}} 마감</span>
      </div>
    </div>`;
  }}).join('');
}}

function openModal(uid){{
  const d=D.find(x=>x.uid===uid); if(!d) return;
  const i=d.influencer, g=d.gonggu_info;
  const av=i.platform==='instagram'?'av-ig':'av-nb';
  document.getElementById('modal').innerHTML=`
    <div class="modal-head">
      <h3>${{g.product_name||d.title}}</h3>
      <button class="close-btn" onclick="closeModal()">×</button>
    </div>
    ${{d.is_real?'<div style="background:#E8F5E9;border-radius:10px;padding:.4rem .8rem;margin-bottom:.8rem;font-size:.8rem;color:#2E7D32;font-weight:700">✅ 직접 등록한 실제 공구 데이터입니다</div>':''}}
    <div class="inf-card">
      <div class="avatar ${{av}}" style="width:44px;height:44px">${{i.name[0]}}</div>
      <div>
        <div style="font-weight:800">${{i.name}}</div>
        <div style="font-size:.78rem;color:#999">@${{i.handle}} · ${{i.followers}} 팔로워</div>
      </div>
    </div>
    <div class="info-box">
      <div class="info-row"><span>브랜드</span><span class="info-val">${{g.brand||'-'}}</span></div>
      <div class="info-row"><span>공구가</span><span class="info-val" style="color:var(--pink);font-size:1.1rem">${{g.price}}</span></div>
      <div class="info-row"><span>정가</span><span class="info-val" style="text-decoration:line-through;color:#aaa">${{g.original_price}}</span></div>
      <div class="info-row"><span>할인율</span><span class="info-val" style="color:var(--pink)">${{g.discount}} OFF</span></div>
      <div class="info-row"><span>마감일</span><span class="info-val">${{g.period||'-'}}</span></div>
      <div class="info-row"><span>상태</span><span class="status st-${{g.status}}" style="padding:.2rem .6rem">${{g.status}}</span></div>
    </div>
    <a class="go-btn" href="${{d.link}}" target="_blank" rel="noopener">
      ${{i.platform==='instagram'?'📸 인스타그램':'📝 블로그'}}에서 공구 보기 →
    </a>
  `;
  document.getElementById('ov').classList.add('show');
}}
function closeModal(e){{
  if(!e||e.target===e.currentTarget)
    document.getElementById('ov').classList.remove('show');
}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeModal()}});
init();
</script>
</body>
</html>"""

    out = BASE_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ index.html 생성 완료 ({out.stat().st_size//1024}KB)")
    return out

if __name__ == "__main__":
    print("📦 데이터 빌드 중...")
    data = build_data()
    print(f"   인플루언서: {data['stats']['influencers']}명")
    print(f"   총 공구:    {data['total_gonggu_found']}건")

    cats = {}
    for r in data["results"]:
        c = r["category"]
        cats[c] = cats.get(c, 0) + 1
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"   {c}: {n}건")

    latest = DATA_DIR / "latest.json"
    latest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ latest.json 저장")

    build_html(data)
