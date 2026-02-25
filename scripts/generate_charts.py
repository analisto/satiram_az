"""
generate_charts.py
Produces all business insight charts from data/satiram.csv → charts/
"""

from __future__ import annotations

import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ---------------------------------------------------------------------------
# Paths & style
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "satiram.csv"
CHARTS_DIR = ROOT / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# Colour palette (business-appropriate)
BLUE        = "#2563EB"
LIGHT_BLUE  = "#93C5FD"
ORANGE      = "#F97316"
GREEN       = "#16A34A"
RED         = "#DC2626"
GREY        = "#94A3B8"
DARK        = "#1E293B"
BG          = "#F8FAFC"

def apply_style(ax: plt.Axes, title: str, xlabel: str = "", ylabel: str = "") -> None:
    ax.set_facecolor(BG)
    ax.get_figure().set_facecolor("white")
    ax.set_title(title, fontsize=14, fontweight="bold", color=DARK, pad=14)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, color=DARK)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color=DARK)
    ax.tick_params(colors=DARK, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")
    ax.grid(axis="x" if ax.get_xlim()[0] != ax.get_xlim()[1] else "y",
            color="#E2E8F0", linewidth=0.8, linestyle="--")

def save(fig: plt.Figure, name: str) -> None:
    path = CHARTS_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {name}")


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
with open(DATA_FILE, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(f"Loaded {len(rows)} listings.\n")

# ---------------------------------------------------------------------------
# 1. Top 15 Categories by Listing Count
# ---------------------------------------------------------------------------
cat_counts = Counter(r["category_name"] for r in rows)
top15 = cat_counts.most_common(15)
labels15 = [t[0] for t in reversed(top15)]
values15 = [t[1] for t in reversed(top15)]

fig, ax = plt.subplots(figsize=(11, 7))
bars = ax.barh(labels15, values15, color=BLUE, height=0.65)
for bar, val in zip(bars, values15):
    ax.text(val + 5, bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", ha="left", fontsize=8.5, color=DARK)
apply_style(ax, "Top 15 Categories by Number of Listings", xlabel="Number of Listings")
ax.set_xlim(0, max(values15) * 1.15)
ax.grid(axis="x", color="#E2E8F0", linewidth=0.8, linestyle="--")
fig.tight_layout()
save(fig, "01_top_categories_by_listings.png")

# ---------------------------------------------------------------------------
# 2. Geographic Distribution — Top 12 Cities
# ---------------------------------------------------------------------------
city_counts = Counter(r["city_name"] for r in rows if r["city_name"])
top12_cities = city_counts.most_common(12)
c_labels = [t[0] for t in reversed(top12_cities)]
c_values = [t[1] for t in reversed(top12_cities)]

fig, ax = plt.subplots(figsize=(11, 6))
colors_city = [BLUE if l == "Bakı" else LIGHT_BLUE for l in c_labels]
bars = ax.barh(c_labels, c_values, color=colors_city, height=0.65)
for bar, val in zip(bars, c_values):
    ax.text(val + 10, bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", ha="left", fontsize=8.5, color=DARK)
apply_style(ax, "Geographic Distribution of Listings — Top 12 Cities", xlabel="Number of Listings")
ax.set_xlim(0, max(c_values) * 1.15)
ax.grid(axis="x", color="#E2E8F0", linewidth=0.8, linestyle="--")
ax.text(0.97, 0.05, "83% of all listings\noriginate from Bakı",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=8.5, color=RED, style="italic")
fig.tight_layout()
save(fig, "02_geographic_distribution.png")

# ---------------------------------------------------------------------------
# 3. Daily Listing Volume (Jan – Feb 2026)
# ---------------------------------------------------------------------------
day_counts: dict[str, int] = defaultdict(int)
for r in rows:
    dt = r.get("created_at", "")
    if dt and len(dt) >= 10:
        # format: DD.MM.YYYY HH:MM
        parts = dt[:10].split(".")
        if len(parts) == 3:
            day_counts[dt[:10]] += 1

# Keep only Jan-Feb 2026
relevant = {k: v for k, v in day_counts.items()
            if k.endswith("2026") and k[3:5] in ("01", "02")}

# Sort by date
def sort_key(date_str: str) -> tuple:
    d, m, y = date_str.split(".")
    return int(y), int(m), int(d)

sorted_dates = sorted(relevant, key=sort_key)
day_labels = [f"{k[:5]}" for k in sorted_dates]  # DD.MM
day_values = [relevant[k] for k in sorted_dates]

fig, ax = plt.subplots(figsize=(14, 5))
ax.fill_between(range(len(day_labels)), day_values, alpha=0.15, color=BLUE)
ax.plot(range(len(day_labels)), day_values, color=BLUE, linewidth=2, marker="o", markersize=4)

# Mark top day
peak_idx = day_values.index(max(day_values))
ax.annotate(f"Peak: {max(day_values)} listings\n({day_labels[peak_idx]})",
            xy=(peak_idx, max(day_values)),
            xytext=(peak_idx + 1.5, max(day_values) - 30),
            arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.3),
            fontsize=8.5, color=ORANGE, fontweight="bold")

ax.set_xticks(range(len(day_labels)))
ax.set_xticklabels(day_labels, rotation=45, ha="right", fontsize=7.5)
apply_style(ax, "Daily Listing Volume — January & February 2026", ylabel="New Listings")
ax.yaxis.set_major_locator(mticker.MultipleLocator(50))
ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, linestyle="--")
fig.tight_layout()
save(fig, "03_daily_listing_volume.png")

# ---------------------------------------------------------------------------
# 4. Buyer Engagement by Category — Average Views per Listing
# ---------------------------------------------------------------------------
focus_cats = [
    "Torpaq", "Həyət evləri, bağ evləri", "Nömrələr və SIM-kartlar", "Audio və video",
    "Saat və zinət əşyaları", "İş axtarıram", "Velosipedlər",
    "Biznes üçün avadanlıq", "Noutbuklar və netbuklar",
    "Oyunlar, Pultlar və Proqramlar", "Mənzillər", "Avtomobillər",
    "Telefonlar", "Mebellər",
]
cat_views = defaultdict(list)
for r in rows:
    cat_views[r["category_name"]].append(float(r["views"]) if r["views"] else 0)

avg_views = [(cat, statistics.mean(cat_views[cat])) for cat in focus_cats if cat in cat_views]
avg_views.sort(key=lambda x: x[1])
av_labels = [x[0] for x in avg_views]
av_values = [x[1] for x in avg_views]

fig, ax = plt.subplots(figsize=(11, 7))
bar_colors = [GREEN if v > 50 else BLUE if v > 35 else LIGHT_BLUE for v in av_values]
bars = ax.barh(av_labels, av_values, color=bar_colors, height=0.65)
for bar, val in zip(bars, av_values):
    ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}", va="center", ha="left", fontsize=8.5, color=DARK)
apply_style(ax, "Buyer Engagement by Category — Average Views per Listing", xlabel="Avg Views per Listing")
ax.set_xlim(0, max(av_values) * 1.15)
ax.grid(axis="x", color="#E2E8F0", linewidth=0.8, linestyle="--")

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=GREEN, label="High (>50)"),
                   Patch(facecolor=BLUE, label="Medium (35-50)"),
                   Patch(facecolor=LIGHT_BLUE, label="Low (<35)")]
