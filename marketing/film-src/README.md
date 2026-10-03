# Agent Marketplace film: source

A 120-second 1080p motion film, built entirely in code. Every visual beat, music hit and sound effect is placed from the voice-over's word timings. If you change the script or the voice, run the build again and everything re-syncs.

## Files

| File | What it does |
|---|---|
| `script.json` | Voice-over lines (`text`) and the relative pause before each one (`gap`). |
| `build_vo.py` | Synthesises each line and spreads them over 120 s. Then aligns every word with Whisper and writes `build/cues.json` and `build/cues.js`. |
| `film.html` | The animation: a deterministic `seek(t)` timeline that reads `build/cues.js`. Open it in Chromium and call `seek(42)` to inspect any moment. |
| `music.py` | Original score and sound design, placed from `build/cues.json`. Mixes in the VO with ducking. |
| `render.js` / `stills.js` | Headless Chromium frame renderer, and a renderer for single stills used in QA. |
| `build.sh` | Runs the whole pipeline and writes `build/agent-marketplace-film.mp4` plus a web copy under 30 MB. |

## Voice

- **Sonia (`en-GB-SoniaNeural`)** is used when `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` are set. Use any Azure Speech resource; the free F0 tier is enough.
- Without those variables, it falls back to a local Piper voice. That voice is a placeholder for timing only.

## Run

```bash
pip install numpy scipy faster-whisper piper-tts
npm i playwright          # or set PLAYWRIGHT_PATH to an existing install
export AZURE_SPEECH_KEY=… AZURE_SPEECH_REGION=westeurope
./build.sh                # about 15 minutes with 4 workers
```

## Content rules agreed with stakeholders

- No partner names. Say "partners".
- Use "Every agent", not "Every VP&C agent".
- Show no pilot metrics, scores, winner names or approval times. The current figures are dummy data. The league table is labelled "Illustrative".
- Selection is made by a monthly panel that includes an evaluation agent.
