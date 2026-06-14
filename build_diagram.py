import sys
sys.path.insert(0, "/Users/chasedevries/.claude/skills/drawio-diagrams")
from drawio_layout import Diagram, text_size

# ---- box content; sizes are computed from the text so boxes are snug ----
LABELS = {
    "pages":        "HTML views + HTMX 1.9\nindex / photos\nhx-get loads navbar fragment",
    "photojs":      "photos.html inline JS\nfetch() gallery + thumbnails\n(error/empty handling)",
    "mux":          "router/router.go + middleware\nServeMux · logRequests · recoverPanics",
    "pagehandlers": "Page handlers\nindex / photos\n-> html/template",
    "navbarh":      "navbar fragment\nactive-link state",
    "static":       "Static file servers\n/assets  ·  /styles",
    "requests":     "requests pkg\nnavbar path helper",
    "gcs":          "Google Cloud Storage\nchasedv-photos bucket",
}
BOLD = {"mux"}
CYL = {"gcs"}


def size(bid):
    return text_size(LABELS[bid], bold=bid in BOLD,
                     shape="cylinder" if bid in CYL else "rounded")


# Pack boxes into rows with a fixed gap so containers wrap them tightly.
GAP = 60
pos = {}  # id -> (x, y, w, h)


def row(ids, left, top):
    x = left
    for bid in ids:
        w, h = size(bid)
        pos[bid] = (x, top, w, h)
        x += w + GAP
    return x - GAP  # right edge of the row


def center_over(bid, left, right, top):
    w, h = size(bid)
    pos[bid] = (round((left + right) / 2 - w / 2), top, w, h)


LEFT = 60
client_right = row(["pages", "photojs"], LEFT, 90)
rowb_right = row(["pagehandlers", "navbarh", "static"], LEFT, 360)
center_over("mux", LEFT, rowb_right, 250)          # mux sits above the handler row
nb_x, _, nb_w, _ = pos["navbarh"]
center_over("requests", nb_x, nb_x + nb_w, 480)    # requests sits under navbar handler
gx, _, gw, _ = pos["static"]
center_over("gcs", gx, gx + gw, 630)               # GCS under the right side

# ---- build the diagram ----
d = Diagram(page_width=680, page_height=760, name="htmx-demo architecture")
d.text("title", 30, 20, 620, 36,
       "htmx-demo — Go + HTMX photo site (Cloud Run)",
       font_size=20, bold=True, align="center")

# containers placed roughly; fit_containers() tightens them around their boxes
d.container("client", 40, 80, 640, 150, "BROWSER (client)",
            fill="#E3F2FD", stroke="#1565C0", font_color="#0D47A1")
d.container("server", 40, 220, 640, 420,
            "GO SERVER — net/http ServeMux",
            fill="#E8F5E9", stroke="#2E7D32", font_color="#1B5E20")
d.container("external", 40, 640, 640, 120, "EXTERNAL SERVICES",
            fill="#F3E5F5", stroke="#6A1B9A", font_color="#4A148C")

FILLS = {
    "pages": ("#BBDEFB", "#1565C0"), "photojs": ("#BBDEFB", "#1565C0"),
    "mux": ("#A5D6A7", "#2E7D32"),
    "pagehandlers": ("#C8E6C9", "#2E7D32"), "navbarh": ("#C8E6C9", "#2E7D32"),
    "static": ("#C8E6C9", "#2E7D32"), "requests": ("#C8E6C9", "#2E7D32"),
    "gcs": ("#E1BEE7", "#6A1B9A"),
}
for bid, (x, y, w, h) in pos.items():
    fill, stroke = FILLS[bid]
    d.box(bid, x, y, w, h, LABELS[bid], fill=fill, stroke=stroke,
          bold=bid in BOLD, shape="cylinder" if bid in CYL else "rounded")

d.fit_containers(pad=22, title_h=32)


# ---- edges computed from the (packed) geometry ----
def corridor(src, fa, dst, ta):
    p = d.anchor(src, fa)
    q = d.anchor(dst, ta)
    cy = (p[1] + q[1]) / 2
    return [(p[0], cy), (q[0], cy)]


# pages -> mux: route through the gap just ABOVE the server container so the
# horizontal run clears the (left-aligned) server title, then drop into mux's
# top-center, which is to the right of the title text.
_hp = d.anchor("pages", (0.85, 1))
_hq = d.anchor("mux", (0.5, 0))
_hcy = d.containers["server"]["y"] - 12
d.edge("e-http", "pages", "mux", fa=(0.85, 1), ta=(0.5, 0),
       waypoints=[(_hp[0], _hcy), (_hq[0], _hcy)],
       label="HTTP GET", color="#1565C0", label_color="#0D47A1")
d.edge("e-mux-page", "mux", "pagehandlers", fa=(0.2, 1), ta=(0.5, 0),
       waypoints=corridor("mux", (0.2, 1), "pagehandlers", (0.5, 0)))
d.edge("e-mux-nav", "mux", "navbarh", fa=(0.5, 1), ta=(0.5, 0),
       waypoints=corridor("mux", (0.5, 1), "navbarh", (0.5, 0)))
d.edge("e-mux-static", "mux", "static", fa=(0.85, 1), ta=(0.5, 0),
       waypoints=corridor("mux", (0.85, 1), "static", (0.5, 0)))
d.edge("e-nav-req", "navbarh", "requests", fa=(0.5, 1), ta=(0.5, 0),
       waypoints=corridor("navbarh", (0.5, 1), "requests", (0.5, 0)))

# Photos load straight from GCS in the browser, bypassing the Go server:
# down the far-right lane, clear of every box, into the GCS box from the right.
_p = d.anchor("photojs", (0.9, 1))
_q = d.anchor("gcs", (1, 0.5))
_lane = max(v[0] + v[2] for v in pos.values()) + 30  # right of every box
_yt = _p[1] + 30
d.edge("e-photo", "photojs", "gcs", fa=(0.9, 1), ta=(1, 0.5),
       waypoints=[(_p[0], _yt), (_lane, _yt), (_lane, _q[1])],
       label="fetch() — bypasses\nGo server",
       color="#6A1B9A", label_color="#4A148C", dashed=True)

# drop each label onto the first clear spot along its edge
emap = {e["id"]: e for e in d.edges}
for _ in range(4):
    for eid, e in emap.items():
        if not e["label"]:
            continue
        for t in (i / 100 for i in range(5, 95)):
            e["t"] = t
            if not [p for p in d.check() if eid in p]:
                break

problems = d.check()
if problems:
    print("PROBLEMS:")
    print("\n".join(problems))
else:
    d.write("/Users/chasedevries/Projects/web-test/architecture.drawio")
    print("OK: architecture.drawio written, verified collision-free")