ax.legend(handles=legend_elements, loc="lower right", fontsize=8, framealpha=0.8)
fig.tight_layout()
save(fig, "04_avg_views_by_category.png")

# ---------------------------------------------------------------------------
# 5. Premium Boost — Premium vs Non-Premium Average Views
# ---------------------------------------------------------------------------
top10_cats = [t[0] for t in cat_counts.most_common(10)]
prem_avg, nonprem_avg, cat_plot_labels = [], [], []
for cat in top10_cats:
    p = [float(r["views"]) for r in rows if r["category_name"] == cat and r["is_premium"] == "True"]
    np_ = [float(r["views"]) for r in rows if r["category_name"] == cat and r["is_premium"] != "True"]
    if p and np_:
        prem_avg.append(statistics.mean(p))
        nonprem_avg.append(statistics.mean(np_))
        cat_plot_labels.append(cat)

x = range(len(cat_plot_labels))
width = 0.38
fig, ax = plt.subplots(figsize=(13, 6))
b1 = ax.bar([i - width / 2 for i in x], prem_avg, width, label="Premium", color=ORANGE)
b2 = ax.bar([i + width / 2 for i in x], nonprem_avg, width, label="Standard", color=LIGHT_BLUE)
for bar, val in zip(b1, prem_avg):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{val:.0f}", ha="center", fontsize=7.5, color=ORANGE, fontweight="bold")
for bar, val in zip(b2, nonprem_avg):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{val:.0f}", ha="center", fontsize=7.5, color=DARK)
ax.set_xticks(list(x))
ax.set_xticklabels(cat_plot_labels, rotation=30, ha="right", fontsize=8.5)
ax.legend(fontsize=9)
apply_style(ax, "Premium vs Standard Listings — Average Views per Category", ylabel="Avg Views")
ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, linestyle="--")
fig.tight_layout()
save(fig, "05_premium_vs_standard_views.png")

