"""Original score + sound design for the Agent Marketplace film.

Every section change, hit and sound effect is placed from build/cues.json,
so the music re-fits automatically when the voice-over changes."""
import json, wave
import numpy as np
from scipy import signal

SR = 48000
DUR = 120.0
N = int(SR * DUR)
rng = np.random.default_rng(42)
BEAT = 0.5


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def note(name):
    names = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
    n, o = name[:-1], int(name[-1])
    return names[n] + 12 * (o + 1)


class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2))

    def add(self, t, sig, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i >= N:
            return
        if sig.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l, sig * r], 1) * 1.414
        j = min(N, i + len(sig))
        if i < 0:
            sig = sig[-i:]
            i = 0
        self.x[i:j] += sig[:j - i] * gain


def env_adsr(n, a, d, s, r, sr=SR):
    a, d, r = int(a * sr), int(d * sr), int(r * sr)
    sus = max(0, n - a - d - r)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False), np.linspace(1, s, d, endpoint=False), np.full(sus, s), np.linspace(s, 0, r)])
    return e[:n] if len(e) >= n else np.pad(e, (0, n - len(e)))


def saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + phase) % 1.0) - 1


def lp(x, fc, order=2):
    sos = signal.butter(order, min(fc, SR * 0.45), 'low', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def hp(x, fc, order=2):
    sos = signal.butter(order, fc, 'high', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], 'band', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def sweep_lp(x, f0, f1):
    """Time-varying lowpass via chunked filtering (cheap and smooth enough)."""
    out = np.zeros_like(x)
    chunks = 64
    L = len(x)
    zi = None
    for c in range(chunks):
        a, b = c * L // chunks, (c + 1) * L // chunks
        fc = f0 * (f1 / f0) ** (c / (chunks - 1))
        sos = signal.butter(2, min(fc, SR * .45), 'low', fs=SR, output='sos')
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[a:b], zi = signal.sosfilt(sos, x[a:b], zi=zi)
    return out


# ---------------- instruments ----------------
def pad(notes, dur, cutoff=1800, att=1.2, rel=1.8, bright=1.0):
    n = int((dur + rel) * SR)
    L = np.zeros(n); R = np.zeros(n)
    for m in notes:
        f = mtof(m)
        for k, det in enumerate([-0.11, 0.0, 0.12]):
            ph = rng.random()
            s = saw(f * 2 ** (det / 12), n, ph)
            if k == 0: L += s
            elif k == 2: R += s
            else: L += s * .7; R += s * .7
    x = np.stack([L, R], 1) / (len(notes) * 2.5)
    x = lp(x, cutoff * bright, 2)
    e = env_adsr(n, att, 0.5, 0.85, rel)
    return x * e[:, None]


def pluck(m, dur=0.4, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    s = sum((0.6 ** h) * np.sin(2 * np.pi * f * (h + 1) * t) * np.exp(-t * (6 + h * 4) / bright) for h in range(5))
    att = np.minimum(1, t / 0.003)
    return s * att * 0.5


def bell(m, dur=2.5):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 1.6) + .4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3) + .2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 5)
    return s * np.minimum(1, t / .002) * .45


def kick(level=1.0):
    n = int(.45 * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7.5)
    click = rng.standard_normal(n) * np.exp(-t * 400) * .25
    return np.tanh((s + click) * 1.6) * level


def clap():
    n = int(.35 * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    e = np.zeros(n)
    for d in [0, .011, .022]:
        e += np.where(t >= d, np.exp(-(t - d) * 60), 0)
    e += np.exp(-t * 14) * .4
    return bp(nz * e, 900, 5000) * .9


def hat(op=False):
    n = int((.25 if op else .06) * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t * (14 if op else 70)) * .35


def snare():
    n = int(.25 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * .5
    return (body + bp(rng.standard_normal(n), 1500, 8000) * np.exp(-t * 22)) * .6


def tom(f0=90):
    n = int(1.2 * SR); t = np.arange(n) / SR
    f = f0 * (1 + .6 * np.exp(-t * 12))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2) * 1.0


def impact(size=1.0):
    n = int(4.0 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 8)) / SR) * np.exp(-t * 1.4)
    crash = hp(rng.standard_normal(n), 3000) * np.exp(-t * 1.3) * .25
    body = lp(rng.standard_normal(n), 400) * np.exp(-t * 6) * .6
    return np.tanh((boom * 1.2 + crash + body) * 1.3) * size


