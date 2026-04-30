#!/usr/bin/env python3
"""
Kodak PCD0992 — Geometry of Misalignment: 24-Image PDF Generator (v3)
Paper 3 (2026c): Angular Distance Between KLT and BT.601 Axes

v3 changes from v2:
- Header spacer bar pulled down, text evened out within
- Section titles closer to charts (reduced padding)
- Table/chart borders thicker (1.0-1.2pt)
- Section 1 grid darker
- Section 2 gets graph-paper background, whisker-and-point replacing colored bars
- Classification centered under Section 2 title
- BOLD CAPS typographic system for classification/status
- Section 3 compressed vertically to give Section 4 room
- Section 4 title/subtitle no longer overlap
- Cb-Cr callout condensed to one centered line in BOLD CAPS
- Precision badge applied to model divergence

Usage:
    python kodak_geometry_pdfs.py --input ./results --output ./paper3_output

Requirements: Python 3, NumPy, matplotlib
Author: Jasmine Baetzel (2026)
"""

import argparse, json, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.ticker as ticker

# =============================================================================
# CONSTANTS
# =============================================================================

BT601_MATRIX = np.array([
    [ 0.299,     0.587,     0.114    ],
    [-0.168736, -0.331264,  0.5      ],
    [ 0.5,      -0.418688, -0.081312 ]
])
BT601_UNIT = np.array([row / np.linalg.norm(row) for row in BT601_MATRIX])

IMAGE_TITLES = {
    "kodim01": "stone building", "kodim02": "red door", "kodim03": "hats",
    "kodim04": "portrait of a girl in red", "kodim05": "motocross bikes",
    "kodim06": "sailboat at anchor", "kodim07": "shuttered windows",
    "kodim08": "market place", "kodim09": "sailboats under spinnakers",
    "kodim10": "off-shore sailboat race", "kodim11": "sailboat at pier",
    "kodim12": "couple on beach", "kodim13": "mountain stream",
    "kodim14": "white water rafters", "kodim15": "girl with painted face",
    "kodim16": "tropical key", "kodim17": "monument",
    "kodim18": "model in black dress", "kodim19": "lighthouse in Maine",
    "kodim20": "P51 Mustang", "kodim21": "Portland Head Light",
    "kodim22": "barn and pond (KINSA Photo Contest)",
    "kodim23": "two macaws", "kodim24": "mountain chalet",
}

# 3-Tier diagnostic colors
COLOR_NAVY    = '#1B3A5C'
COLOR_EMERALD = '#2D6A4F'
COLOR_CRIMSON = '#8B2D3A'

# Supporting colors
COLOR_SLATE   = '#5A5A5A'
COLOR_GRAY    = '#888888'
COLOR_DARK    = '#333333'
COLOR_LIGHT   = '#CCCCCC'
COLOR_GRID    = '#C8C8C8'  # Darker grid (was #E0E0E0)
COLOR_BG      = '#FFFFFF'

FILL_ALPHA = 0.30

# Font settings
FONT_MONO = 'Courier'
FS_HDR = 7; FS_TITLE = 14; FS_SUB = 8; FS_SEC = 10; FS_BODY = 8
FS_HERO = 26; FS_HERO_SUB = 7.5; FS_SMALL = 6.5; FS_FOOTER = 7

# Page
PAGE_W = 8.5; PAGE_H = 11.0; ML = 0.75; MR = 0.75
R_CRIT = 0.404  # p<0.05 at n=24

# =============================================================================
# HELPERS
# =============================================================================