# ---------------------------------------------------------------------------
# 6. Feature Adoption Across the Platform
# ---------------------------------------------------------------------------
features = {
    "WhatsApp Enabled":    sum(1 for r in rows if r["whatsapp_enabled"] == "True"),
    "Standard Listing\n(non-premium)": sum(1 for r in rows if r["is_premium"] != "True"),
    "New Item":            sum(1 for r in rows if r["is_new"] == "True"),
    "Premium Listing":     sum(1 for r in rows if r["is_premium"] == "True"),
    "Delivery Offered":    sum(1 for r in rows if r["has_delivery"] == "True"),
    "Shop Account":        sum(1 for r in rows if r["is_shop"] == "True"),
}
feat_labels = list(features.keys())
feat_values = [features[k] for k in feat_labels]
feat_pcts = [100 * v / len(rows) for v in feat_values]

fig, ax = plt.subplots(figsize=(11, 5))
bar_c = [GREEN if p > 60 else BLUE if p > 20 else ORANGE if p > 10 else RED for p in feat_pcts]
bars = ax.bar(feat_labels, feat_pcts, color=bar_c, width=0.55)
for bar, pct, val in zip(bars, feat_pcts, feat_values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{pct:.0f}%\n({val:,})", ha="center", fontsize=8.5, color=DARK)
apply_style(ax, "Feature Adoption Across the Platform", ylabel="% of Total Listings")
ax.set_ylim(0, 110)
ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, linestyle="--")
ax.axhline(y=100, color=GREY, linewidth=0.8, linestyle=":")
fig.tight_layout()
save(fig, "06_feature_adoption.png")

# ---------------------------------------------------------------------------
# 7. Delivery Adoption by Top 10 Categories
# ---------------------------------------------------------------------------
top10_for_delivery = [t[0] for t in cat_counts.most_common(10)]
del_pcts = []
del_labels = []
for cat in top10_for_delivery:
    total = sum(1 for r in rows if r["category_name"] == cat)
    with_del = sum(1 for r in rows if r["category_name"] == cat and r["has_delivery"] == "True")
    del_labels.append(cat)
    del_pcts.append(100 * with_del / total if total else 0)

# sort ascending
paired = sorted(zip(del_pcts, del_labels))
del_pcts_s = [p[0] for p in paired]
del_labels_s = [p[1] for p in paired]

fig, ax = plt.subplots(figsize=(11, 6))
bar_c2 = [GREEN if p >= 25 else BLUE if p >= 10 else RED for p in del_pcts_s]
bars = ax.barh(del_labels_s, del_pcts_s, color=bar_c2, height=0.65)
for bar, val in zip(bars, del_pcts_s):
    ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val:.0f}%", va="center", ha="left", fontsize=8.5, color=DARK)
apply_style(ax, "Delivery Adoption Rate — Top 10 Categories", xlabel="% of Listings Offering Delivery")
ax.set_xlim(0, max(del_pcts_s) * 1.25)
ax.axvline(x=100 * 1404 / len(rows), color=ORANGE, linewidth=1.2, linestyle="--")
ax.text(100 * 1404 / len(rows) + 0.3, 0.3, "Platform avg",
        fontsize=7.5, color=ORANGE, style="italic")
