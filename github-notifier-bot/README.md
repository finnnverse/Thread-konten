# GitHub Notifier Bot (Telegram)

Notifikasi Telegram saat akun GitHub yang dipantau **bikin repo baru**, **push**, **release**, atau **fork**.

## Setup
1. Buat bot lewat [@BotFather](https://t.me/BotFather), ambil token.
2. (Opsional) buat GitHub personal access token (tanpa scope pun cukup) agar rate limit lebih besar.
3. Jalankan (butuh Python 3.8+, tanpa dependensi):

```bash
export TELEGRAM_TOKEN=123:abc
export GITHUB_TOKEN=ghp_xxx      # opsional
export POLL_INTERVAL=120         # opsional, detik
python3 bot.py
```

## Perintah
- `/watch <username>` – mulai pantau (data awal jadi baseline, tidak spam)
- `/unwatch <username>` – berhenti
- `/list` – daftar pantauan

Status disimpan di `state.json`. Bot hanya bisa melihat aktivitas **publik**; event GitHub bisa tertunda beberapa menit.
