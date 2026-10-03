"""Synthesise the voice-over, align words, and lay the lines out on the 120 s timeline.

Engine (first that works):
  * Azure Speech (en-GB-SoniaNeural) when AZURE_SPEECH_KEY and AZURE_SPEECH_REGION are set (licensed).
  * edge-tts: the same Sonia voice via Microsoft Edge's free read-aloud service (unofficial, no SLA).
  * A local Piper voice (placeholder only).

Outputs (in build/): vo/<id>.wav, cues.json, cues.js (window.CUES for film.html).
"""
import difflib
import json
import os
import re
import subprocess
import sys
import urllib.request
import wave
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).parent
BUILD = HERE / 'build'
VO = BUILD / 'vo'
TOTAL = 120.0
LEAD_IN = 1.0          # silence before the first line
OUTRO_HOLD = 6.5       # music-only tail after the last line
SONIA = 'en-GB-SoniaNeural'

# Spoken forms for on-screen words that TTS engines mis-read.
SAY = {'A.I.': 'AI'}


def azure_tts(text, out):
    key, region = os.environ['AZURE_SPEECH_KEY'], os.environ['AZURE_SPEECH_REGION']
    ssml = (f"<speak version='1.0' xml:lang='en-GB' xmlns='http://www.w3.org/2001/10/synthesis'>"
            f"<voice name='{SONIA}'><prosody rate='-4%'>{escape(text)}</prosody></voice></speak>")
    req = urllib.request.Request(
        f'https://{region}.tts.speech.microsoft.com/cognitiveservices/v1', data=ssml.encode(),
        headers={'Ocp-Apim-Subscription-Key': key, 'Content-Type': 'application/ssml+xml',
                 'X-Microsoft-OutputFormat': 'riff-48khz-16bit-mono-pcm', 'User-Agent': 'agent-marketplace-film'})
    with urllib.request.urlopen(req, timeout=60) as r:
        out.write_bytes(r.read())


def edge_tts_synth(text, out):
    import asyncio
    import certifi
    import edge_tts
    # edge-tts trusts only certifi's bundle; behind a TLS-inspecting proxy add its CA too.
    extra = os.environ.get('SSL_CERT_FILE') or ('/root/.ccr/ca-bundle.crt' if Path('/root/.ccr/ca-bundle.crt').exists() else None)
    if extra:
        bundle = BUILD / 'ca-bundle.pem'
        bundle.write_text(Path(certifi.where()).read_text() + '\n' + Path(extra).read_text())
        certifi.where = lambda: str(bundle)
        import edge_tts.communicate as ec
        if hasattr(ec, 'certifi'):
            ec.certifi.where = certifi.where
        if hasattr(ec, '_SSL_CTX'):
            import ssl
            ec._SSL_CTX = ssl.create_default_context(cafile=str(bundle))
    mp3 = out.with_suffix('.mp3')
    asyncio.run(edge_tts.Communicate(text, SONIA, rate='-4%').save(str(mp3)))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp3), '-ar', '48000', '-ac', '1', str(out)], check=True)
    mp3.unlink()


def piper_tts(text, out):
    model = HERE / 'voices' / 'en_GB-cori-high.onnx'
    if not model.exists():
        model.parent.mkdir(exist_ok=True)
        base = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/high/en_GB-cori-high.onnx'
        for suffix in ('', '.json'):
            urllib.request.urlretrieve(base + suffix, str(model) + suffix)
    subprocess.run(['piper', '-m', str(model), '--length-scale', '0.98', '--sentence-silence', '0.28', '-f', str(out)],
                   input=text.encode(), check=True, capture_output=True)


def duration(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def norm(w):
    return re.sub(r'[^a-z0-9]', '', w.lower())


def align(model, wav, script_words):
    """Return a start time (s, relative to the clip) for every script word."""
    segs, _ = model.transcribe(str(wav), word_timestamps=True, language='en')
    heard = [(norm(w.word), w.start) for s in segs for w in s.words]
    want = [norm(w) for w in script_words]
    sm = difflib.SequenceMatcher(a=want, b=[h[0] for h in heard], autojunk=False)
    times = [None] * len(want)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            times[a + k] = heard[b + k][1]
    # fill gaps by interpolation between known neighbours
    known = [(i, t) for i, t in enumerate(times) if t is not None]
    if not known:
        return [i * 0.3 for i in range(len(want))]
    for i in range(len(times)):
        if times[i] is None:
            prev = max((k for k in known if k[0] < i), default=None, key=lambda k: k[0])
            nxt = min((k for k in known if k[0] > i), default=None, key=lambda k: k[0])
            if prev and nxt:
                times[i] = prev[1] + (nxt[1] - prev[1]) * (i - prev[0]) / (nxt[0] - prev[0])
            elif prev:
                times[i] = prev[1] + 0.3 * (i - prev[0])
            else:
                times[i] = max(0.0, nxt[1] - 0.3 * (nxt[0] - i))
    return [round(t, 3) for t in times]


def main():
    VO.mkdir(parents=True, exist_ok=True)
    if os.environ.get('AZURE_SPEECH_KEY') and os.environ.get('AZURE_SPEECH_REGION'):
        engine = 'azure'
    else:
        engine = 'piper'
        try:
            edge_tts_synth('Test.', VO / '_probe.wav'); (VO / '_probe.wav').unlink(); engine = 'edge'
        except Exception as e:  # noqa: BLE001 — any failure means fall back
            print('edge-tts unavailable:', e, file=sys.stderr)
    print('voice engine:', engine, file=sys.stderr)
    synth = {'azure': azure_tts, 'edge': edge_tts_synth, 'piper': piper_tts}[engine]
    lines = json.loads((HERE / 'script.json').read_text())
    for l in lines:
        spoken = l['text']
        for a, b in SAY.items():
            spoken = spoken.replace(a, b)
        out = VO / f"{l['id']}.wav"
        synth(spoken, out)
        l['dur'] = round(duration(out), 3)

    # lay out: lead-in, then each line after its gap; stretch gaps to fill the timeline
    speech = sum(l['dur'] for l in lines)
    base_gaps = sum(l['gap'] for l in lines[1:])
    room = TOTAL - LEAD_IN - OUTRO_HOLD - speech
    if room < base_gaps * 0.7:
        sys.exit(f'Script too long: {speech:.1f}s of speech leaves {room:.1f}s for gaps')
    k = room / base_gaps
    t = LEAD_IN
    for i, l in enumerate(lines):
        if i:
            t += l['gap'] * k
        l['t'] = round(t, 3)
        t += l['dur']

    from faster_whisper import WhisperModel
    model = WhisperModel('small.en', device='cpu', compute_type='int8')
    for l in lines:
        rel = align(model, VO / f"{l['id']}.wav", l['text'].split())
        l['words'] = [round(l['t'] + r, 3) for r in rel]

    cues = {'engine': engine, 'lines': {l['id']: {'t': l['t'], 'dur': l['dur'], 'end': round(l['t'] + l['dur'], 3),
                                                  'text': l['text'], 'words': l['words']} for l in lines}}
    (BUILD / 'cues.json').write_text(json.dumps(cues, indent=1))
    (BUILD / 'cues.js').write_text('window.CUES=' + json.dumps(cues) + ';')
    for l in lines:
        print(f"{l['id']:9s} {l['t']:7.2f} → {l['t'] + l['dur']:7.2f}", file=sys.stderr)


if __name__ == '__main__':
    main()
