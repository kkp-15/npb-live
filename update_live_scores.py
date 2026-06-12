#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NPB公式の試合一覧から当日のスコア・試合状態を取得し data/live.json に保存する。

本リポジトリ（公開・npb-live）のGitHub Actionsが試合時間帯に約20分毎に実行し、
mainへamend+force pushする（履歴を増やさない）。npb-magic本体が非公開のため、
raw配信用に分離した専用リポジトリ。
サイト側は raw.githubusercontent.com 経由でfetchし、当日分だけ表示に合成する。
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

YEAR = 2026
URL = f"https://npb.jp/games/{YEAR}/"
UA = "Mozilla/5.0 (compatible; npb-magic-live/1.0; +https://npb-magic.kkpwebninja.com)"
OUT = os.path.join(os.path.dirname(__file__), "data", "live.json")

JST = timezone(timedelta(hours=9))

# NPB公式のフルネーム → サイト内表示名
FULL_TO_SHORT = {
    "読売ジャイアンツ": "巨人", "阪神タイガース": "阪神",
    "東京ヤクルトスワローズ": "ヤクルト", "横浜DeNAベイスターズ": "DeNA",
    "横浜ＤｅＮＡベイスターズ": "DeNA", "広島東洋カープ": "広島",
    "中日ドラゴンズ": "中日", "福岡ソフトバンクホークス": "ソフトバンク",
    "東北楽天ゴールデンイーグルス": "楽天", "オリックス・バファローズ": "オリックス",
    "北海道日本ハムファイターズ": "日本ハム", "埼玉西武ライオンズ": "西武",
    "千葉ロッテマリーンズ": "ロッテ",
}


def classify_state(text: str) -> tuple[str, str, str, str]:
    """state文字列 → (status, label, venue, start)。
    例: 「（エスコンＦ） 14:00」→ ('before', '14:00 開始予定', 'エスコンF', '14:00')
    statusは before/live/final/cancelled/unknown"""
    t = re.sub(r"\s+", "", text)
    # 球場名（…）を抽出して除去（全角Ｆ等は半角に正規化）
    venue = ""
    m = re.match(r"^（([^）]*)）", t)
    if m:
        venue = m.group(1).translate(str.maketrans(
            "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))
    label = re.sub(r"^（[^）]*）", "", t)
    if "試合終了" in label:
        return "final", "試合終了", venue, ""
    if "中止" in label or "ノーゲーム" in label:
        return "cancelled", "中止", venue, ""
    if re.search(r"\d+回(表|裏)", label) or "試合中" in label:
        return "live", label or "試合中", venue, ""
    tm = re.match(r"^(\d{1,2}:\d{2})$", label)
    if tm:
        return "before", tm.group(1) + " 開始予定", venue, tm.group(1)
    if label == "" or "試合前" in label:
        return "before", "試合前", venue, ""
    return "unknown", label, venue, ""


def main() -> int:
    today = datetime.now(JST).strftime("%Y-%m-%d")
    today_compact = datetime.now(JST).strftime("%m%d")

    r = requests.get(URL, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    # r.text はエンコーディング誤判定で文字化けすることがあるため bytes を渡す
    # （BeautifulSoupがmeta charsetから正しく判定する）
    soup = BeautifulSoup(r.content, "html.parser")

    games = []
    for box in soup.select(".score_box"):
        cls = box.get("class") or []
        if "date" in cls:
            continue
        a = box.find("a")
        href = a.get("href", "") if a else ""
        # 当日分だけ（hrefに /scores/2026/0612/ の形式で日付が入る）
        if f"/{YEAR}/{today_compact}/" not in href:
            continue
        left = box.select_one("img.logo_left")
        right = box.select_one("img.logo_right")
        state_el = box.select_one(".state")
        score_el = box.select_one(".score")
        if not (left and right and state_el):
            continue
        home = FULL_TO_SHORT.get((left.get("alt") or "").strip())
        away = FULL_TO_SHORT.get((right.get("alt") or "").strip())
        if not (home and away):
            continue
        status, label, venue, start = classify_state(state_el.get_text(" ", strip=True))
        g = {"home": home, "away": away, "status": status, "label": label}
        if venue:
            g["venue"] = venue
        if start:
            g["start"] = start
        if score_el:
            m = re.match(r"^(\d+)\s*-\s*(\d+)$", score_el.get_text(strip=True))
            if m:
                g["score_home"] = int(m.group(1))
                g["score_away"] = int(m.group(2))
        games.append(g)

    out = {
        "date": today,
        "updated_at": datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "games": games,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"[ok] live.json: {today} {len(games)}試合")
    for g in games:
        print(" ", g)
    return 0


if __name__ == "__main__":
    sys.exit(main())