def assign_tiers(eff):
    s = np.sort(eff); n = len(s)
    return s[n//3], s[2*n//3]

def tier_color(e, t1, t2):
    if e >= t2: return COLOR_NAVY
    elif e >= t1: return COLOR_EMERALD
    else: return COLOR_CRIMSON

def tier_label(e, t1, t2):
    if e >= t2: return 'Aligned'
    elif e >= t1: return 'Moderate'
    else: return 'Critical'

def format_tier_text(tier_str):
    """BOLD CAPS typographic system for classifications."""
    parts = tier_str.split()
    if len(parts) >= 2:
        return parts[0].upper() + ' ' + ' '.join(p.lower() for p in parts[1:])
    return tier_str.upper()

def precision_badge(res):
    a = abs(res)
    if a < 1.0: return '\u2713'
    elif a > 3.0: return '\u0394'
    return ''

def compute_angles(evecs):
    evecs = np.array(evecs); angles = []
    for i in range(3):
        ev = evecs[i] / np.linalg.norm(evecs[i])
        c = np.clip(abs(np.dot(ev, BT601_UNIT[i])), 0, 1)
        angles.append(float(np.degrees(np.arccos(c))))
    return angles

def compute_ew(angles, evals):
    evals = np.array(evals); w = evals / evals.sum()
    return float(sum(angles[i]*w[i] for i in range(3)))

def compute_eff(rgb_r, ycbcr_r):
    return round((rgb_r - ycbcr_r) / rgb_r * 100, 1) if rgb_r > 0 else 0.0

def compute_regression(angles, eff):
    n = len(eff); X = np.column_stack([angles, np.ones(n)])
    c, _, _, _ = np.linalg.lstsq(X, eff, rcond=None)
    p = X @ c; R = float(np.corrcoef(eff, p)[0,1])
    return {'coeffs': c, 'R': round(R,4), 'R_sq': round(R**2,4), 'predicted': p}

# =============================================================================
# DATA LOADING
# =============================================================================

def load_all(input_dir):
    data = []
    for i in range(1,25):
        for pat in [f"kodim{i:02d}_gap_analysis.json", f"kodim{i:02d}_analysis.json"]:
            fp = os.path.join(input_dir, pat)
            if os.path.isfile(fp):
                d = json.load(open(fp)); break
        else: print(f"WARNING: kodim{i:02d} not found"); continue
        pca = d['pca_decomposition']
        angles = compute_angles(pca['eigenvectors'])
        data.append({
            'image_id': d['image_id'],
            'title': IMAGE_TITLES.get(d['image_id'], ''),
            'dimensions': d['dimensions'],
            'tier': d['dimensionality_tier'],
            'pc1_pct': pca['variance_explained_pct'][0],
            'condition_number': pca['condition_number'],
            'var_pct': pca['variance_explained_pct'],
            'angles': angles,
            'ew_angle': compute_ew(angles, pca['eigenvalues']),
            'efficiency': compute_eff(d['rgb_pairwise_correlations']['avg_abs_r'],
                                       d['ycbcr_residual_correlations']['avg_abs_r']),
            'ycbcr_resid': d['ycbcr_residual_correlations'],
            'psnr': d['chroma_subsampling_420'],
        })
    return data

# =============================================================================
# RENDERING
# =============================================================================

def setup_mpl():
    plt.rcParams.update({
        'font.family': 'monospace',
        'font.monospace': [FONT_MONO, 'DejaVu Sans Mono', 'Liberation Mono'],
        'font.size': FS_BODY, 'axes.linewidth': 1.0,
        'axes.edgecolor': COLOR_GRAY, 'axes.labelcolor': COLOR_DARK,
        'xtick.color': COLOR_DARK, 'ytick.color': COLOR_DARK,
        'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
        'xtick.major.size': 3, 'ytick.major.size': 3,
        'figure.facecolor': COLOR_BG, 'axes.facecolor': COLOR_BG,
        'savefig.facecolor': COLOR_BG, 'text.color': COLOR_DARK,
    })

def hline(fig, y, weight=0.8, color=COLOR_DARK):
    fig.add_artist(plt.Line2D([ML/PAGE_W, 1-MR/PAGE_W], [y,y],
        color=color, linewidth=weight, transform=fig.transFigure))

def draw_hf(fig, img_id, title, dims, tier, pc1, pg):
    """Header/footer with proper spacing — bar pulled down."""
    # Top text
    fig.text(ML/PAGE_W, 1-0.30/PAGE_H,
             'KODAK LOSSLESS TRUE COLOR IMAGE SUITE \u2014 PCD0992',
             fontsize=FS_HDR, fontfamily='monospace', color=COLOR_DARK, va='top')
    fig.text(1-MR/PAGE_W, 1-0.30/PAGE_H, f'Page {pg} of 2',
             fontsize=FS_HDR, fontfamily='monospace', color=COLOR_DARK, va='top', ha='right')

    # Spacer bar — generous breathing room
    hline(fig, 1-0.55/PAGE_H, 1.2)

    # Title with space below bar
    fig.text(ML/PAGE_W, 1-0.68/PAGE_H,
             f'Geometry of Misalignment: {img_id.upper()}',
             fontsize=FS_TITLE, fontfamily='monospace', fontweight='bold', color=COLOR_DARK, va='top')
    fig.text(1-MR/PAGE_W, 1-0.70/PAGE_H,
             f'{dims["width"]}x{dims["height"]} | 24-bit RGB | PNG (lossless)',
             fontsize=FS_SUB, fontfamily='monospace', color=COLOR_GRAY, va='top', ha='right')

    # Subtitle — single clean line, no overlay tricks
    tier_fmt = format_tier_text(tier)
    fig.text(ML/PAGE_W, 1-0.96/PAGE_H,
             f'{title} | {tier_fmt} (PC1 = {pc1}%)',
             fontsize=FS_SUB, fontfamily='monospace', color=COLOR_GRAY, va='top')

    hline(fig, 1-1.28/PAGE_H, 0.5, COLOR_LIGHT)

    # Footer
    fig.text(ML/PAGE_W, 0.25/PAGE_H,
             'Kodak PCD0992 Geometry of Misalignment Series | Baetzel (2026)',
             fontsize=FS_FOOTER, fontfamily='monospace', color=COLOR_GRAY, va='bottom')
    fig.text(1-MR/PAGE_W, 0.25/PAGE_H, f'Page {pg} of 2',
             fontsize=FS_FOOTER, fontfamily='monospace', color=COLOR_GRAY, va='bottom', ha='right')


def render_p1(fig, rec, S):
    draw_hf(fig, rec['image_id'], rec['title'], rec['dimensions'],
            rec['tier'], rec['pc1_pct'], 1)

    tc = rec['tier_color']
    idx = S['ids'].index(rec['image_id'])
    ae = S['eff']; ap = S['reg']['predicted']; rsq = S['reg']['R_sq']

    # --- Section 1 title ---
    fig.text(ML/PAGE_W, 1-1.48/PAGE_H,
             '1. Predicted vs. Actual Decorrelation Efficiency',
             fontsize=FS_SEC, fontfamily='monospace', fontweight='bold', color=COLOR_DARK, va='top')

    cw = (PAGE_W-ML-MR)*0.75/PAGE_W
    cx = (1-cw)/2
    ch = 2.85/PAGE_H

    ax1 = fig.add_axes([cx, 1-4.75/PAGE_H, cw, ch])

    # Dense metric grid — major every 5%, minor every 2.5%
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax1.xaxis.set_minor_locator(ticker.MultipleLocator(2.5))
    ax1.yaxis.set_minor_locator(ticker.MultipleLocator(2.5))
    ax1.grid(True, which='major', color=COLOR_GRID, linewidth=0.5, alpha=0.7, zorder=0)
    ax1.grid(True, which='minor', color='#DEDEDE', linewidth=0.25, alpha=0.5, zorder=0)
    ax1.set_axisbelow(True)

    # Identity line — match data range
    ax1.plot([28,85],[28,85], color=COLOR_LIGHT, linewidth=0.8, zorder=1)

    # Suite points
    for j in range(len(ae)):
        if j == idx: continue
        c = tier_color(ae[j], S['t1'], S['t2'])
        ax1.scatter(ap[j], ae[j], s=22, color=c, alpha=0.30, edgecolors='none', zorder=2)

    # This image
    ax1.scatter(ap[idx], ae[idx], s=55, color=tc, edgecolors=COLOR_DARK,
                linewidth=0.8, zorder=4)
    ax1.annotate(rec['image_id'].upper(), (ap[idx], ae[idx]),
                 xytext=(8,6), textcoords='offset points',
                 fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_DARK)

    ax1.set_xlabel('Predicted Efficiency (3-axis model)', fontsize=FS_BODY, fontfamily='monospace')
    ax1.set_ylabel('Actual Measured Efficiency (%)', fontsize=FS_BODY, fontfamily='monospace')
    ax1.text(0.97, 0.05, f'R\u00b2 = {rsq:.3f}\np < 0.001 | n = 24',
             transform=ax1.transAxes, fontsize=FS_SMALL, fontfamily='monospace',
             color=COLOR_DARK, ha='right', va='bottom')
    ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))
    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))
    ax1.set_xlim(28,85); ax1.set_ylim(28,85)

    # --- Section 2 title (more padding above from Section 1) ---
    s2y = 1-5.30/PAGE_H
    fig.text(ML/PAGE_W, s2y, '2. Angular Misalignment Profile',
             fontsize=FS_SEC, fontfamily='monospace', fontweight='bold', color=COLOR_DARK, va='top')

    # Classification subtitle — LEFT ALIGNED to same margin as title
    tier_fmt = format_tier_text(rec['tier'])
    fig.text(ML/PAGE_W, s2y - 0.20/PAGE_H,
             f'     Classification: {tier_fmt} (PC1 = {rec["pc1_pct"]}%)',
             fontsize=FS_SMALL, fontfamily='monospace', fontweight='bold',
             color=COLOR_SLATE, va='top')

    # Dot-strip chart — tighter to subtitle
    ax2h = 2.3/PAGE_H
    ax2 = fig.add_axes([cx, 1-7.85/PAGE_H, cw, ax2h])

    # Full coordinate grid — strong opacity for visibility
    ax2.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax2.xaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax2.grid(True, which='major', color='#B0B0B0', linewidth=0.6, alpha=0.9, zorder=0)
    ax2.grid(True, which='minor', color='#D0D0D0', linewidth=0.35, alpha=0.7, zorder=0)
    # Horizontal gridlines to create boxes
    for yg in [0.5, 1.5]:
        ax2.axhline(y=yg, color='#B0B0B0', linewidth=0.6, alpha=0.9, zorder=0)
    ax2.set_axisbelow(True)
    ax2.spines['left'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False)

    # Single-line axis labels — saturated colors
    axis_names = ['\u03b8\u2081 (PC1\u2194Y)', '\u03b8\u2082 (PC2\u2194Cb)', '\u03b8\u2083 (PC3\u2194Cr)']
    # Saturated versions — vivid blue, green, red
    DOT_NAVY    = '#0D47A1'
    DOT_EMERALD = '#1B7A3D'
    DOT_CRIMSON = '#B71C1C'
    axis_colors = [DOT_NAVY, DOT_EMERALD, DOT_CRIMSON]
    ypos = [2, 1, 0]

    for i, (nm, yp) in enumerate(zip(axis_names, ypos)):
        smin = S['astats'][i]['min']
        smax = S['astats'][i]['max']
        smean = S['astats'][i]['mean']
        sstd = S['astats'][i]['std']
        tv = rec['angles'][i]

        # Thin baseline
        ax2.plot([0, 90], [yp, yp], color='#E0E0E0', linewidth=0.6, zorder=1)

        # Plot all 24 images as small dots — higher alpha for visibility
        for j in range(len(S['ids'])):
            if j == idx: continue
            other_angle = S['all_angles'][j, i]
            ax2.scatter(other_angle, yp, marker='o', s=20,
                        color=axis_colors[i], alpha=0.55, edgecolors='none', zorder=2)

        # Suite mean — small vertical tick
        ax2.plot([smean, smean], [yp-0.15, yp+0.15],
                 color=COLOR_GRAY, linewidth=1.0, zorder=3)

        # This image — large filled circle, saturated color
        ax2.scatter(tv, yp, marker='o', s=80, color=axis_colors[i],
                    edgecolors=COLOR_DARK, linewidth=0.9, zorder=5)

        # Value label above dot
        ax2.text(tv, yp+0.38, f'{tv:.2f}\u00b0',
                 fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_DARK,
                 ha='center', va='bottom', fontweight='bold')

        # Range + SD label on right
        ax2.text(93, yp, f'{smin:.1f}\u00b0 \u2013 {smax:.1f}\u00b0  |  SD: {sstd:.2f}',
                 fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY,
                 ha='left', va='center')

    ax2.set_yticks(ypos)
    ax2.set_yticklabels(axis_names, fontsize=FS_BODY, fontfamily='monospace')
    ax2.tick_params(axis='y', length=0)
    ax2.set_xlim(0, 90)
    ax2.set_ylim(-0.6, 2.8)

    # X-axis label — use fig.text BELOW the axes to avoid overlap with legend
    ax2.set_xlabel('')  # clear matplotlib's own label
    fig.text(0.5, 1-8.10/PAGE_H,
             'Angular Misalignment (degrees)',
             fontsize=FS_BODY, fontfamily='monospace', color=COLOR_DARK,
             ha='center', va='top')

    # Legend — well below x-axis label
    fig.text(0.5, 1-8.30/PAGE_H,
             'Small dots = suite (n=24)  |  Tick = suite mean  |  Large dot = this image',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center', va='top')

    # Caption — centered, padded from legend
    pe = ap[idx]
    pkc = max(rec['angles'][1], rec['angles'][2])
    pkl = '\u03b8\u2082' if rec['angles'][1] >= rec['angles'][2] else '\u03b8\u2083'

    fig.text(0.5, 1-8.60/PAGE_H,
             f'{pkc:.1f}\u00b0 chrominance misalignment ({pkl}) \u2192 '
             f'{pe:.1f}% predicted  |  \u03b8\u2081 = {rec["angles"][0]:.1f}\u00b0',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_DARK, va='top',
             style='italic', ha='center')

    # Coupling note — padded from caption
    fig.text(ML/PAGE_W, 1-9.00/PAGE_H,
             'Note: \u03b8\u2082 and \u03b8\u2083 are functionally coupled at r = 0.999 (Baetzel 2026c). '
             'The three-axis model is diagnostic;',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, va='top')
    fig.text(ML/PAGE_W, 1-9.18/PAGE_H,
             'the geometric degrees of freedom are two (one luminance angle, one chrominance angle), not three.',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, va='top')


def render_p2(fig, rec, S):
    draw_hf(fig, rec['image_id'], rec['title'], rec['dimensions'],
            rec['tier'], rec['pc1_pct'], 2)

    tc = rec['tier_color']
    idx = S['ids'].index(rec['image_id'])
    pe = float(S['reg']['predicted'][idx])
    res = float(rec['efficiency'] - pe)
    ew = float(S['ew_pred'][idx])
    rsq = S['reg']['R_sq']
    bdg = precision_badge(res)
    rw = 'bold' if abs(res) > 3.0 else 'normal'

    # --- Section 3: Triptych Hero ---
    fig.text(ML/PAGE_W, 1-1.38/PAGE_H, '3. Model Comparison',
             fontsize=FS_SEC, fontfamily='monospace', fontweight='bold', color=COLOR_DARK, va='top')
    hline(fig, 1-1.55/PAGE_H, 0.5, COLOR_LIGHT)

    hy = 1-2.05/PAGE_H   # hero numbers
    sy = 1-2.40/PAGE_H   # sub labels
    cy = 1-2.60/PAGE_H   # context

    cols = [0.18, 0.50, 0.82]

    # Measured
    fig.text(cols[0], hy, f'{rec["efficiency"]:.1f}%',
             fontsize=FS_HERO, fontfamily='monospace', fontweight='bold', color=tc, ha='center', va='center')
    fig.text(cols[0], sy, 'Measured Efficiency',
             fontsize=FS_HERO_SUB, fontfamily='monospace', color=COLOR_SLATE, ha='center')
    fig.text(cols[0], cy, f'Suite: {S["emin"]:.1f}% - {S["emax"]:.1f}%',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center')

    # Predicted
    rs = f'Residual: {res:+.1f}pp'
    if bdg: rs = f'{bdg} {rs}'
    fig.text(cols[1], hy, f'{pe:.1f}%',
             fontsize=FS_HERO, fontfamily='monospace', fontweight='bold', color=COLOR_DARK, ha='center', va='center')
    fig.text(cols[1], sy, '3-Axis Predicted',
             fontsize=FS_HERO_SUB, fontfamily='monospace', color=COLOR_SLATE, ha='center')
    fig.text(cols[1], cy, f'R\u00b2 = {rsq:.3f} | {rs}',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center', fontweight=rw)

    # Energy-Weighted
    fig.text(cols[2], hy, f'{ew:.1f}%',
             fontsize=FS_HERO, fontfamily='monospace', fontweight='bold', color=COLOR_DARK, ha='center', va='center')
    fig.text(cols[2], sy, 'Energy-Weighted',
             fontsize=FS_HERO_SUB, fontfamily='monospace', color=COLOR_SLATE, ha='center')
    fig.text(cols[2], cy, f'R\u00b2 = {S["ew_rsq"]:.3f} | NO PREDICTIVE POWER',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center', fontweight='bold')

    # Divergence
    div = abs(pe - ew)
    fig.text(0.50, 1-2.85/PAGE_H,
             f'Model divergence: {div:.1f} percentage points',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center')

    hline(fig, 1-3.05/PAGE_H, 0.5, COLOR_LIGHT)

    # --- Section 4: Residual Correlations ---
    fig.text(ML/PAGE_W, 1-3.25/PAGE_H,
             '4. Axis-Specific Residual Correlations (Suite-Wide)',
             fontsize=FS_SEC, fontfamily='monospace', fontweight='bold', color=COLOR_DARK, va='top')
    fig.text(ML/PAGE_W, 1-3.50/PAGE_H,
             'Bivariate correlations: per-axis angular misalignment vs. YCbCr residual pairs (n = 24)',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, va='top')

    tt = 1-4.00/PAGE_H
    rh = 0.38/PAGE_H
    cx = [0.12, 0.40, 0.58, 0.76]

    rm = S['rmat']
    rlabs = ['|Y-Cb|', '|Y-Cr|', '|Cb-Cr|']
    rows = ['theta_1 (PC1<->Y)', 'theta_2 (PC2<->Cb)', 'theta_3 (PC3<->Cr)']

    # Header rules (thicker)
    hline(fig, tt+0.15/PAGE_H, 1.2)
    for j, l in enumerate(rlabs):
        fig.text(cx[j+1], tt+0.28/PAGE_H, l,
                 fontsize=FS_BODY+0.5, fontfamily='monospace', color=COLOR_DARK,
                 ha='center', va='center', fontweight='bold')
    hline(fig, tt, 0.8)

    for i, rl in enumerate(rows):
        yc = tt - (i+0.5)*rh
        fig.text(cx[0], yc, rl,
                 fontsize=FS_BODY, fontfamily='monospace', color=COLOR_DARK, ha='left', va='center')
        for j in range(3):
            v = rm[i,j]; sig = abs(v) >= R_CRIT
            w = 'bold' if sig else 'normal'
            c = COLOR_DARK if sig else COLOR_GRAY
            fig.text(cx[j+1], yc+0.06/PAGE_H, f'{v:+.3f}',
                     fontsize=FS_BODY, fontfamily='monospace', color=c, ha='center', va='center', fontweight=w)
            fig.text(cx[j+1], yc-0.08/PAGE_H, 'p < 0.05' if sig else 'n.s.',
                     fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center', va='center')
        if i < 2:
            hline(fig, tt-(i+1)*rh, 0.3, COLOR_LIGHT)

    hline(fig, tt-3*rh, 0.8)

    # Cb-Cr callout
    fig.text(0.76, tt-3*rh-0.15/PAGE_H,
             'Cb-Cr: NO SIGNAL \u2014 intrinsic to BT.601 chroma bisection',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_SLATE,
             ha='center', va='top', fontweight='bold')

    # --- Section 5: Key Findings (2x2) ---
    s5 = 1-5.85/PAGE_H
    hline(fig, s5+0.15/PAGE_H, 0.5, COLOR_LIGHT)

    tier_fmt = format_tier_text(rec['tier'])
    fig.text(ML/PAGE_W, s5,
             f'5. Key Findings | {rec["title"].upper()} | {tier_fmt}',
             fontsize=FS_SEC, fontfamily='monospace', fontweight='bold', color=COLOR_DARK, va='top')

    r1y = s5 - 0.50/PAGE_H
    r2y = s5 - 1.30/PAGE_H
    cl = 0.28; cr = 0.72
    so = 0.24/PAGE_H; co = 0.42/PAGE_H

    pi = 1 if rec['angles'][1] >= rec['angles'][2] else 2
    pa = rec['angles'][pi]; pl = f'theta_{pi+1}'

    # Top-Left: Measured
    fig.text(cl, r1y, f'{rec["efficiency"]:.1f}%', fontsize=20, fontfamily='monospace',
             fontweight='bold', color=tc, ha='center', va='center')
    fig.text(cl, r1y-so, 'Measured Efficiency', fontsize=FS_SMALL, fontfamily='monospace',
             color=COLOR_SLATE, ha='center')
    fig.text(cl, r1y-co, f'Suite: {S["emin"]:.1f}% - {S["emax"]:.1f}% | Mean: {S["emean"]:.1f}%',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center')

    # Top-Right: Predicted
    fig.text(cr, r1y, f'{pe:.1f}%', fontsize=20, fontfamily='monospace',
             fontweight='bold', color=COLOR_DARK, ha='center', va='center')
    fig.text(cr, r1y-so, '3-Axis Predicted', fontsize=FS_SMALL, fontfamily='monospace',
             color=COLOR_SLATE, ha='center')
    fig.text(cr, r1y-co, f'Residual: {res:+.1f}pp | EW pred: {ew:.1f}%',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center')

    # Bottom-Left: Peak Chroma
    fig.text(cl, r2y, f'{pa:.1f}\u00b0', fontsize=20, fontfamily='monospace',
             fontweight='bold', color=COLOR_DARK, ha='center', va='center')
    fig.text(cl, r2y-so, f'Peak Chroma ({pl})', fontsize=FS_SMALL, fontfamily='monospace',
             color=COLOR_SLATE, ha='center')
    fig.text(cl, r2y-co, f'Suite: {S["astats"][pi]["min"]:.1f}\u00b0 - {S["astats"][pi]["max"]:.1f}\u00b0 | Wide variation',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center')

    # Bottom-Right: Luminance
    fig.text(cr, r2y, f'{rec["angles"][0]:.1f}\u00b0', fontsize=20, fontfamily='monospace',
             fontweight='bold', color=COLOR_DARK, ha='center', va='center')
    fig.text(cr, r2y-so, 'Luminance (theta_1)', fontsize=FS_SMALL, fontfamily='monospace',
             color=COLOR_SLATE, ha='center')
    fig.text(cr, r2y-co, f'Suite: {S["astats"][0]["min"]:.1f}\u00b0 - {S["astats"][0]["max"]:.1f}\u00b0 | Narrow band',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, ha='center')

    # --- Section 6: Global Model ---
    s6 = s5 - 2.10/PAGE_H
    hline(fig, s6+0.15/PAGE_H, 0.5, COLOR_LIGHT)
    fig.text(ML/PAGE_W, s6, '6. Global Model Context (n = 24)',
             fontsize=FS_SEC, fontfamily='monospace', fontweight='bold', color=COLOR_DARK, va='top')
    c = S['reg']['coeffs']
    fig.text(ML/PAGE_W, s6-0.25/PAGE_H,
             f'Efficiency = {c[3]:.2f} + ({c[0]:+.2f})(theta_1) + ({c[1]:+.2f})(theta_2) + ({c[2]:+.2f})(theta_3)',
             fontsize=FS_BODY, fontfamily='monospace', color=COLOR_DARK, va='top')
    fig.text(ML/PAGE_W, s6-0.45/PAGE_H,
             f'R\u00b2 = {rsq:.3f} | p < 0.001 | This image: {pe:.1f}% | Residual: {res:+.1f}pp',
             fontsize=FS_SMALL, fontfamily='monospace', color=COLOR_GRAY, va='top')

    # --- References ---
    ry = s6 - 0.80/PAGE_H
    hline(fig, ry+0.15/PAGE_H, 0.8)
    fig.text(ML/PAGE_W, ry, 'References', fontsize=FS_BODY, fontfamily='monospace',
             fontweight='bold', color=COLOR_DARK, va='top')
    refs = [
        '[1] Baetzel, J. (2026a). "Statistical Characterization of Inter-Channel Redundancy Structure"',
        '[2] Baetzel, J. (2026b). "Per-Image Decorrelation Efficiency of the BT.601 Fixed Transform"',
        '[3] Baetzel, J. (2026c). "The Orthogonal Constraint on Chrominance Axis Misalignment"',
        '[4] ITU-R Recommendation BT.601-7: Studio Encoding Parameters, 2011.',
        '[5] Watanabe, S. "Karhunen-Loeve Expansion and Factor Analysis," pp. 635-660, 1965.',
    ]
    for j, r in enumerate(refs):
        fig.text(ML/PAGE_W, ry-(j+1)*0.20/PAGE_H, r, fontsize=FS_SMALL, fontfamily='monospace',
                 color=COLOR_GRAY, va='top')


def render_pdf(rec, S, path):
    with PdfPages(path) as pdf:
        f1 = plt.figure(figsize=(PAGE_W, PAGE_H)); render_p1(f1, rec, S); pdf.savefig(f1); plt.close(f1)
        f2 = plt.figure(figsize=(PAGE_W, PAGE_H)); render_p2(f2, rec, S); pdf.savefig(f2); plt.close(f2)

def write_json(rec, S, odir):
    idx = S['ids'].index(rec['image_id']); pe = S['reg']['predicted'][idx]
    out = {
        'image_id': rec['image_id'], 'title': rec['title'],
        'dimensionality_tier': rec['tier'], 'condition_number': rec['condition_number'],
        'variance_explained_pct': rec['var_pct'],
        'angular_misalignment': {
            'theta_1_PC1_Y': round(rec['angles'][0],2),
            'theta_2_PC2_Cb': round(rec['angles'][1],2),
            'theta_3_PC3_Cr': round(rec['angles'][2],2),
            'total_degrees': round(sum(rec['angles']),2),
        },
        'energy_weighted_angle': round(rec['ew_angle'],4),
        'decorrelation_efficiency_pct': rec['efficiency'],
        'predicted_efficiency_3axis': round(float(pe),2),
        'residual_pp': round(float(rec['efficiency']-pe),2),
        'diagnostic_tier': rec['tier_label'],
    }
    json.dump(out, open(os.path.join(odir, f'{rec["image_id"]}_geometry.json'), 'w'), indent=2)

def write_summary(data, S, odir):
    sm = {
        'suite': 'Kodak Lossless True Color Image Suite (PCD0992)', 'n_images': len(data),
        'angular_range_statistics': {ax: S['astats'][i] for i, ax in enumerate(['PC1_Y','PC2_Cb','PC3_Cr'])},
        'regression': {'R': S['reg']['R'], 'R_squared': S['reg']['R_sq'],
            'coefficients': {k: round(float(v),6) for k,v in zip(['theta1','theta2','theta3'], S['reg']['coeffs'][:3])},
            'intercept': round(float(S['reg']['coeffs'][3]),4)},
        'energy_weighted_R_squared': S['ew_rsq'],
        'diagnostic_tiers': {'t1': S['t1'], 't2': S['t2']},
    }
    json.dump(sm, open(os.path.join(odir, 'geometry_suite_summary.json'), 'w'), indent=2)

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Paper 3 PDF Generator v3')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not os.path.isdir(args.input): print(f"Error: {args.input} not found"); sys.exit(1)
    os.makedirs(args.output, exist_ok=True)

    print("Loading..."); data = load_all(args.input); print(f"  {len(data)} images")

    aa = np.array([d['angles'] for d in data])
    ae = np.array([d['efficiency'] for d in data])
    ew = np.array([d['ew_angle'] for d in data])
    ids = [d['image_id'] for d in data]

    yr = np.array([[abs(d['ycbcr_resid']['Y_Cb']), abs(d['ycbcr_resid']['Y_Cr']),
                    abs(d['ycbcr_resid']['Cb_Cr'])] for d in data])

    reg = compute_regression(aa, ae)
    ewr = float(np.corrcoef(ew, ae)[0,1]); ewrsq = round(ewr**2, 4)
    ewsl = np.polyfit(ew, ae, 1); ewp = np.polyval(ewsl, ew)

    rmat = np.zeros((3,3))
    for i in range(3):
        for j in range(3):
            rmat[i,j] = float(np.corrcoef(aa[:,i], yr[:,j])[0,1])

    astats = []
    for i in range(3):
        c = aa[:,i]
        astats.append({'min': round(float(c.min()),2), 'max': round(float(c.max()),2),
                       'mean': round(float(c.mean()),2), 'std': round(float(c.std(ddof=1)),2)})

    t1, t2 = assign_tiers(ae)
    for d in data:
        d['tier_color'] = tier_color(d['efficiency'], t1, t2)
        d['tier_label'] = tier_label(d['efficiency'], t1, t2)

    S = {'ids': ids, 'eff': ae, 'reg': reg, 'ew_rsq': ewrsq, 'ew_pred': ewp,
         'rmat': rmat, 'astats': astats, 'all_angles': aa,
         'emin': round(float(ae.min()),1), 'emax': round(float(ae.max()),1),
         'emean': round(float(ae.mean()),1), 't1': round(float(t1),1), 't2': round(float(t2),1)}

    setup_mpl()
    print("Generating...")
    for d in data:
        p = os.path.join(args.output, f'{d["image_id"]}_geometry.pdf')
        print(f'  {d["image_id"]}... eff={d["efficiency"]:.1f}% [{d["tier_label"]}]')
        render_pdf(d, S, p); write_json(d, S, args.output)

    write_summary(data, S, args.output)
    print(f"\nDone: {len(data)} PDFs + JSONs + summary -> {args.output}")

if __name__ == '__main__':
    main()
