"""SVG kit that follows Google Cloud architecture-diagram conventions.

Containers carry the meaning (org, project, VPC, perimeter, zone); services are
icons with labels, never boxes. Palette and border treatments follow the Google
Cloud diagramming guidance so the result reads the way a GCP reference
architecture reads.
"""
import base64, os

def _icon_root():
    """Locate the cloud provider icon set.

    Order: DIAGRAM_ICONS env var, then the resources folder shipped with the
    `diagrams` pip package, then a vendored ./icons folder. If Vodafone holds a
    licensed Google Cloud icon pack, point DIAGRAM_ICONS at it: the layout code
    below never hard-codes a provider, only relative paths like
    "gcp/compute/run.png".
    """
    env = os.environ.get("DIAGRAM_ICONS")
    if env and os.path.isdir(env):
        return env
    try:
        import diagrams
        cand = os.path.join(os.path.dirname(os.path.dirname(diagrams.__file__)), "resources")
        if os.path.isdir(cand):
            return cand
    except ImportError:
        pass
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
    if os.path.isdir(local):
        return local
    raise RuntimeError(
        "No icon set found. Run `pip install diagrams`, or set DIAGRAM_ICONS to a "
        "folder laid out as <provider>/<category>/<name>.png")


RES = _icon_root()

# Google Material palette
GBLUE   = "#4285F4"; GBLUE_D = "#1A73E8"; GRED = "#EA4335"; GRED_D = "#C5221F"
GYELLOW = "#FBBC04"; GGREEN = "#34A853"; GGREEN_D = "#188038"
GREY_T  = "#202124"   # text
GREY_S  = "#5F6368"   # secondary text
GREY_B  = "#DADCE0"   # borders
GREY_F  = "#F1F3F4"   # cloud fill
WHITE   = "#FFFFFF"
PURPLE  = "#A142F4"

FONT = "Arial, Helvetica, sans-serif"
_cache = {}


