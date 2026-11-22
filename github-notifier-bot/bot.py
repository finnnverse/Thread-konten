#!/usr/bin/env python3
"""Bot Telegram: notifikasi saat akun GitHub update (push/release/fork) atau bikin repo baru.

Env:
  TELEGRAM_TOKEN  (wajib)  token dari @BotFather
  GITHUB_TOKEN    (opsional) naikkan rate limit GitHub 60 -> 5000 req/jam
  POLL_INTERVAL   (opsional) detik antar cek GitHub, default 120
  STATE_FILE      (opsional) default state.json
"""
import html
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "120"))
STATE_FILE = os.environ.get("STATE_FILE", "state.json")

lock = threading.Lock()
# state = {"users": {"login_lower": {"login": str, "last_event": int, "repos": [str], "chats": [int]}}}
state = {"users": {}}


def load_state():
    global state
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {"users": {}}


def save_state():
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, STATE_FILE)


def http_json(url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, headers=headers or {})
    if data is not None:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def tg(method, **params):
    return http_json(f"https://api.telegram.org/bot{TG_TOKEN}/{method}", data=params, timeout=70)


def send(chat_id, text):
    try:
        tg("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
           disable_web_page_preview=True)
    except Exception as e:
        print("send error:", e)


def gh(path):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "gh-notifier-bot"}
    if GH_TOKEN:
        h["Authorization"] = f"Bearer {GH_TOKEN}"
    return http_json("https://api.github.com" + path, headers=h, timeout=30)


def fetch_snapshot(login):
    events = gh(f"/users/{login}/events/public?per_page=30")
    repos = gh(f"/users/{login}/repos?per_page=100&sort=created&direction=desc")
    return events, repos


def describe_event(ev):
    t, repo = ev["type"], ev["repo"]["name"]
    url = f"https://github.com/{repo}"
    p = ev.get("payload", {})
    if t == "PushEvent":
        commits = p.get("commits", [])
        lines = "\n".join(
            "• " + html.escape(c["message"].splitlines()[0][:80]) for c in commits[-3:]
        )
        branch = p.get("ref", "").replace("refs/heads/", "")
        return (f"🔄 <b>Update</b> di <a href=\"{url}\">{html.escape(repo)}</a> "
                f"({html.escape(branch)}, {p.get('size', len(commits))} commit)\n{lines}")
    if t == "ReleaseEvent":
        r = p.get("release", {})
        return (f"🚀 <b>Release</b> {html.escape(r.get('tag_name', ''))} di "
                f"<a href=\"{r.get('html_url', url)}\">{html.escape(repo)}</a>")
    if t == "ForkEvent":
        return f"🍴 <b>Fork</b> <a href=\"{url}\">{html.escape(repo)}</a>"
    if t == "PublicEvent":
        return f"🌐 <b>Repo dipublikkan</b>: <a href=\"{url}\">{html.escape(repo)}</a>"
    return None


def check_user(key):
    u = state["users"][key]
    events, repos = fetch_snapshot(u["login"])
    msgs = []

    known = set(u["repos"])
    for r in reversed(repos):
        if r["full_name"] not in known:
            desc = f"\n{html.escape(r['description'])}" if r.get("description") else ""
            msgs.append(f"🆕 <b>Repo baru</b>: <a href=\"{r['html_url']}\">"
                        f"{html.escape(r['full_name'])}</a>{desc}")
    u["repos"] = sorted(known | {r["full_name"] for r in repos})

    last = u["last_event"]
    for ev in sorted(events, key=lambda e: int(e["id"])):
        if int(ev["id"]) > last:
            m = describe_event(ev)
            if m:
                msgs.append(m)
    if events:
        u["last_event"] = max(last, max(int(e["id"]) for e in events))

    for m in msgs:
        for chat in u["chats"]:
            send(chat, f"👤 <b>{html.escape(u['login'])}</b>\n{m}")


def poller():
    while True:
        with lock:
            keys = list(state["users"])
        for key in keys:
            try:
                with lock:
                    if key in state["users"]:
                        check_user(key)
                        save_state()
            except urllib.error.HTTPError as e:
                print(f"GitHub error {key}: {e.code}")
                if e.code in (403, 429):
                    time.sleep(60)
            except Exception as e:
                print(f"error {key}: {e}")
            time.sleep(2)
        time.sleep(POLL_INTERVAL)


HELP = (
    "Bot notifikasi GitHub 🔔\n\n"
    "/watch &lt;username&gt; – pantau akun\n"
    "/unwatch &lt;username&gt; – berhenti pantau\n"
    "/list – daftar akun yang dipantau\n\n"
    "Kamu akan dapat notif saat ada repo baru, push, release, atau fork."
)


def handle(msg):
    chat = msg["chat"]["id"]
    parts = (msg.get("text") or "").split()
    if not parts or not parts[0].startswith("/"):
        return
    cmd = parts[0].split("@")[0].lower()
    arg = parts[1].lstrip("@").strip() if len(parts) > 1 else ""

    if cmd in ("/start", "/help"):
        send(chat, HELP)
    elif cmd == "/watch":
        if not arg:
            return send(chat, "Pakai: /watch &lt;username&gt;")
        key = arg.lower()
        with lock:
            if key in state["users"]:
                if chat not in state["users"][key]["chats"]:
                    state["users"][key]["chats"].append(chat)
                save_state()
                return send(chat, f"✅ Sekarang memantau <b>{html.escape(arg)}</b>")
        try:
            events, repos = fetch_snapshot(arg)
        except urllib.error.HTTPError as e:
            return send(chat, "❌ Akun tidak ditemukan." if e.code == 404
                        else f"❌ GitHub error {e.code}")
        login = repos[0]["owner"]["login"] if repos else arg
        with lock:
            state["users"][key] = {
                "login": login,
                "last_event": max((int(e["id"]) for e in events), default=0),
                "repos": [r["full_name"] for r in repos],
                "chats": [chat],
            }
            save_state()
        send(chat, f"✅ Sekarang memantau <b>{html.escape(login)}</b> "
                   f"({len(repos)} repo saat ini).")
    elif cmd == "/unwatch":
        key = arg.lower()
        with lock:
            u = state["users"].get(key)
            if not u or chat not in u["chats"]:
                return send(chat, "Akun itu tidak ada di daftarmu.")
            u["chats"].remove(chat)
            if not u["chats"]:
                del state["users"][key]
            save_state()
        send(chat, f"🛑 Berhenti memantau <b>{html.escape(arg)}</b>")
    elif cmd == "/list":
        with lock:
            mine = [u["login"] for u in state["users"].values() if chat in u["chats"]]
        send(chat, "Dipantau:\n" + "\n".join(f"• {html.escape(n)}" for n in mine)
             if mine else "Belum ada. Pakai /watch &lt;username&gt;")


def main():
    if not TG_TOKEN:
        raise SystemExit("Set TELEGRAM_TOKEN dulu.")
    load_state()
    threading.Thread(target=poller, daemon=True).start()
    offset = 0
    print("Bot jalan...")
    while True:
        try:
            for upd in tg("getUpdates", offset=offset, timeout=50).get("result", []):
                offset = upd["update_id"] + 1
                if "message" in upd:
                    handle(upd["message"])
        except Exception as e:
            print("poll error:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
