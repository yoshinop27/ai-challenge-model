"""
SoilSense data-flow diagram — slide-deck ready PNG.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = "#0e0e0e"
BLUE_BD  = "#1e40af";  BLUE_T  = "#93c5fd"
GREEN_BD = "#14532d";  GREEN_T = "#86efac"
GOLD_BD  = "#92400e";  GOLD_T  = "#fbbf24"
PURP_BD  = "#312e81";  PURP_T  = "#a5b4fc"
SLATE_BD = "#1e293b";  SLATE_T = "#64748b"
CARD     = "#131313"
DIM      = "#4b5563"
TEXT_DIM = "#374151"

DPI = 220
W, H = 15, 8.5

fig, ax = plt.subplots(figsize=(W, H), dpi=DPI)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

# ── Box ───────────────────────────────────────────────────────────────────────
def box(cx, cy, w, h, badge, title, subtitle, bd, tc):
    rx, ry = cx - w / 2, cy - h / 2
    ax.add_patch(FancyBboxPatch(
        (rx, ry), w, h,
        boxstyle="round,pad=0.05",
        linewidth=1.1, edgecolor=bd, facecolor=CARD, zorder=3,
    ))
    # badge strip at top
    strip_h = h * 0.28
    ax.add_patch(FancyBboxPatch(
        (rx, cy + h / 2 - strip_h), w, strip_h,
        boxstyle="round,pad=0.0",
        linewidth=0, facecolor=bd, alpha=0.18, zorder=4,
        clip_on=True,
    ))
    ax.text(cx, cy + h / 2 - strip_h / 2, badge,
            ha="center", va="center", fontsize=5.2, color=tc,
            fontweight="bold", zorder=5)
    ax.text(cx, cy - 0.04, title,
            ha="center", va="center", fontsize=7.2, color=tc,
            fontweight="bold", zorder=5)
    ax.text(cx, cy - 0.30, subtitle,
            ha="center", va="center", fontsize=5.4, color=DIM,
            zorder=5, style="italic")

# ── Arrow (horizontal) ────────────────────────────────────────────────────────
def harrow(x1, y, x2, label="", color="#374151", lw=1.3):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                mutation_scale=9),
                zorder=2)
    if label:
        ax.text((x1 + x2) / 2, y + 0.11, label,
                ha="center", va="bottom", fontsize=4.9, color=TEXT_DIM, zorder=5)

# ── Arrow (vertical) ──────────────────────────────────────────────────────────
def varrow(x, y1, y2, label="", color="#374151", lw=1.1):
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                mutation_scale=9),
                zorder=2)
    if label:
        ax.text(x + 0.1, (y1 + y2) / 2, label,
                ha="left", va="center", fontsize=4.9, color=TEXT_DIM, zorder=5)

# ── Section headers ───────────────────────────────────────────────────────────
COLS = [1.75, 4.9, 8.05, 11.2]
HEADERS = ["Frontend", "Backend (FastAPI)", "ML Models", "LLM (Claude)"]
HCOLS   = [BLUE_T, GREEN_T, GOLD_T, PURP_T]
for cx, label, tc in zip(COLS, HEADERS, HCOLS):
    ax.text(cx, H - 0.3, label,
            ha="center", va="center", fontsize=6.2, color=tc, fontweight="bold",
            bbox=dict(facecolor=BG, edgecolor=tc, boxstyle="round,pad=0.25",
                      linewidth=0.8),
            zorder=6)

# ── Column dividers ───────────────────────────────────────────────────────────
for x in [3.3, 6.46, 9.62]:
    ax.plot([x, x], [0.55, H - 0.68], color="#1a1a1a", lw=0.9, zorder=1)

# ── Row labels ────────────────────────────────────────────────────────────────
ROW_A, ROW_B, ROW_C = 6.4, 4.2, 1.9
for ry, label in [(ROW_A, "Sample\nPath"), (ROW_B, "Farm\nAnalysis"), (ROW_C, "External\nAPIs")]:
    ax.text(0.25, ry, label, ha="center", va="center",
            fontsize=5, color="#2d3748", fontweight="bold", rotation=90, zorder=5)

# ═══════════════════════════════════════════════════
#  NODES
# ═══════════════════════════════════════════════════
BW, BH = 2.8, 0.88

# — Row A: Sample path —
box(COLS[0], ROW_A, BW, BH,
    "React · Frontend",    "Sample Modal",       "Photo upload · crop list",      BLUE_BD, BLUE_T)
box(COLS[1], ROW_A, BW, BH,
    "FastAPI · /predict",  "Image Classifier",   "Decode · transform · infer",    GREEN_BD, GREEN_T)
box(COLS[2], ROW_A, BW, BH,
    "PyTorch · EfficientNet-B0 ×2",  "Dual Classifier",  "Soil type · moisture level",  GOLD_BD, GOLD_T)
box(COLS[3], ROW_A, BW, BH,
    "Claude · OpenRouter", "Crop Recommendations", "Good/avoid crops · tip",      PURP_BD, PURP_T)

# — Row B: Farm analysis path —
box(COLS[0], ROW_B, BW, BH,
    "React · Mapbox",      "Farm Map",           "Markers · contour overlay",     BLUE_BD, BLUE_T)
box(COLS[1], ROW_B, BW, BH,
    "FastAPI · /analyze-farm", "Farm Analysis",  "Weather · elevation · satellite", GREEN_BD, GREEN_T)
box(COLS[2], ROW_B, BW, BH,
    "Claude · vision + text", "Suitability Grid", "15×15 score grid per crop",   PURP_BD, PURP_T)
box(COLS[3], ROW_B, BW, BH,
    "Claude · agronomist", "12-Month Timeline",  "Plant · harvest · maintain",    PURP_BD, PURP_T)

# — Row C: External APIs —
EXT_W, EXT_H = 2.4, 0.65
EXT_XS = [1.6, 4.3, 7.0, 9.7, 12.4]
EXT_DATA = [
    ("OpenWeather",    "Current + 5-day forecast"),
    ("Open Elevation", "Grid elevation data"),
    ("Mapbox",         "Satellite imagery + tiles"),
    ("OpenRouter",     "LLM request gateway"),
    ("Farm Map UI",    "Overlay + timeline modal"),
]
for cx, (title, sub) in zip(EXT_XS, EXT_DATA):
    ax.add_patch(FancyBboxPatch(
        (cx - EXT_W/2, ROW_C - EXT_H/2), EXT_W, EXT_H,
        boxstyle="round,pad=0.04",
        linewidth=0.7, edgecolor="#1e293b", facecolor="#0d0d0d", zorder=3,
    ))
    ax.text(cx, ROW_C + 0.09, title,
            ha="center", va="center", fontsize=6.2, color=SLATE_T,
            fontweight="bold", zorder=4)
    ax.text(cx, ROW_C - 0.16, sub,
            ha="center", va="center", fontsize=4.8, color="#2d3748",
            zorder=4, style="italic")

# ═══════════════════════════════════════════════════
#  ARROWS
# ═══════════════════════════════════════════════════

# Row A horizontals
harrow(COLS[0]+BW/2, ROW_A, COLS[1]-BW/2, "photo + crops", BLUE_T)
harrow(COLS[1]+BW/2, ROW_A, COLS[2]-BW/2, "image tensor",  GREEN_T)
harrow(COLS[2]+BW/2, ROW_A, COLS[3]-BW/2, "soil · moisture",GOLD_T)

# Row B horizontals
harrow(COLS[0]+BW/2, ROW_B, COLS[1]-BW/2, "farm + samples", BLUE_T)
harrow(COLS[1]+BW/2, ROW_B, COLS[2]-BW/2, "context + imagery", GREEN_T)
harrow(COLS[2]+BW/2, ROW_B, COLS[3]-BW/2, "suitability grid", PURP_T)

# Col 3: Crop recs flow down to Row B backend (result consolidation)
varrow(COLS[3], ROW_A - BH/2, ROW_B + BH/2, "recs JSON", PURP_T)

# Col 1: results flow left from backend back to Farm Map
ax.annotate("", xy=(COLS[0]+BW/2, ROW_B),
            xytext=(COLS[1]-BW/2, ROW_B),
            arrowprops=dict(arrowstyle="<|-", color=GREEN_T, lw=1.1,
                            mutation_scale=9), zorder=2)
ax.text((COLS[0]+BW/2 + COLS[1]-BW/2)/2, ROW_B - 0.12, "contour PNG + timeline",
        ha="center", va="top", fontsize=4.9, color=TEXT_DIM, zorder=5)

# External APIs feed /analyze-farm (vertical up)
for ex_cx in [EXT_XS[0], EXT_XS[1], EXT_XS[2]]:
    ax.annotate("", xy=(COLS[1], ROW_B - BH/2 - 0.08),
                xytext=(ex_cx, ROW_C + EXT_H/2),
                arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=0.8,
                                mutation_scale=7,
                                connectionstyle="arc3,rad=0.0"),
                zorder=1)

# OpenRouter feeds Claude nodes (subtle)
ax.annotate("", xy=(COLS[3], ROW_B - BH/2 - 0.08),
            xytext=(EXT_XS[3], ROW_C + EXT_H/2),
            arrowprops=dict(arrowstyle="-|>", color="#1e1e2e", lw=0.8,
                            mutation_scale=7),
            zorder=1)
ax.annotate("", xy=(COLS[3], ROW_A - BH/2 - 0.08),
            xytext=(EXT_XS[3], ROW_C + EXT_H/2),
            arrowprops=dict(arrowstyle="-|>", color="#1e1e2e", lw=0.8,
                            mutation_scale=7),
            zorder=1)

# Farm Map UI box (last in ext row) ← from col0 Farm Map
ax.annotate("", xy=(EXT_XS[4] - EXT_W/2, ROW_C),
            xytext=(COLS[0] + BW/2, ROW_B - BH/2),
            arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=0.8,
                            mutation_scale=7,
                            connectionstyle="arc3,rad=0.15"),
            zorder=1)

# ── Title & credit ────────────────────────────────────────────────────────────
ax.text(W / 2, H - 0.1, "SoilSense — Application Data Flow",
        ha="center", va="top", fontsize=11, color="#e8e8e8", fontweight="bold", zorder=6)
ax.text(W - 0.2, 0.1, "Grinnell AI  ·  Pi515 AI Challenge 2026",
        ha="right", va="bottom", fontsize=5.2, color="#252525", zorder=6)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    (BLUE_T,  "Frontend (React)"),
    (GREEN_T, "Backend (FastAPI)"),
    (GOLD_T,  "ML Models (PyTorch)"),
    (PURP_T,  "LLM (Claude)"),
    (SLATE_T, "External APIs"),
]
lx = 0.6
for tc, label in legend_items:
    ax.add_patch(mpatches.FancyBboxPatch(
        (lx - 0.08, 0.08), 0.16, 0.22,
        boxstyle="round,pad=0.02", facecolor=tc, linewidth=0, zorder=5,
    ))
    ax.text(lx + 0.15, 0.19, label,
            ha="left", va="center", fontsize=5, color="#3a3a3a", zorder=5)
    lx += 1.7

# ── Save ──────────────────────────────────────────────────────────────────────
out = "documentation/data_flow.png"
fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor=BG, edgecolor="none")
plt.close(fig)
print(f"Saved → {out}  ({W*DPI:.0f}×{H*DPI:.0f}px)")
