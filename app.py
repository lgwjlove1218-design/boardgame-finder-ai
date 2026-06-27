import streamlit as st
import pandas as pd
from urllib.parse import quote

st.set_page_config(
    page_title="BoardGame Finder AI",
    page_icon="🎲",
    layout="wide"
)

st.markdown("""
<style>
.title {
    font-size:52px;
    font-weight:900;
    margin-bottom:8px;
}
.subtitle {
    font-size:20px;
    color:#666;
    margin-bottom:35px;
}
.card {
    border:1px solid #e5e7eb;
    border-radius:22px;
    padding:24px;
    margin-bottom:22px;
    box-shadow:0 6px 20px rgba(0,0,0,0.06);
    background:white;
}
.badge {
    display:inline-block;
    background:#f1f5f9;
    padding:7px 12px;
    border-radius:999px;
    margin:4px;
    font-size:14px;
}
.reason {
    background:#f8fafc;
    padding:15px;
    border-radius:14px;
    margin-top:12px;
    line-height:1.7;
}
.small-text {
    color:#666;
    font-size:14px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 데이터 불러오기
# =========================
df = pd.read_csv("boardlife_games.csv")

df["players_min"] = pd.to_numeric(df["players_min"], errors="coerce")
df["players_max"] = pd.to_numeric(df["players_max"], errors="coerce")
df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")


# =========================
# 함수
# =========================
def clean_genre(g):
    g = str(g).replace("게임", "").strip()
    return g if g and g != "nan" else "정보 없음"


def format_rating(value):
    if pd.notna(value):
        return f"{float(value):.3f}"
    return "정보 없음"


def safe_link(value, fallback):
    if pd.isna(value) or not str(value).startswith("http"):
        return fallback
    return str(value)


def get_mood_analysis(memo):
    memo = str(memo).strip()

    mood_rules = {
        "파티/술자리": {
            "keywords": ["파티", "술", "술자리", "웃", "웃긴", "재밌", "시끌", "친구"],
            "genres": ["파티", "추리"],
            "bonus": 900,
            "reason": "여럿이 웃으면서 즐기기 좋은 분위기를 반영했습니다."
        },
        "가벼운/입문": {
            "keywords": ["가벼", "쉬운", "초보", "입문", "간단", "빨리", "부담"],
            "genres": ["파티", "가족", "어린이"],
            "bonus": 800,
            "reason": "초보자도 쉽게 시작할 수 있는 게임을 우선했습니다."
        },
        "전략/깊이": {
            "keywords": ["전략", "머리", "깊이", "고민", "빡겜", "진지", "운빨 적"],
            "genres": ["전략"],
            "bonus": 900,
            "reason": "전략성과 고민할 요소가 있는 게임을 우선했습니다."
        },
        "협력": {
            "keywords": ["협력", "같이", "팀", "다같이", "함께"],
            "genres": ["협력"],
            "bonus": 900,
            "reason": "서로 협력하며 진행하는 게임을 우선했습니다."
        },
        "추리/마피아": {
            "keywords": ["추리", "마피아", "정체", "블러핑", "심리", "속임"],
            "genres": ["추리", "파티"],
            "bonus": 900,
            "reason": "심리전과 추리 요소가 있는 게임을 우선했습니다."
        },
        "가족": {
            "keywords": ["가족", "아이", "어린이", "부모", "명절"],
            "genres": ["가족", "어린이"],
            "bonus": 800,
            "reason": "가족과 함께 즐기기 좋은 게임을 우선했습니다."
        },
        "커플/2인": {
            "keywords": ["커플", "둘이", "2인", "데이트", "여자친구", "남자친구"],
            "genres": ["2인", "가족", "전략"],
            "bonus": 700,
            "reason": "둘이서 즐기기 좋은 게임을 우선했습니다."
        },
    }

    matched = []

    for mood_name, rule in mood_rules.items():
        if any(keyword in memo for keyword in rule["keywords"]):
            matched.append({
                "mood": mood_name,
                "genres": rule["genres"],
                "bonus": rule["bonus"],
                "reason": rule["reason"]
            })

    return matched


def score_game(row, selected_player, selected_genre, memo):
    score = 0

    rank = row["rank"]
    rating = row["rating"]
    genre = clean_genre(row.get("genre", "정보 없음"))

    min_p = row["players_min"]
    max_p = row["players_max"]

    # 순위 점수
    if pd.notna(rank):
        score += max(0, 350 - rank)

    # 평점 점수
    if pd.notna(rating):
        score += rating * 80

    # 인원수 점수
    if selected_player != "상관없음" and pd.notna(min_p) and pd.notna(max_p):
        p = 6 if selected_player == "6명 이상" else int(selected_player.replace("명", ""))

        if min_p <= p <= max_p:
            score += 1200
        else:
            score -= 3000

    # 선택 장르 점수
    if selected_genre != "상관없음":
        if selected_genre in genre:
            score += 1200
        else:
            score -= 1200

    # 원하는 분위기 점수
    mood_matches = get_mood_analysis(memo)

    for match in mood_matches:
        if any(target in genre for target in match["genres"]):
            score += match["bonus"]
        else:
            score -= 250

    return score


def make_reason(row, selected_player, selected_genre, memo):
    name = row["name"]
    genre = clean_genre(row.get("genre", "정보 없음"))
    players = row.get("players", "정보 없음")
    rank = int(row["rank"])
    rating = format_rating(row.get("rating", None))

    reason_parts = []

    reason_parts.append(
        f"{name}은 보드라이프 TOP 300 중 {rank}위 게임이며, 평점은 {rating}입니다."
    )

    reason_parts.append(
        f"수집된 플레이 인원은 {players}, 장르는 {genre}입니다."
    )

    if selected_player != "상관없음":
        reason_parts.append(f"선택한 인원수({selected_player}) 조건을 반영했습니다.")

    if selected_genre != "상관없음":
        reason_parts.append(f"선택한 장르({selected_genre}) 조건을 반영했습니다.")

    mood_matches = get_mood_analysis(memo)

    if memo and mood_matches:
        mood_text = ", ".join([m["mood"] for m in mood_matches])
        reason_parts.append(
            f"입력한 분위기 '{memo}'에서 {mood_text} 키워드를 감지하여 추천 점수에 반영했습니다."
        )
    elif memo:
        reason_parts.append(
            f"입력한 분위기 '{memo}'도 참고했지만, 명확한 분위기 키워드는 감지되지 않았습니다."
        )

    return " ".join(reason_parts)


def mood_help_text(memo):
    mood_matches = get_mood_analysis(memo)

    if not memo:
        return ""

    if not mood_matches:
        return "입력한 분위기에서 명확한 키워드를 찾지 못했습니다. 예: 술자리, 초보, 협력, 추리, 커플, 전략"

    moods = ", ".join([m["mood"] for m in mood_matches])
    return f"감지된 분위기: {moods}"


# =========================
# 화면 상단
# =========================
st.markdown('<div class="title">🎲 BoardGame Finder AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">보드라이프 TOP 300 기반 맞춤 보드게임 추천 서비스</div>',
    unsafe_allow_html=True
)


# =========================
# 사이드바
# =========================
with st.sidebar:
    st.header("🎛 추천 조건")

    mode = st.radio(
        "추천 모드",
        ["AI 맞춤 추천", "랭킹 보기", "랜덤 추천"]
    )

    selected_player = st.selectbox(
        "👥 인원수",
        ["상관없음", "1명", "2명", "3명", "4명", "5명", "6명 이상"]
    )

    genre_options = (
        ["상관없음"]
        + sorted(
            df["genre"]
            .dropna()
            .astype(str)
            .str.replace("게임", "", regex=False)
            .unique()
            .tolist()
        )
    )

    selected_genre = st.selectbox(
        "🎭 장르",
        genre_options
    )

    keyword = st.text_input(
        "🔎 게임명 검색",
        placeholder="예) 스플렌더, 카탄, 코드네임"
    )

    memo = st.text_area(
        "💬 원하는 분위기",
        placeholder="예) 6명이 술자리에서 할 가벼운 파티게임 / 초보자 포함 / 커플끼리"
    )

    if memo:
        help_msg = mood_help_text(memo)
        if "감지된 분위기" in help_msg:
            st.success(help_msg)
        else:
            st.info(help_msg)

    exclude = st.text_input(
        "🚫 제외할 게임",
        placeholder="예) 카탄, 스플렌더"
    )

    top_n = st.slider("표시 개수", 3, 20, 7)


st.divider()


# =========================
# 결과 계산
# =========================
result = df.copy()

# 검색어 필터
if keyword:
    result = result[
        result["name"].astype(str).str.contains(keyword, case=False, na=False)
    ]

# 제외 게임 필터
for ex in [x.strip() for x in exclude.split(",") if x.strip()]:
    result = result[
        ~result["name"].astype(str).str.contains(ex, case=False, na=False)
    ]

# 실제 인원수 필터
if selected_player != "상관없음":
    p = 6 if selected_player == "6명 이상" else int(selected_player.replace("명", ""))

    result = result[
        (result["players_min"].notna())
        & (result["players_max"].notna())
        & (result["players_min"] <= p)
        & (result["players_max"] >= p)
    ]

# 실제 장르 필터
if selected_genre != "상관없음":
    result = result[
        result["genre"].astype(str).str.replace("게임", "", regex=False).str.contains(
            selected_genre, na=False
        )
    ]


# 모드별 처리
if mode == "AI 맞춤 추천":
    result["score"] = result.apply(
        lambda row: score_game(row, selected_player, selected_genre, memo),
        axis=1
    )
    result = result.sort_values("score", ascending=False).head(top_n)
    st.markdown("## 🤖 AI 맞춤 추천 결과")

elif mode == "랜덤 추천":
    result = result.sample(min(top_n, len(result)))
    st.markdown("## 🎁 랜덤 추천 결과")

else:
    result = result.sort_values("rank").head(top_n)
    st.markdown("## 🏆 보드라이프 랭킹 보기")


# =========================
# 결과 출력
# =========================
if result.empty:
    st.warning("조건에 맞는 게임이 없습니다. 인원수나 장르 조건을 조금 넓혀보세요.")

else:
    for _, row in result.iterrows():
        name = str(row["name"])
        rank = int(row["rank"])
        genre = clean_genre(row.get("genre", "정보 없음"))
        players = row.get("players", "정보 없음")
        rating = format_rating(row.get("rating", None))

        boardlife = safe_link(
            row.get("boardlife_link", ""),
            f"https://www.google.com/search?q={quote('보드라이프 ' + name)}"
        )

        shopping = safe_link(
            row.get("shopping_link", ""),
            f"https://search.shopping.naver.com/search/all?query={quote(name + ' 보드게임')}"
        )

        google = safe_link(
            row.get("google_link", ""),
            f"https://www.google.com/search?q={quote(name + ' 보드게임')}"
        )

        st.markdown(f"""
        <div class="card">
            <h2>{rank}위. 🎲 {name}</h2>
            <span class="badge">🏆 TOP {rank}</span>
            <span class="badge">👥 {players}</span>
            <span class="badge">🎭 {genre}</span>
            <span class="badge">⭐ 평점 {rating}</span>
            <div class="reason">
                <b>🤖 AI 추천 이유</b><br>
                {make_reason(row, selected_player, selected_genre, memo)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.link_button("📖 보드라이프", boardlife, use_container_width=True)
        c2.link_button("🛒 구매 검색", shopping, use_container_width=True)
        c3.link_button("🔎 정보 검색", google, use_container_width=True)


with st.expander("ℹ️ 이 AI Agent 설명"):
    st.write("""
    이 앱은 보드라이프 TOP 300 데이터를 기반으로 추천합니다.
    
    각 게임 상세 페이지와 랭킹 페이지에서 수집한 실제 데이터를 활용하여
    플레이 인원, 장르, 평점, 순위, 사용자 입력 키워드를 종합적으로 반영합니다.
    
    '원하는 분위기' 입력란은 단순 메모가 아니라
    술자리, 초보, 전략, 협력, 추리, 가족, 커플 등 키워드를 분석하여 추천 점수에 반영합니다.
    """)