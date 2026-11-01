# Bámi-Sọ̀rọ̀ — Yorùbá Speech-to-Text

A speech recognition and translation platform for Yorùbá, built to handle the part most ASR systems skip: **tone marks**. Yorùbá is tonal — *ọwọ́* (hand), *ọwọ* (broom), and *ọ̀wọ̀* (respect) are different words — so a transcript that drops diacritics is only partly correct.

## What it does

- **Speech-to-text** — record up to 60 seconds in the browser and get a written transcript
- **Tone restoration** — diacritics and tone marks are restored on the output, not stripped
- **Translation** — move between Yorùbá and English
- **Text-to-speech** — play a transcript back as audio
- **Accounts** — sign-up and login, so history is tied to a user
- **History** — every transcription is saved and can be revisited

## Architecture

| Layer | Stack |
| :--- | :--- |
| Frontend | Next.js · React · TypeScript · Tailwind CSS |
| Backend | FastAPI · SQLAlchemy (async) · Pydantic |
| Speech model | W2V-BERT (fine-tuned) via PyTorch + Transformers |
| Hosted ASR / translation | OpenAI transcription + GPT models |
| Speech synthesis | `edge-tts` · `gTTS` |
| Database | PostgreSQL (Neon) via `asyncpg` |
| Auth | JWT (`PyJWT`) + `bcrypt` |

Audio is handled in two paths: a local W2V-BERT model for offline inference, and a hosted transcription path for accuracy on longer clips. The backend picks the path per request rather than forcing one model on every case.

## Running locally

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in the values
uvicorn main:app --reload
```

`requirements.txt` pulls the full ML stack, including `torch`. If you only need the hosted transcription path and want a fast install, use `requirements-host.txt` instead — that is what the Render service builds with. The first run with the full requirements downloads the local model weights, which is a few hundred MB; `torch` will use CUDA automatically if it is available.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

On Windows there are helper scripts at the repository root — `start-all.bat` or `start-all.ps1` — that launch both servers together.

## Configuration

Copy `.env.example` and set the values it lists. The essentials are the database URL, a JWT signing secret, and the API key for the hosted transcription service. No secrets are committed to this repository.

## Deployment

The repository ships both deployment configs:

- `render.yaml` — backend service on Render
- `vercel.json` — frontend on Vercel

## Status

The hosted demo is currently offline while it's being redeployed. To run it, follow the local setup above.

## License

© 2026 Samuel Ogundare. All rights reserved. No permission is granted to copy, modify, redistribute, or deploy this code without written permission.