def riser(dur, f0=300, f1=9000):
    n = int(dur * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    x = sweep_lp(nz, f0, f1) * (t / dur) ** 2.2
    tone = np.sin(2 * np.pi * np.cumsum(200 * 2 ** (2.5 * t / dur)) / SR) * (t / dur) ** 3 * .25
    return (x * .55 + tone)


def whoosh(dur=.8, lo=400, hi=4000):
    n = int(dur * SR); t = np.arange(n) / SR
    e = np.sin(np.pi * t / dur) ** 2
    x = sweep_lp(rng.standard_normal(n), lo, hi) * e
    return hp(x, 150) * .5


def blip(f=1200, dur=.09, level=.35):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t * (1 + .5 * np.exp(-t * 40))) * np.exp(-t * 45) * level


def click():
    n = int(.03 * SR); t = np.arange(n) / SR
    return (hp(rng.standard_normal(n), 2000) * np.exp(-t * 300) * .5 + np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 200) * .3)


def type_tick():
    n = int(.025 * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 2000, 7000) * np.exp(-t * 350) * .35


def chime(notes, gap=.07):
    out = np.zeros(int((len(notes) * gap + 1.5) * SR))
    for i, m in enumerate(notes):
        b = bell(m, 1.4) * .6; s = int(i * gap * SR); out[s:s + len(b)] += b
    return out