ax.grid(axis="x", color="#E2E8F0", linewidth=0.8, linestyle="--")
fig.tight_layout()
save(fig, "07_delivery_adoption_by_category.png")

# ---------------------------------------------------------------------------
# 8. Seller Activity Distribution
# ---------------------------------------------------------------------------
seller_listing_counts = Counter(r["customer_id"] for r in rows)
buckets = {"1 listing": 0, "2–5 listings": 0, "6–10 listings": 0, "11+ listings": 0}
for v in seller_listing_counts.values():
    if v == 1:
        buckets["1 listing"] += 1
    elif v <= 5:
        buckets["2–5 listings"] += 1
    elif v <= 10:
        buckets["6–10 listings"] += 1
    else:
        buckets["11+ listings"] += 1

bucket_labels = list(buckets.keys())
bucket_values = list(buckets.values())
bucket_pcts = [100 * v / sum(bucket_values) for v in bucket_values]

fig, ax = plt.subplots(figsize=(9, 5))
b_colors = [BLUE, LIGHT_BLUE, ORANGE, RED]
bars = ax.bar(bucket_labels, bucket_pcts, color=b_colors, width=0.5)
for bar, pct, val in zip(bars, bucket_pcts, bucket_values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
            f"{pct:.0f}%\n({val:,} sellers)", ha="center", fontsize=9, color=DARK)
apply_style(ax, "Seller Activity Distribution — How Many Listings per Seller", ylabel="% of Sellers")
ax.set_ylim(0, 100)
ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, linestyle="--")
fig.tight_layout()
save(fig, "08_seller_activity_distribution.png")

# ---------------------------------------------------------------------------
# 9. Median Asking Price by Category (Top 10, excluding zero prices)
# ---------------------------------------------------------------------------
price_data = []
for cat in [t[0] for t in cat_counts.most_common(10)]:
    prices = [float(r["price"]) for r in rows if r["category_name"] == cat and float(r["price"] or 0) > 0]
    if prices:
        price_data.append((cat, statistics.median(prices)))

price_data.sort(key=lambda x: x[1])
p_labels = [x[0] for x in price_data]
p_values = [x[1] for x in price_data]

fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh(p_labels, p_values, color=BLUE, height=0.65)
for bar, val in zip(bars, p_values):
    label = f"{val:,.0f} AZN"
    ax.text(val + max(p_values) * 0.01, bar.get_y() + bar.get_height() / 2,
            label, va="center", ha="left", fontsize=8.5, color=DARK)
apply_style(ax, "Median Asking Price by Category (Top 10)", xlabel="Median Price (AZN)")
ax.set_xlim(0, max(p_values) * 1.2)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.grid(axis="x", color="#E2E8F0", linewidth=0.8, linestyle="--")
fig.tight_layout()
save(fig, "09_median_price_by_category.png")

# ---------------------------------------------------------------------------
# 10. Engagement Funnel — Views → Favourites → Contacts
# ---------------------------------------------------------------------------
# Summed across all listings
total_views = sum(float(r["views"]) for r in rows)
total_favs = sum(float(r["favorites_count"]) for r in rows)
total_contacts = sum(float(r["contact_count"]) for r in rows)

funnel_labels = ["Total Views", "Saved to Favourites", "Contact Requests"]
funnel_values = [total_views, total_favs, total_contacts]
funnel_pcts = [100, 100 * total_favs / total_views, 100 * total_contacts / total_views]

fig, ax = plt.subplots(figsize=(9, 5))
f_colors = [BLUE, ORANGE, GREEN]
bars = ax.bar(funnel_labels, funnel_values, color=f_colors, width=0.45)
for bar, val, pct in zip(bars, funnel_values, funnel_pcts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 200,
            f"{val:,.0f}\n({pct:.2f}% of views)", ha="center", fontsize=9, color=DARK)
apply_style(ax, "Buyer Engagement Funnel — From Views to Contacts", ylabel="Total Count (All Listings)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.set_ylim(0, max(funnel_values) * 1.2)
ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, linestyle="--")
fig.tight_layout()
save(fig, "10_engagement_funnel.png")

print("\nAll 10 charts generated successfully in charts/")
