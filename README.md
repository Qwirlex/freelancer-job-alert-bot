# Freelancer Job Alert Bot

A Telegram bot that watches the Freelancer.com feed and pings you the moment a new project matches your skills. Getting in early on a fresh post is half the battle, so this lets you see and bid on the right jobs before the crowd shows up.

Built with Python. It reads the public Freelancer RSS feed, so there is no account or API key needed for the source.

## What it does

- Polls the Freelancer.com project feed on an interval you set
- Keeps only the posts that match your keywords and drops the ones you do not want
- Sends each match to your Telegram with the title, a short summary, and a direct link
- Remembers what it has already seen, so you never get the same job twice
- On the first run it learns the current posts quietly, then only alerts on new ones after that

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Get your chat id from [@userinfobot](https://t.me/userinfobot).
3. Open `config.json` and fill in your token and chat id. The `config.json` here only has placeholders, so keep your real token to yourself and do not commit it back.
4. Tune `include_keywords` and `exclude_keywords` to fit the work you want.

## Run

```
pip install -r requirements.txt
python bot.py
```

Leave it running and it checks for new jobs on the interval you set.

## Run with Docker

```
docker build -t job-alert-bot .
docker run -d --restart always job-alert-bot
```

## Config notes

- `include_keywords`: a job is kept if its title, summary, or skills contain any of these.
- `exclude_keywords`: a job is dropped if it contains any of these, even if it matched an include word. Good for filtering out work you do not do.
- `poll_interval_seconds`: how often to check. 300 (five minutes) is a sensible start.