def reverb(x, secs=2.6, wet=.28):
    n = int(secs * SR); t = np.arange(n) / SR
    out = np.zeros_like(x)
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / secs)
        ir = lp(ir, 6000); ir[:int(.012 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum())
        out[:, c] = signal.fftconvolve(x[:, c], ir)[:len(x)]
    return x * (1 - wet) + out * wet * 2.2


# ---------------- arrangement ----------------
music = Bus(); drums = Bus(); sfx = Bus()
CH = {  # chord tones (midi)
    'Am': ['A2', 'C3', 'E3', 'A3'], 'F': ['F2', 'A2', 'C3', 'F3'], 'C': ['C3', 'E3', 'G3', 'C4'], 'G': ['G2', 'B2', 'D3', 'G3'],
    'Em': ['E2', 'G2', 'B2', 'E3'], 'Dm': ['D3', 'F3', 'A3', 'D4'],
}
CH = {k: [note(n) for n in v] for k, v in CH.items()}
ROOT = {'Am': note('A1'), 'F': note('F1'), 'C': note('C2'), 'G': note('G1'), 'Em': note('E1'), 'Dm': note('D2')}


def chords_at(seq, t0, bar_len, until):
    out = []; t = t0; i = 0
    while t < until - 1e-6:
        out.append((t, min(bar_len, until - t), seq[i % len(seq)])); t += bar_len; i += 1
    return out



seqB = ['C', 'G', 'Am', 'F']


def groove(t0, t1, kick_on=True, clap_from=None, energy=1.0, cut=2600):
    for (t, d, c) in chords_at(seqB, t0, 4.0, t1):
        music.add(t, pad(CH[c], d, cutoff=cut * energy, att=.3, rel=1.0), .55)
        bn = int(BEAT / 2 * SR)
        for k in range(int(d / (BEAT / 2))):
            tt = t + k * BEAT / 2
            f = mtof(ROOT[c] + (12 if k % 4 == 2 else 0))
            s = (np.sign(np.sin(2 * np.pi * f * np.arange(bn) / SR)) * .3 + np.sin(2 * np.pi * f * np.arange(bn) / SR)) * env_adsr(bn, .005, .1, .6, .08)
            music.add(tt, lp(s, 500) * .55)
        arp = [CH[c][i] + 12 for i in (0, 2, 1, 3, 2, 1, 3, 0)]
        for k in range(int(d / .125)):
            music.add(t + k * .125, pluck(arp[k % 8] + (12 if k % 16 >= 12 else 0), .3, bright=energy), .2 * energy, pan=.4 * np.sin(k * .7))
    for b in range(int(round(t0 / BEAT)), int(round(t1 / BEAT))):
        tb = b * BEAT
        if kick_on: drums.add(tb, kick(.9), .85)
        drums.add(tb + .25, hat(b % 4 == 3), .45 * energy)
        if clap_from is not None and tb >= clap_from and b % 2: drums.add(tb, clap(), .45)

# ---------------- cues ----------------
from pathlib import Path
BUILD = Path(__file__).parent / 'build'
LINES = json.loads((BUILD / 'cues.json').read_text())['lines']
ORDER = list(LINES)


def nz(s):
    return ''.join(ch for ch in s.lower() if ch.isalnum())


def at(lid, word, n=0):
    c = 0
    for w, t in zip(LINES[lid]['text'].split(), LINES[lid]['words']):
        if nz(w).startswith(nz(word)):
            if c == n:
                return t
            c += 1
    raise KeyError(f'{lid}:{word}')


def ls(lid): return LINES[lid]['t']
def le(lid): return LINES[lid]['end']


def S0(lid):
    i = ORDER.index(lid)
    if i == 0: return 0.0
    gap = ls(lid) - le(ORDER[i - 1])
    return ls(lid) - min(1.0, gap * .55)


T_LIGHT, T_DARK, T_RED = S0('intro'), S0('cycle'), S0('outro')

# ---------------- 1 · imagine (dark, intimate) ----------------
music.add(0.0, pad(CH['Am'][:3], T_LIGHT + .5, cutoff=800, att=2.0, rel=2.0), .9)
music.add(0, np.sin(2 * np.pi * mtof(note('A1')) * np.arange(int(T_LIGHT * SR)) / SR) * env_adsr(int(T_LIGHT * SR), 1.5, .5, 1, 1.0) * .35)
for w, m in [('Imagine', 'E5'), ('App', 'A5'), ('AI', 'C6'), ('Built', 'E6'), ('people', 'B5')]:
    music.add(at('imagine', w), bell(note(m)), .4, pan=rng.uniform(-.6, .6))
tA = at('imagine', 'App')
for k in range(int((T_LIGHT - tA) / .125)):  # sparkling arp as the tiles bloom
    music.add(tA + k * .125, pluck([note(x) for x in ['A4', 'C5', 'E5', 'A5']][k % 4] + 12 * (k % 8 == 7), .3), .14, pan=.4 * np.sin(k))
drums.add(T_LIGHT - 2.0, riser(2.0, 300, 9000), .6)
drums.add(T_LIGHT - .6, impact(.9)[::-1][-int(.6 * SR):], .4)

# ---------------- 2–9 · marketplace chapters (light, uplifting groove) ----------------
drums.add(T_LIGHT, impact(1.0), 1.0)
music.add(T_LIGHT, chime([note(m) for m in ['C5', 'E5', 'G5', 'C6', 'E6']], .06), .45)
groove(T_LIGHT, S0('share'), kick_on=False, energy=.85)
groove(S0('share'), S0('league'), kick_on=True, clap_from=S0('discover'))
drums.add(S0('league') - 1.5, riser(1.5, 400, 8000), .4)
groove(S0('league'), S0('panel'), kick_on=True, clap_from=S0('league'), energy=1.1)
groove(S0('panel'), S0('winners'), kick_on=False, energy=.75, cut=1900)   # thoughtful breakdown
drums.add(S0('winners') - 2.0, riser(2.0, 300, 11000), .6)
for k in range(16):
    drums.add(S0('winners') - 1.0 + k * .0625, snare(), .12 + .3 * k / 16)
tW = at('winners', 'Winners')
drums.add(tW, impact(.85), .85)
music.add(tW, chime([note(m) for m in ['G5', 'C6', 'E6', 'G6']], .07), .45)
groove(S0('winners'), S0('govern'), kick_on=True, clap_from=S0('winners'), energy=1.1)
groove(S0('govern'), T_DARK, kick_on=True, clap_from=None, energy=.9)
drums.add(T_DARK - 1.6, riser(1.6, 300, 9000), .55)

# ---------------- 10–12 · cycle, benefits, combine (dark, epic half-time) ----------------
drums.add(T_DARK, impact(1.0), 1.0)
for (t, d, c) in chords_at(['Am', 'F', 'C', 'G'], T_DARK, 2.5, T_RED):
    music.add(t, pad(CH[c] + [CH[c][0] + 24], d, cutoff=2200, att=.2, rel=1.2), .7)
    music.add(t, np.sin(2 * np.pi * mtof(ROOT[c]) * np.arange(int(d * SR)) / SR) * env_adsr(int(d * SR), .02, .3, .85, .3) * .55)
for b in range(int(T_DARK / BEAT), int((T_RED - 1.0) / BEAT)):
    tb = b * BEAT
    if b % 4 == 0: drums.add(tb, kick(1.0), .9)
    if b % 4 == 2: drums.add(tb, snare(), .55)
    drums.add(tb + .25, hat(), .3)
for w in ['Share', 'Experiment', 'Improve', 'Scale']:            # a hit on every cycle word
    t = at('cycle', w); drums.add(t, tom(70 + 12 * ['Share', 'Experiment', 'Improve', 'Scale'].index(w)), .8); drums.add(t, impact(.35), .3)
for w in ['ideation', 'fluency', 'learn']:
    drums.add(at('fluency', w), tom(110), .5)
tP = at('combine', 'participation')
for k in range(48):                                              # ideas multiplying: rising glitter
    music.add(tP - .4 + (k / 48) ** .7 * 2.6, bell(note(['C6', 'E6', 'G6', 'A6', 'D6'][k % 5]), .8), .05 + .06 * k / 48, pan=rng.uniform(-.8, .8))
drums.add(T_RED - 3.0, riser(3.0, 200, 12000), .75)
for k in range(24):
    drums.add(T_RED - 1.5 + k * .0625, snare(), .1 + .35 * k / 24)

# ---------------- 13 · outro (red, resolve) ----------------
drums.add(T_RED, impact(1.1), 1.0)
big = [note(n) for n in ['C2', 'C3', 'G3', 'C4', 'E4', 'G4']]
music.add(T_RED, pad(big, 6.0, cutoff=3000, att=.05, rel=4.0), .8)
music.add(T_RED, chime([note(m) for m in ['C5', 'E5', 'G5', 'C6', 'E6', 'G6']], .08), .5)
for k in range(int(5.0 / .125)):
    music.add(T_RED + k * .125, pluck([note('C5'), note('G5'), note('E5'), note('C6')][k % 4], .35), .16 * (1 - k / 40), pan=.4 * np.sin(k))
for b in range(int(T_RED / BEAT), int((T_RED + 4.0) / BEAT)):
    drums.add(b * BEAT, kick(.8), .7); drums.add(b * BEAT + .25, hat(), .35)
tend = le('outro')
music.add(tend - 1.5, pad([note(n) for n in ['F2', 'A3', 'C4', 'F4']], 2.5, cutoff=2000, att=1.0, rel=2.0), .7)
music.add(tend + .8, pad([note(n) for n in ['C2', 'G2', 'E3', 'G3', 'C4', 'E4']], 120 - tend - 2.5, cutoff=2200, att=1.0, rel=2.5), 1.1)
music.add(tend + .8, np.sin(2 * np.pi * mtof(note('C1')) * np.arange(int((119 - tend) * SR)) / SR) * env_adsr(int((119 - tend) * SR), 1, .5, 1, 2.5) * .5)
for i, m in enumerate(['G5', 'C6', 'E6', 'G6']):
    music.add(tend + .8 + i * .9, bell(note(m), 3.5), .3, pan=rng.uniform(-.5, .5))

# ---------------- sound design ----------------
for lid in ORDER[1:]:                                            # a whoosh into every chapter
    sfx.add(S0(lid) - .35, whoosh(.7, 500, 5000), .35, pan=rng.uniform(-.5, .5))
tt0 = at('imagine', 'App') - .35
for k in range(14):
    sfx.add(tt0 + k * .06, blip(rng.uniform(700, 1300), .07, .14), 1, pan=rng.uniform(-.8, .8))
tB = at('imagine', 'Built')
for k in range(10):
    sfx.add(tB + .05 + k * .07, click(), .25, pan=rng.uniform(-.7, .7))       # tiles flipping
# share: typing, submit click, platform clicks
tS = at('share', 'submit'); txt = 'Auto-triage small purchase requests'
for i in range(len(txt)): sfx.add(tS - .1 + i * 1.3 / len(txt) + rng.uniform(-.008, .008), type_tick(), .55, pan=.25)
sfx.add(tS + 1.55, click(), .7); sfx.add(tS + 1.65, chime([note('C6'), note('G6')], .05), .25)
for w in ['Copilot', 'partners', 'own']: sfx.add(at('share', w), click(), .6); sfx.add(at('share', w), blip(1000, .08, .18), 1)
for i in range(6): sfx.add(at('share', 'any') + i * .09, blip(800 + i * 90, .06, .12), 1, pan=-.5 + i * .2)
# discover: typing, matching, results
tD, tC, tF, tR = at('discover', 'describe'), at('discover', 'concierge'), at('discover', 'finds'), at('discover', 'right')
txt = 'Chase my overdue purchase orders'
for i in range(len(txt)): sfx.add(tD - .3 + i * (tC - .2 - tD) / len(txt) + rng.uniform(-.008, .008), type_tick(), .55, pan=.2)
sfx.add(tC - .3, click(), .6)
for k in range(3): sfx.add(tF - .05 + k * .2, blip(rng.uniform(900, 1300), .08, .2), 1, pan=-.4 + k * .4)
sfx.add(tR, chime([note('E6'), note('A6')], .05), .25)
# try / rate / improve
sfx.add(at('try', 'Try'), blip(700, .1, .2), 1)
for k in range(5): sfx.add(at('try', 'Rate') + k * .15, blip(1200 + k * 150, .07, .18), 1, pan=-.4 + k * .2)
sfx.add(at('try', 'Innovation'), chime([note('C6'), note('E6'), note('G6')], .06), .3)
# league: rows climbing
for k in range(6): sfx.add(at('league', 'rise') + k * .15, blip(600 + k * 120, .06, .15), 1)
sfx.add(at('league', 'visibility'), chime([note('G6'), note('C7')], .05), .2)
# panel
for k in range(4): sfx.add(at('panel', 'panel') + k * .12, blip(700 + k * 100, .07, .16), 1)
sfx.add(at('panel', 'evaluation'), chime([note('E6'), note('B6')], .05), .25)
sfx.add(at('panel', 'management'), tom(120) * .5, .4)
# winners: confetti sparkle, function nodes
sp = np.zeros(int(2.5 * SR))
for k in range(60):
    b = blip(rng.uniform(2500, 6000), .05, .08); s = int(rng.uniform(0, 1.8) * SR); sp[s:s + len(b)] += b
sfx.add(at('winners', 'awards'), sp, 1)
for k in range(6): sfx.add(at('winners', 'entire') - .1 + k * .12 + .4, blip(900 + k * 80, .06, .14), 1, pan=-.6 + k * .24)
# governance
sfx.add(at('govern', 'Restricted'), tom(110) * .5, .5)
sfx.add(at('govern', 'protected') - .15, click(), .9); sfx.add(at('govern', 'protected') - .15, blip(300, .12, .3), 1)
for w in ['access', 'workflow']: sfx.add(at('govern', w), blip(900, .08, .2), 1)
sfx.add(at('govern', 'rest') - .1, chime([note('D6'), note('G6'), note('B6')], .06), .35)
# ---------------- mix ----------------
mus = reverb(music.x, 2.8, .30)
drm = reverb(drums.x, 1.4, .12)
fx = reverb(sfx.x, 1.8, .22)
bed = mus * .8 + drm * .9
# master fade-in / out
tt = np.arange(N) / SR
bed *= np.minimum(1, tt / .3)[:, None] * np.clip((120 - tt) / 1.6, 0, 1)[:, None]

# voice-over track
vo = np.zeros(N)
for lid, l in LINES.items():
    w = wave.open(str(BUILD / 'vo' / f'{lid}.wav')); sr = w.getframerate()
    d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
    if sr != SR:
        d = signal.resample_poly(d, SR, sr)
    i = int(l['t'] * SR); vo[i:i + len(d)] += d[:N - i]
vo = hp(vo, 90)
# gentle presence + compression
vo = vo + bp(vo, 2500, 6000) * .25
envv = np.sqrt(lp(vo ** 2, 20, 1).clip(0))
g = np.minimum(1, (0.08 / (envv + 1e-6)) ** 0.35)
vo = vo * np.where(envv > .08, g, 1)
vo = vo / np.abs(vo).max() * .9
vo2 = np.stack([vo, vo], 1)
vo2 = reverb(vo2, 1.0, .06)

# ducking from VO envelope
ve = np.sqrt(lp(vo ** 2, 6, 1).clip(0)); ve = ve / ve.max()
duck = 1 - .5 * np.clip(ve * 4, 0, 1)
duck = lp(duck, 4, 1)
bed = bed / np.abs(bed).max()
bed = np.tanh(bed * 2.4) / np.tanh(2.4)
fx = fx / max(1e-6, np.abs(fx).max())
mix = vo2 * 1.0 + bed * .40 * duck[:, None] + fx * .30
mix = np.tanh(mix * 1.1) / np.tanh(1.1)


def wr(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())


wr(str(BUILD / 'mix.wav'), mix)
wr(str(BUILD / 'music_only.wav'), (bed * .40 + fx * .30) * .9)
print('ok', np.abs(mix).max())
