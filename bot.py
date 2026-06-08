import json
import time
import logging
import os

import requests
import feedparser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("job-alert")

SEEN_FILE = "seen.json"
TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"


def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    # keep the file from growing forever
    trimmed = list(seen)[-5000:]
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f)


def fetch_items(rss_url):
    resp = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    resp.raise_for_status()
    return feedparser.parse(resp.content).entries


def matches(entry, includes, excludes):
    tags = " ".join(t.get("term", "") for t in entry.get("tags", []))
    blob = (entry.get("title", "") + " " + entry.get("summary", "") + " " + tags).lower()
    if any(x in blob for x in excludes):
        return False
    return any(k in blob for k in includes)


def send_telegram(token, chat_id, text):
    requests.post(
        TELEGRAM_URL.format(token=token),
        data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=15,
    ).raise_for_status()


REPOS = {
    "scraper": ("a monitoring bot that scrapes a source and sends instant alerts",
                "https://github.com/Qwirlex/crypto-price-alert-bot"),
    "api": ("a Flask service that connects APIs and forwards events between apps",
            "https://github.com/Qwirlex/webhook-relay"),
    "bot": ("a Telegram alert bot that watches a feed and pings on new matches",
            "https://github.com/Qwirlex/crypto-price-alert-bot"),
}

KINDS = {
    "scraper": "web scrapers",
    "api": "API integrations and automations",
    "bot": "bots and automations",
}


def detect_kind(blob):
    if "scrap" in blob:
        return "scraper"
    if "api" in blob or "webhook" in blob or "integration" in blob:
        return "api"
    return "bot"


def make_proposal(entry):
    blob = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    kind = detect_kind(blob)
    line, repo = REPOS[kind]
    proposal = (
        f"Hi, this is a good fit for me. I build clean Python {KINDS[kind]} and can get this done "
        f"with documented code and a short setup guide, so it is easy to run and hand over. "
        f"I recently built {line}, which is close to what you need. I keep things simple, deliver fast, "
        f"and stay in touch the whole way. You can see similar projects here: {repo}. "
        f"Tell me your exact requirements and I will confirm the timeline and a fixed price."
    )
    return proposal[:1000]


def format_alert(entry):
    title = entry.get("title", "Project")
    link = entry.get("link", "")
    summary = entry.get("summary", "").replace("\n", " ").strip()
    if len(summary) > 200:
        summary = summary[:200] + "..."
    proposal = make_proposal(entry)
    return f"\U0001F4BC <b>{title}</b>\n{summary}\n{link}\n\n\U0001F4DD <b>Proposal:</b>\n{proposal}"


def main():
    config = load_config()
    tg = config["telegram"]
    interval = config.get("poll_interval_seconds", 300)
    rss_url = config.get("rss_url", "https://www.freelancer.com/rss.xml")
    includes = [k.lower() for k in config.get("include_keywords", [])]
    excludes = [k.lower() for k in config.get("exclude_keywords", [])]

    seen = load_seen()
    first_run = len(seen) == 0  # on first run, learn current state without spamming old posts

    log.info("watching %s every %ds (first_run=%s)", rss_url, interval, first_run)
    while True:
        try:
            sent = 0
            for entry in fetch_items(rss_url):
                uid = entry.get("id") or entry.get("link")
                if not uid or uid in seen:
                    continue
                seen.add(uid)
                if first_run:
                    continue
                if matches(entry, includes, excludes):
                    send_telegram(tg["bot_token"], tg["chat_id"], format_alert(entry))
                    sent += 1
                    log.info("alerted: %s", entry.get("title", ""))
            save_seen(seen)
            if first_run:
                log.info("first run: %d posts marked seen, alerts start now", len(seen))
                first_run = False
            elif sent:
                log.info("sent %d alerts", sent)
        except requests.RequestException as e:
            log.error("fetch failed: %s", e)
        except Exception as e:  # keep the loop alive
            log.exception("unexpected error: %s", e)
        time.sleep(interval)


if __name__ == "__main__":
    main()
