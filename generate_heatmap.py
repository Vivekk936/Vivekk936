"""
Render a GitHub-style contribution heatmap as an animated SVG.

Input:
    data/contributions.json

Output:
    contrib-heatmap.svg
"""

import json
import os
import html
from datetime import datetime, timedelta


HERE = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(
    HERE, "..", "data", "contributions.json"
)

OUT_PATH = os.path.join(
    HERE, "..", "contrib-heatmap.svg"
)

# GitHub-style contribution colors
PALETTE = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
    "#69f0a0",
]


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def level_for_count(count, maximum):
    if count <= 0:
        return 0

    if maximum <= 0:
        return 0

    ratio = count / maximum

    if ratio <= 0.20:
        return 1
    if ratio <= 0.40:
        return 2
    if ratio <= 0.65:
        return 3
    if ratio <= 0.85:
        return 4

    return 5


def esc(value):
    return html.escape(str(value))


def build_heatmap(data):
    days = data.get("days", [])

    if not days:
        raise RuntimeError(
            "No contribution days found in contributions.json"
        )

    days = sorted(days, key=lambda x: x["date"])

    counts = {
        item["date"]: int(item.get("count", 0))
        for item in days
    }

    first_date = datetime.strptime(
        days[0]["date"], "%Y-%m-%d"
    ).date()

    last_date = datetime.strptime(
        days[-1]["date"], "%Y-%m-%d"
    ).date()

    # Move back to Sunday so the calendar starts cleanly.
    first_sunday = first_date - timedelta(
        days=(first_date.weekday() + 1) % 7
    )

    # Calendar dimensions
    cell = 13
    gap = 4
    step = cell + gap

    left = 48
    top = 54

    dates = []

    current = first_sunday

    while current <= last_date:
        dates.append(current)
        current += timedelta(days=1)

    columns = ((len(dates) + 6) // 7)

    width = left + columns * step + 25
    height = top + 7 * step + 70

    maximum = max(counts.values()) if counts else 0

    parts = []

    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )

    parts.append("""
<style>
    .bg {
        fill: #0d1117;
    }

    .title {
        fill: #c9d1d9;
        font-family: monospace;
        font-size: 14px;
        font-weight: bold;
    }

    .label {
        fill: #8b949e;
        font-family: monospace;
        font-size: 10px;
    }

    .cell {
        opacity: 0;
        animation: reveal 0.45s ease forwards;
    }

    @keyframes reveal {
        from {
            opacity: 0;
            transform: scale(0.4);
        }

        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    .legend {
        fill: #8b949e;
        font-family: monospace;
        font-size: 10px;
    }
</style>
""")

    parts.append(
        '<rect class="bg" x="0" y="0" '
        f'width="{width}" height="{height}" rx="8"/>'
    )

    parts.append(
        '<text class="title" x="18" y="25">'
        'Vivekk936@github: ~/contributions --graph'
        '</text>'
    )

    # Day labels
    day_names = ["Sun", "", "Tue", "", "Thu", "", "Sat"]

    for row, label in enumerate(day_names):
        if label:
            y = top + row * step + 10
            parts.append(
                f'<text class="label" x="8" y="{y}">'
                f'{label}</text>'
            )

    # Month labels
    previous_month = None

    for column in range(columns):
        date = first_sunday + timedelta(days=column * 7)

        if date > last_date:
            break

        month = date.strftime("%b")

        if month != previous_month:
            x = left + column * step
            parts.append(
                f'<text class="label" x="{x}" y="43">'
                f'{month}</text>'
            )

            previous_month = month

    # Contribution cells
    for index, date in enumerate(dates):
        column = index // 7
        row = index % 7

        date_string = date.isoformat()

        count = counts.get(date_string, 0)

        level = level_for_count(
            count,
            maximum
        )

        x = left + column * step
        y = top + row * step

        delay = min(index * 0.012, 5)

        parts.append(
            f'<rect class="cell" '
            f'x="{x}" y="{y}" '
            f'width="{cell}" height="{cell}" '
            f'rx="2" '
            f'fill="{PALETTE[level]}" '
            f'style="animation-delay:{delay:.3f}s">'
            f'<title>{esc(date_string)}: '
            f'{count} contributions</title>'
            f'</rect>'
        )

    # Legend
    legend_y = top + 7 * step + 25

    parts.append(
        f'<text class="legend" x="48" y="{legend_y}">'
        'Less'
        '</text>'
    )

    legend_x = 78

    for level in range(6):
        parts.append(
            f'<rect x="{legend_x}" '
            f'y="{legend_y - 10}" '
            f'width="13" height="13" rx="2" '
            f'fill="{PALETTE[level]}"/>'
        )

        legend_x += 17

    parts.append(
        f'<text class="legend" x="{legend_x + 3}" '
        f'y="{legend_y}">More</text>'
    )

    # Statistics
    total = data.get(
        "total_contributions",
        sum(counts.values())
    )

    current_streak = data.get(
        "current_streak",
        {}
    ).get("length", 0)

    longest_streak = data.get(
        "longest_streak",
        {}
    ).get("length", 0)

    best_day = data.get(
        "best_day",
        {}
    )

    stats_y = height - 12

    stats = (
        f"{total:,} contributions  •  "
        f"current streak: {current_streak}  •  "
        f"longest streak: {longest_streak}"
    )

    if best_day:
        stats += (
            f"  •  best day: "
            f"{best_day.get('count', 0)}"
        )

    parts.append(
        f'<text class="legend" x="18" y="{stats_y}">'
        f'{esc(stats)}</text>'
    )

    parts.append("</svg>")

    return "\n".join(parts)


def main():
    data = load_data()

    svg = build_heatmap(data)

    with open(
        OUT_PATH,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(svg)

    size_kb = os.path.getsize(OUT_PATH) / 1024

    print(
        f"wrote {OUT_PATH} "
        f"{size_kb:.1f} KB"
    )


if __name__ == "__main__":
    main()
