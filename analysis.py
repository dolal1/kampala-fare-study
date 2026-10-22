# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "matplotlib>=3.9", "tabulate>=0.9"]
# ///
"""Kampala ride-hailing fare and wait-time study.

    uv run analysis.py            reads data/quotes.csv and data/routes.csv, writes out/
    uv run analysis.py --sample   runs on made-up rows, writes out/sample/ (to test the pipeline)
    uv run analysis.py --focus Bolt   charts Bolt (default SafeBoda) against its cheapest rival

Each row of quotes.csv is one fare quote read off an app's booking screen before
confirming: no trip has to be taken. See README.md for the logging method.
"""

import argparse
import random
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
APPS = ["SafeBoda", "Bolt", "Faras"]
# Colour follows the app, never its rank in a chart.
COLOURS = {"SafeBoda": "#2a78d6", "Bolt": "#eb6834", "Faras": "#1baf7a"}
BANDS = ["Morning peak", "Midday", "Evening peak", "Night"]
SURFACE, INK, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#898781", "#e1e0d9", "#c3c2b7"


def time_band(hhmm: str) -> str:
    hour = int(str(hhmm).split(":")[0])
    if 7 <= hour < 10:
        return "Morning peak"
    if 10 <= hour < 16:
        return "Midday"
    if 16 <= hour < 20:
        return "Evening peak"
    return "Night"


