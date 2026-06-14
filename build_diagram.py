import sys
sys.path.insert(0, "/Users/chasedevries/.claude/skills/drawio-diagrams")
from drawio_layout import Diagram

d = Diagram(page_width=1654, page_height=1169, name="htmx-demo architecture")

d.text("title", 40, 20, 1574, 40,
       "htmx-demo — Go + HTMX web app (Google Cloud Run)",
       font_size=22, bold=True, align="center")

# ---- CLIENT tier ----
d.container("client", 40, 80, 1574, 180, "BROWSER (client)",
            fill="#E3F2FD", stroke="#1565C0", font_color="#0D47A1")
d.box("pages", 100, 135, 560, 95,
      "HTML views + HTMX 1.9\nindex / jokes / photos / budget\nhx-get/hx-post swap fragments",
      fill="#BBDEFB", stroke="#1565C0")
d.box("photojs", 820, 135, 560, 95,
      "photos.html inline JS\nfetch() gallery + thumbnails\n(runs in the browser)",
      fill="#BBDEFB", stroke="#1565C0")

# ---- SERVER tier ----
d.container("server", 40, 330, 1574, 470,
            "GO SERVER — net/http ServeMux (port 6969)",
            fill="#E8F5E9", stroke="#2E7D32", font_color="#1B5E20")
d.box("mux", 640, 390, 380, 70,
      "router/router.go\nServeMux + handlers",
      fill="#A5D6A7", stroke="#2E7D32", bold=True)
d.box("pagehandlers", 100, 530, 360, 115,
      "Page handlers\nindex/jokes/photos/budget\n-> html/template views",
      fill="#C8E6C9", stroke="#2E7D32")
d.box("fraghandlers", 540, 530, 400, 130,
      "Fragment handlers\nnavbar · generate · budgetData\nauth · logout",
      fill="#C8E6C9", stroke="#2E7D32")
d.box("static", 1180, 530, 360, 95,
      "Static file servers\n/assets  ·  /styles",
      fill="#C8E6C9", stroke="#2E7D32")
d.box("jokes", 540, 705, 200, 80,
      "jokes pkg\nrandom joke",
      fill="#C8E6C9", stroke="#2E7D32")
d.box("requests", 780, 705, 360, 80,
      "requests pkg\nSupabase client (auth + data)",
      fill="#C8E6C9", stroke="#2E7D32")
d.box("vestigial", 100, 695, 360, 95,
      "Built but UNUSED:\nEcho instance · templ · mysql pkg",
      fill="#FFE0B2", stroke="#E65100")

# ---- EXTERNAL tier ----
d.container("external", 40, 870, 1574, 220, "EXTERNAL SERVICES",
            fill="#F3E5F5", stroke="#6A1B9A", font_color="#4A148C")
d.box("mysql", 100, 935, 320, 130,
      "MySQL 8 (compose)\nunused by app",
      shape="cylinder", fill="#ECEFF1", stroke="#90A4AE")
d.box("supabase", 780, 935, 320, 130,
      "Supabase\nAuth + transactions\n(Postgres)",
      shape="cylinder", fill="#E1BEE7", stroke="#6A1B9A")
d.box("gcs", 1180, 935, 360, 130,
      "Google Cloud Storage\nchasedv-photos bucket",
      shape="cylinder", fill="#E1BEE7", stroke="#6A1B9A")

# ---- EDGES ----
d.edge("e-http", "pages", "mux", fa=(0.85, 1), ta=(0.5, 0),
       waypoints=[(556, 300), (830, 300)],
       label="HTTP GET/POST", label_t=0.5, color="#1565C0", label_color="#0D47A1")

d.edge("e-photo", "photojs", "gcs", fa=(0.9, 1), ta=(0.5, 0),
       waypoints=[(1324, 290), (1577, 290), (1577, 905), (1360, 905)],
       label="fetch() — bypasses\nGo server", label_t=0.5,
       color="#6A1B9A", label_color="#4A148C", dashed=True)

d.edge("e-mux-page", "mux", "pagehandlers", fa=(0.2, 1), ta=(0.5, 0),
       waypoints=[(716, 495), (280, 495)])
d.edge("e-mux-frag", "mux", "fraghandlers", fa=(0.45, 1), ta=(0.55, 0),
       waypoints=[(811, 495), (760, 495)])
d.edge("e-mux-static", "mux", "static", fa=(0.85, 1), ta=(0.5, 0),
       waypoints=[(983, 495), (1360, 495)])

d.edge("e-frag-jokes", "fraghandlers", "jokes", fa=(0.2, 1), ta=(0.5, 0),
       waypoints=[(620, 705)])
d.edge("e-frag-req", "fraghandlers", "requests", fa=(0.75, 1), ta=(0.5, 0),
       waypoints=[(840, 685), (960, 685)])

d.edge("e-req-supa", "requests", "supabase", fa=(0.5, 1), ta=(0.6, 0),
       waypoints=[(960, 850), (972, 850)],
       label="REST / GoTrue", label_t=0.5, color="#6A1B9A", label_color="#4A148C")

d.edge("e-vest-mysql", "vestigial", "mysql", fa=(0.3, 1), ta=(0.5, 0),
       waypoints=[(208, 855), (260, 855)],
       label="unused", label_t=0.5, color="#90A4AE", label_color="#607D8B", dashed=True)

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