def _b64(path):
    if path not in _cache:
        with open(os.path.join(RES, path), "rb") as fh:
            _cache[path] = base64.b64encode(fh.read()).decode()
    return _cache[path]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Diagram:
    def __init__(self, w, h):
        self.w, self.h, self.p = w, h, []

    def add(self, s):
        self.p.append(s)

    # ---------- text ----------
    def text(self, x, y, t, size=11, bold=False, color=GREY_T, anchor="start", italic=False):
        self.add('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s"%s '
                 'fill="%s" text-anchor="%s">%s</text>'
                 % (x, y, FONT, size, "500" if bold else "400",
                    ' font-style="italic"' if italic else "", color, anchor, esc(t)))

    def wrap(self, x, y, t, chars, size=9.5, color=GREY_S, lh=11.5, anchor="start", bold=False):
        words, line, lines = t.split(), "", []
        for w in words:
            cand = (line + " " + w).strip()
            if len(cand) > chars and line:
                lines.append(line); line = w
            else:
                line = cand
        if line:
            lines.append(line)
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, size=size, color=color, anchor=anchor, bold=bold)
        return len(lines) * lh

    # ---------- containers ----------
    def cloud(self, x, y, w, h, title, sub=None):
        """Outermost Google Cloud boundary: solid light fill, no dashes."""
        self.add('<rect x="%s" y="%s" width="%s" height="%s" rx="8" fill="%s" stroke="%s" '
                 'stroke-width="1.5"/>' % (x, y, w, h, GREY_F, GREY_B))
        self.add('<g transform="translate(%s,%s) scale(0.052)">'
                 '<path fill="#EA4335" d="M170 90l14-24 1-14C159 29 125 14 88 14 54 14 23 26 0 47l40 57 '
                 '25-7c12-7 25-11 40-11 22 0 44 7 60 20l5-16z" transform="translate(130,30)"/>'
                 '<path fill="#4285F4" d="M283 104c-8-30-25-56-48-75l-40 40c20 17 33 42 33 70v10c22 0 40 18 '
                 '40 40s-18 40-40 40h-80l-8 8v48l8 8h80c57 0 104-46 104-104 0-35-18-67-45-85z" '
                 'transform="translate(130,30)"/>'
                 '<path fill="#34A853" d="M104 376h80v-64h-80c-6 0-11-1-16-3l-11 3-24 24-2 11c18 19 43 29 '
                 '53 29z" transform="translate(130,30)"/>'
                 '<path fill="#FBBC04" d="M104 168C47 168 0 214 0 272c0 34 16 64 42 83l46-46c-13-6-22-20-22-37 '
                 '0-22 18-40 40-40l8-8v-48l-10-8z" transform="translate(130,30)"/>'
                 '</g>' % (x + 14, y + 10))
        self.text(x + 44, y + 26, title, size=13.5, bold=True, color=GREY_T)
        if sub:
            self.text(x + 44, y + 41, sub, size=9.5, color=GREY_S)

    def project(self, x, y, w, h, title, sub=None, icon="gcp/management/project.png"):
        self.add('<rect x="%s" y="%s" width="%s" height="%s" rx="6" fill="%s" stroke="%s" '
                 'stroke-width="1.2"/>' % (x, y, w, h, WHITE, GREY_B))
        if icon:
            self.add('<image href="data:image/png;base64,%s" x="%s" y="%s" width="20" height="20"/>'
                     % (_b64(icon), x + 12, y + 10))
        self.text(x + 38, y + 24, title, size=11.5, bold=True, color=GREY_T)
        if sub:
            self.text(x + 38, y + 37, sub, size=9, color=GREY_S)

    def group(self, x, y, w, h, title, color=GREY_B, dash=None, fill=None, fill_op=1.0,
              icon=None, sub=None, tsize=10.5):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        f = fill or WHITE
        self.add('<rect x="%s" y="%s" width="%s" height="%s" rx="5" fill="%s" fill-opacity="%s" '
                 'stroke="%s" stroke-width="1.2"%s/>' % (x, y, w, h, f, fill_op, color, d))
        tx = x + 10
        if icon:
            self.add('<image href="data:image/png;base64,%s" x="%s" y="%s" width="17" height="17"/>'
                     % (_b64(icon), x + 9, y + 8))
            tx = x + 32
        self.text(tx, y + 21, title, size=tsize, bold=True,
                  color=color if color not in (GREY_B,) else GREY_S)
        if sub:
            self.text(tx, y + 34, sub, size=8.5, color=GREY_S)

    # ---------- services ----------
    def icon(self, cx, y, path, label, sub=None, size=42, chars=18):
        """A service: icon centred on cx, label underneath. No bounding box."""
        self.add('<image href="data:image/png;base64,%s" x="%s" y="%s" width="%s" height="%s"/>'
                 % (_b64(path), cx - size / 2, y, size, size))
        ly = y + size + 13
        used = self.wrap(cx, ly, label, chars, size=10, color=GREY_T, lh=11.5,
                         anchor="middle", bold=True)
        if sub:
            self.wrap(cx, ly + used + 1, sub, chars + 6, size=8.5, color=GREY_S,
                      lh=10, anchor="middle")

    def store(self, cx, y, path, label, sub=None, size=42, chars=20):
        self.icon(cx, y, path, label, sub, size, chars)

    # ---------- connectors ----------
    def line(self, pts, color=GREY_S, width=1.4, dash=None, arrow=True, bidir=False):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        cid = color.lstrip("#")
        path = " ".join(("M" if i == 0 else "L") + "%s %s" % p for i, p in enumerate(pts))
        self.add('<path d="%s" fill="none" stroke="%s" stroke-width="%s"%s%s%s/>'
                 % (path, color, width, d,
                    ' marker-end="url(#a-%s)"' % cid if arrow else "",
                    ' marker-start="url(#s-%s)"' % cid if bidir else ""))

    def step(self, x, y, n, color=GBLUE_D, r=10):
        self.add('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="#FFFFFF" stroke-width="2"/>'
                 % (x, y, r, color))
        self.text(x, y + 3.8, str(n), size=10.5, bold=True, color=WHITE, anchor="middle")

    def tag(self, x, y, t, color=GREY_S, size=8.5):
        w = len(t) * size * 0.55 + 10
        self.add('<rect x="%s" y="%s" width="%s" height="15" rx="3" fill="#FFFFFF" '
                 'fill-opacity="0.95" stroke="%s" stroke-width="0.6"/>' % (x, y, w, color))
        self.text(x + w / 2, y + 11, t, size=size, color=color, anchor="middle")
        return w

    # ---------- render ----------
    def render(self):
        mk = ""
        # sorted, not a bare set: set iteration order varies with hash
        # randomisation, which would make every rebuild produce a spurious diff
        for c in sorted({GREY_S, GBLUE, GBLUE_D, GRED, GRED_D, GGREEN, GGREEN_D,
                         PURPLE, GYELLOW, GREY_B}):
            cid = c.lstrip("#")
            mk += ('<marker id="a-%s" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5.5" '
                   'markerHeight="5.5" orient="auto-start-reverse">'
                   '<path d="M0 1L9 5L0 9z" fill="%s"/></marker>'
                   '<marker id="s-%s" viewBox="0 0 10 10" refX="1.5" refY="5" markerWidth="5.5" '
                   'markerHeight="5.5" orient="auto-start-reverse">'
                   '<path d="M9 1L0 5L9 9z" fill="%s"/></marker>' % (cid, c, cid, c))
        return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                'viewBox="0 0 %s %s" width="%s" height="%s" font-family="%s">'
                '<defs>%s</defs><rect width="%s" height="%s" fill="#FFFFFF"/>%s</svg>'
                % (self.w, self.h, self.w, self.h, FONT, mk, self.w, self.h, "".join(self.p)))

    def save(self, path):
        open(path, "w").write(self.render())
        print("wrote", path, "%.0f KB" % (os.path.getsize(path) / 1024))