def sample_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Made-up routes and quotes with the real schema. Never a finding."""
    rng = random.Random(7)
    routes = pd.DataFrame(
        {"route_id": list("ABCDEF"), "origin": [f"Origin {r}" for r in "ABCDEF"],
         "destination": [f"Destination {r}" for r in "ABCDEF"], "km": [3.2, 5.5, 7.8, 9.4, 12.1, 4.6]}
    )
    base = {"SafeBoda": 950, "Bolt": 900, "Faras": 870}
    peak = {"Morning peak": 1.15, "Midday": 1.0, "Evening peak": 1.25, "Night": 1.1}
    times = {"Morning peak": "08:10", "Midday": "13:00", "Evening peak": "18:20", "Night": "21:30"}
    rows = []
    for day in range(1, 5):
        for _, r in routes.iterrows():
            for band in BANDS:
                for app in APPS:
                    fare = (1500 + base[app] * r.km) * peak[band] * rng.uniform(0.9, 1.1)
                    rows.append({"date": f"2026-10-{12 + day}", "time": times[band], "route_id": r.route_id,
                                 "app": app, "vehicle": "boda", "fare_ugx": round(fare, -2),
                                 "eta_min": max(1, round(rng.gauss(4 if band == "Midday" else 6, 2))),
                                 "surge_shown": "n", "notes": ""})
    return pd.DataFrame(rows), routes


def load(sample: bool) -> pd.DataFrame:
    if sample:
        quotes, routes = sample_data()
    else:
        quotes = pd.read_csv(HERE / "data" / "quotes.csv")
        routes = pd.read_csv(HERE / "data" / "routes.csv")
        if quotes.empty:
            sys.exit("data/quotes.csv has no rows yet. Log some quotes, or run with --sample.")
    df = quotes.merge(routes, on="route_id", how="left", validate="many_to_one")
    missing = sorted(df.loc[df.km.isna(), "route_id"].unique())
    if missing:
        sys.exit(f"No distance in data/routes.csv for route(s): {', '.join(missing)}")
    unknown = sorted(set(df.app) - set(APPS))
    if unknown:
        sys.exit(f"Unknown app name(s) in quotes.csv: {', '.join(unknown)}. Use one of {APPS}.")
    df["band"] = pd.Categorical(df.time.map(time_band), BANDS, ordered=True)
    df["ugx_per_km"] = df.fare_ugx / df.km
    return df


def style(ax, title: str, ylabel: str) -> None:
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=12)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)


def grouped_bars(table: pd.DataFrame, title: str, ylabel: str, path: Path, stamp: str) -> None:
    """One group per row of `table`, one bar per app column."""
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURFACE)
    apps = [a for a in APPS if a in table.columns]
    width = 0.8 / len(apps)
    for i, app in enumerate(apps):
        xs = [x + (i - (len(apps) - 1) / 2) * width for x in range(len(table))]
        ax.bar(xs, table[app], width=width * 0.9, color=COLOURS[app], label=app)
    ax.set_xticks(range(len(table)), [str(x) for x in table.index])
    style(ax, title, ylabel)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, ncols=len(apps), loc="upper left",
              bbox_to_anchor=(0, 1.0))
    ax.set_ylim(0, table[apps].max().max() * 1.18)
    if stamp:
        fig.text(0.99, 0.01, stamp, ha="right", va="bottom", fontsize=8, color=MUTED)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def premiums(by_route: pd.DataFrame) -> pd.DataFrame:
    """Each app's median fare against the cheapest other app's, per route (%)."""
    apps = [a for a in APPS if a in by_route.columns]
    return pd.DataFrame(
        {app: (by_route[app] / by_route.drop(columns=app).min(axis=1) - 1) * 100 for app in apps}
    )


def premium_chart(premium: pd.Series, app: str, path: Path, stamp: str) -> None:
    """One app's median fare against the cheapest rival's, per route."""
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURFACE)
    ax.bar(range(len(premium)), premium.values, width=0.6, color=COLOURS[app])
    ax.axhline(0, color=AXIS, linewidth=1)
    ax.set_xticks(range(len(premium)), premium.index)
    for x, v in enumerate(premium.values):
        ax.annotate(f"{v:+.0f}%", (x, v), xytext=(0, 4 if v >= 0 else -12), textcoords="offset points",
                    ha="center", fontsize=9, color=INK)
    style(ax, f"{app} fare against the cheapest rival, by route", "Difference in median fare (%)")
    ax.spines["bottom"].set_visible(False)
    pad = max(5, premium.abs().max() * 0.25)
    ax.set_ylim(min(0, premium.min()) - pad, max(0, premium.max()) + pad)
    if stamp:
        fig.text(0.99, 0.01, stamp, ha="right", va="bottom", fontsize=8, color=MUTED)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="run on made-up rows")
    ap.add_argument("--vehicle", default="boda", choices=["boda", "car"], help="default boda")
    ap.add_argument("--focus", default="SafeBoda", choices=APPS,
                    help="app to chart against its cheapest rival (default SafeBoda)")
    args = ap.parse_args()

    df = load(args.sample)
    df = df[df.vehicle == args.vehicle]
    if df.empty:
        sys.exit(f"No {args.vehicle} quotes to analyse.")
    out = HERE / "out" / ("sample" if args.sample else "")
    out.mkdir(parents=True, exist_ok=True)
    stamp = "SAMPLE DATA - not a finding" if args.sample else ""

    per_km = df.pivot_table(index="band", columns="app", values="ugx_per_km", aggfunc="median", observed=True)
    eta = df.pivot_table(index="band", columns="app", values="eta_min", aggfunc="median", observed=True)
    by_route = df.pivot_table(index="route_id", columns="app", values="fare_ugx", aggfunc="median")
    counts = df.pivot_table(index="band", columns="app", values="fare_ugx", aggfunc="count", observed=True)

    grouped_bars(per_km, "Median fare per km, by time of day", "UGX per km", out / "fare_per_km.png", stamp)
    grouped_bars(eta, "Median pickup ETA, by time of day", "Minutes", out / "eta.png", stamp)

    lines = [f"# Summary ({args.vehicle})", ""]
    if stamp:
        lines += [f"**{stamp}.**", ""]
    lines += [f"{len(df)} quotes, {df.route_id.nunique()} routes, {df.date.nunique()} days, "
              f"{df.date.min()} to {df.date.max()}.", ""]
    if len(by_route.columns) > 1:
        premium = premiums(by_route)
        if args.focus in premium:
            focus = premium[args.focus].dropna().sort_values()
            premium_chart(focus, args.focus, out / f"premium_{args.focus.lower()}.png", stamp)
        lines += ["## Each app against the cheapest rival, by route (%)", "",
                  "Positive means pricier than the cheapest other app on that route.", "",
                  premium.round(1).to_markdown(), ""]
    lines += ["## Median fare per km (UGX)", "", per_km.round(0).to_markdown(), "",
              "## Median pickup ETA (minutes)", "", eta.round(1).to_markdown(), "",
              "## Median fare by route (UGX)", "", by_route.round(0).to_markdown(), "",
              "## Quotes per cell", "", counts.to_markdown(), ""]
    (out / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"Wrote {out}/")


if __name__ == "__main__":
    main()
