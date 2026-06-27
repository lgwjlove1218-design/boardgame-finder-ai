import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://boardlife.co.kr"

RANK_URLS = [
    "https://boardlife.co.kr/rank/all/1",
    "https://boardlife.co.kr/rank/all/2",
    "https://boardlife.co.kr/rank/all/3",
]

def parse_players(text):
    match = re.search(r"(\d+)\s*-\s*(\d+)명", text)
    if match:
        min_p = int(match.group(1))
        max_p = int(match.group(2))
        return min_p, max_p, f"{min_p}~{max_p}명"

    match = re.search(r"(\d+)명", text)
    if match:
        n = int(match.group(1))
        return n, n, f"{n}명"

    return None, None, "정보 없음"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1400,1200")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

games = []

try:
    for page_url in RANK_URLS:
        print(f"랭킹 페이지 수집 중: {page_url}")
        driver.get(page_url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        title_tags = soup.select("a.title.new-ellip")

        for tag in title_tags:
            name = tag.get_text(strip=True)
            href = tag.get("href", "")

            if not name or not href:
                continue

            link = BASE_URL + href if href.startswith("/") else href
            rank = len(games) + 1

            print(f"{rank}위 상세 수집 중: {name}")

            driver.get(link)
            time.sleep(1.2)

            detail_soup = BeautifulSoup(driver.page_source, "html.parser")

            # 인원수
            players_text = "정보 없음"
            players_min, players_max = None, None

            player_dd = detail_soup.select_one("dd.data.flex-div")
            if player_dd:
                raw_players = player_dd.get_text(" ", strip=True)
                players_min, players_max, players_text = parse_players(raw_players)

            # 장르
            genre = "정보 없음"
            genre_tag = detail_soup.select_one('a.title[href^="/info/type/"]')
            if genre_tag:
                genre = genre_tag.get_text(strip=True)

            # 평점
            rating = "정보 없음"
            rating_tag = detail_soup.select_one("a.game-rate.data")
            if rating_tag:
                rating_text = rating_tag.get_text(strip=True)
                m = re.search(r"\d+(\.\d+)?", rating_text)
                if m:
                    rating = m.group(0)

            games.append({
                "rank": rank,
                "name": name,
                "boardlife_link": link,
                "players": players_text,
                "players_min": players_min,
                "players_max": players_max,
                "genre": genre,
                "rating": rating,
                "shopping_link": f"https://search.shopping.naver.com/search/all?query={name} 보드게임",
                "google_link": f"https://www.google.com/search?q={name} 보드게임",
            })

            if len(games) >= 300:
                break

        if len(games) >= 300:
            break

finally:
    driver.quit()

df = pd.DataFrame(games)
df.to_csv("boardlife_games.csv", index=False, encoding="utf-8-sig")

print(f"완료! 총 {len(df)}개 게임 저장")
print("boardlife_games.csv 생성 완료!")