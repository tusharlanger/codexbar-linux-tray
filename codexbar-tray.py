#!/usr/bin/env python3
"""GNOME tray for codexbar — Claude session/weekly/sonnet/extras + cost."""

import json
import shutil
import subprocess
import threading
from datetime import datetime, timezone

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import GLib, Gtk, AyatanaAppIndicator3 as AppIndicator  # noqa: E402

REFRESH_SECONDS = 120
CODEXBAR = shutil.which("codexbar") or "/home/tushar-langer/.local/bin/codexbar"

THRESHOLD_WARN_PCT = 60
THRESHOLD_CRIT_PCT = 85
ICON_NORMAL = "utilities-system-monitor-symbolic"
ICON_WARN = "dialog-warning-symbolic"
ICON_CRIT = "dialog-error-symbolic"
BAR_WIDTH = 20  # unicode bar segments


def run_json(args):
    try:
        out = subprocess.run(
            [CODEXBAR, *args], capture_output=True, text=True, timeout=15
        )
        data = None
        for line in out.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, list):
                parsed = parsed[0] if parsed else None
            if parsed is not None:
                data = parsed
                break
        if out.returncode != 0:
            msg = None
            if isinstance(data, dict):
                err = data.get("error")
                if isinstance(err, dict):
                    msg = err.get("message")
                msg = msg or data.get("_error")
            return {"_error": msg or out.stderr.strip() or f"exit {out.returncode}"}
        if data is None:
            return {"_error": "empty"}
        return data
    except Exception as e:
        return {"_error": str(e)}


def color_for(pct):
    if pct is None:
        return "#9ca3af"
    if pct >= 90:
        return "#b91c1c"
    if pct >= 70:
        return "#ef4444"
    if pct >= 40:
        return "#f59e0b"
    return "#22c55e"


def esc(s):
    return GLib.markup_escape_text(str(s)) if s is not None else "—"


def fmt_money(v):
    return f"${v:,.2f}" if isinstance(v, (int, float)) else "—"


def fmt_tokens(v):
    if not isinstance(v, (int, float)):
        return "—"
    if v >= 1_000_000:
        return f"{v/1_000_000:.0f}M"
    if v >= 1_000:
        return f"{v/1_000:.0f}K"
    return str(int(v))


def bar(pct, width=BAR_WIDTH):
    pct = max(0, min(100, pct or 0))
    filled = int(round(width * pct / 100))
    return "▰" * filled + "▱" * (width - filled)


def parse_iso(iso_ts):
    if not iso_ts:
        return None
    try:
        if iso_ts.endswith("Z"):
            iso_ts = iso_ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def pace(used_pct, window_minutes, resets_at_iso):
    """Returns (label, projected_pct) describing pace vs reset.
    pace_delta = used_pct - elapsed_pct. Negative = behind, positive = ahead."""
    target = parse_iso(resets_at_iso)
    if target is None or not window_minutes:
        return ("—", None)
    now = datetime.now(timezone.utc)
    remaining_min = (target - now).total_seconds() / 60
    elapsed_min = window_minutes - remaining_min
    if elapsed_min <= 0:
        return ("Just reset", used_pct)
    elapsed_pct = elapsed_min / window_minutes * 100
    delta = used_pct - elapsed_pct
    projected = used_pct / max(elapsed_pct, 0.01) * 100
    if delta < -5:
        tail = "Lasts to reset" if projected <= 100 else "Runs out near reset"
        return (f"Behind ({delta:+.0f}%) · {tail}", projected)
    if delta > 5:
        if projected <= 100:
            return (f"Ahead (+{delta:.0f}%) · Lasts to reset", projected)
        # estimate when 100% will hit
        rate_per_min = used_pct / elapsed_min
        mins_to_100 = (100 - used_pct) / rate_per_min if rate_per_min > 0 else 0
        if mins_to_100 < 60:
            eta = f"{int(mins_to_100)}m"
        elif mins_to_100 < 1440:
            eta = f"{int(mins_to_100/60)}h {int(mins_to_100%60)}m"
        else:
            eta = f"{int(mins_to_100/1440)}d {int((mins_to_100%1440)/60)}h"
        return (f"Ahead (+{delta:.0f}%) · Runs out in {eta}", projected)
    return (f"On pace ({delta:+.0f}%) · Lasts to reset", projected)


def humanize_until(iso_ts):
    if not iso_ts:
        return "—"
    try:
        if iso_ts.endswith("Z"):
            iso_ts = iso_ts[:-1] + "+00:00"
        target = datetime.fromisoformat(iso_ts)
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        delta = target - datetime.now(timezone.utc)
        secs = int(delta.total_seconds())
        if secs <= 0:
            return "due"
        days, rem = divmod(secs, 86400)
        hours, rem = divmod(rem, 3600)
        mins = rem // 60
        if days:
            return f"{days}d {hours}h"
        if hours:
            return f"{hours}h {mins}m"
        return f"{mins}m"
    except Exception:
        return "—"


class CodexBarTray:
    def __init__(self):
        self.indicator = AppIndicator.Indicator.new(
            "codexbar-tray",
            ICON_NORMAL,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_label("…", "$000.00")
        self.menu = Gtk.Menu()
        loading = Gtk.MenuItem(label="Loading…")
        loading.set_sensitive(False)
        self.menu.append(loading)
        self.menu.show_all()
        self.indicator.set_menu(self.menu)
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.refresh()
        GLib.timeout_add_seconds(REFRESH_SECONDS, self.refresh)

    def refresh(self, *_):
        threading.Thread(target=self._worker, daemon=True).start()
        return True

    def _worker(self):
        results = {
            "claude_usage": run_json(
                ["usage", "--provider", "claude", "--source", "oauth", "--json"]
            ),
            "claude_cost": run_json(["cost", "--provider", "claude", "--json"]),
            "codex_cost": run_json(["cost", "--provider", "codex", "--json"]),
        }
        GLib.idle_add(self._render, results)

    def _add(self, text, sensitive=True):
        item = Gtk.MenuItem(label=text)
        item.set_sensitive(sensitive)
        self.menu.append(item)
        return item

    def _add_markup(self, markup, sensitive=False):
        item = Gtk.MenuItem()
        label = Gtk.Label()
        label.set_markup(markup)
        label.set_xalign(0)
        label.set_use_markup(True)
        item.add(label)
        item.set_sensitive(sensitive)
        self.menu.append(item)
        return item

    def _meter(self, name, glyph, pct, reset_human, pace_label):
        col = color_for(pct)
        bar_str = bar(pct)
        line1 = (
            f"<b>{esc(glyph)} {esc(name)}</b>   "
            f"<tt>{bar_str}</tt>  "
            f"<span foreground='{col}'><b>{pct}%</b></span>"
        )
        self._add_markup(line1)
        if reset_human:
            sub = f"<span foreground='#9ca3af' size='small'>      ↻ {esc(reset_human)}  ·  {esc(pace_label)}</span>"
            self._add_markup(sub)

    def _render(self, results):
        # Build a fresh menu each render — re-binding via set_menu()
        # is the only reliable way to refresh appindicator dbusmenu state.
        self.menu = Gtk.Menu()

        usage = results["claude_usage"]
        usage_err = usage.get("_error") or (usage.get("error") or {}).get("message")
        u = usage.get("usage") or {}
        primary = u.get("primary") or {}
        secondary = u.get("secondary") or {}
        tertiary = u.get("tertiary") or {}
        provider_cost = u.get("providerCost") or {}
        login = u.get("loginMethod", "—")

        # icon by worst-case usage %
        worst = max(primary.get("usedPercent") or 0, secondary.get("usedPercent") or 0)
        if worst >= THRESHOLD_CRIT_PCT:
            self.indicator.set_icon_full(ICON_CRIT, "high")
        elif worst >= THRESHOLD_WARN_PCT:
            self.indicator.set_icon_full(ICON_WARN, "warn")
        else:
            self.indicator.set_icon_full(ICON_NORMAL, "ok")

        # top-bar label = session %
        sess_pct = primary.get("usedPercent")
        self.indicator.set_label(
            f"{sess_pct}%" if isinstance(sess_pct, int) else "—",
            "100%",
        )

        plan = login.replace("Claude ", "") if isinstance(login, str) else "—"
        self._add_markup(
            f"<b><big>Claude</big></b>  <span foreground='#9ca3af'>· {esc(plan)}</span>"
        )

        if usage_err:
            low = usage_err.lower()
            if "429" in usage_err or "rate limit" in low or "rate_limit" in low:
                label = "rate limited — retrying"
                color = "#f59e0b"
            else:
                label = f"usage error: {usage_err[:60]}"
                color = "#ef4444"
            self._add_markup(
                f"<span foreground='{color}'>  {esc(label)}</span>"
            )
        else:
            sp = primary.get("usedPercent") or 0
            sp_pace, _ = pace(sp, primary.get("windowMinutes"), primary.get("resetsAt"))
            self._meter(
                "Session",
                "⏱",
                sp,
                humanize_until(primary.get("resetsAt")) + " left",
                sp_pace,
            )

            wp = secondary.get("usedPercent") or 0
            wp_pace, _ = pace(
                wp, secondary.get("windowMinutes"), secondary.get("resetsAt")
            )
            self._meter(
                "Weekly",
                "📅",
                wp,
                humanize_until(secondary.get("resetsAt")) + " left",
                wp_pace,
            )

            tp = tertiary.get("usedPercent") or 0
            if tp > 0:
                tp_pace, _ = pace(
                    tp,
                    tertiary.get("windowMinutes"),
                    tertiary.get("resetsAt") or secondary.get("resetsAt"),
                )
                self._meter("Sonnet", "✦", tp, None, tp_pace)

            if provider_cost:
                used = provider_cost.get("used") or 0
                limit = provider_cost.get("limit") or 0
                pct = int(round(100 * used / limit)) if limit else 0
                col = color_for(pct)
                period = provider_cost.get("period", "Monthly")
                self._add_markup(
                    f"<b>💳 Extra</b>  <span foreground='#9ca3af'>({esc(period)})</span>   "
                    f"<tt>{bar(pct)}</tt>  "
                    f"<span foreground='{col}'><b>{pct}%</b></span>"
                )
                self._add_markup(
                    f"<span foreground='#9ca3af' size='small'>      "
                    f"{esc(fmt_money(used))} / {esc(fmt_money(limit))}</span>"
                )

        self.menu.append(Gtk.SeparatorMenuItem())

        # ── Cost section
        cc = results["claude_cost"]
        cx = results["codex_cost"]
        self._add_markup(
            "<b><big>Cost</big></b>  <span foreground='#9ca3af'>· local logs</span>"
        )

        def cost_row(label, d):
            if "_error" in d:
                return
            today = fmt_money(d.get("sessionCostUSD"))
            today_t = fmt_tokens(d.get("sessionTokens"))
            m30 = fmt_money(d.get("last30DaysCostUSD"))
            m30_t = fmt_tokens(d.get("last30DaysTokens"))
            self._add_markup(
                f"<b>{esc(label)}</b>   "
                f"today <span foreground='#22c55e'>{esc(today)}</span> "
                f"<span foreground='#9ca3af' size='small'>· {esc(today_t)}</span>"
            )
            self._add_markup(
                f"<span foreground='#9ca3af' size='small'>         30d  {esc(m30)}  ·  {esc(m30_t)}</span>"
            )

        cost_row("Claude", cc)
        cost_row("Codex", cx)

        self.menu.append(Gtk.SeparatorMenuItem())
        ts = datetime.now().strftime("%H:%M:%S")
        self._add_markup(
            f"<span foreground='#9ca3af' size='small'>Updated {esc(ts)}</span>"
        )

        ref = Gtk.MenuItem(label="Refresh now")
        ref.connect("activate", self.refresh)
        self.menu.append(ref)

        dash = Gtk.MenuItem(label="Usage Dashboard")
        dash.connect(
            "activate",
            lambda _: subprocess.Popen(
                ["xdg-open", "https://claude.ai/settings/usage"]
            ),
        )
        self.menu.append(dash)

        status = Gtk.MenuItem(label="Status Page")
        status.connect(
            "activate",
            lambda _: subprocess.Popen(["xdg-open", "https://status.anthropic.com"]),
        )
        self.menu.append(status)

        self.menu.append(Gtk.SeparatorMenuItem())
        about = Gtk.MenuItem(label=f"CodexBar tray · {self._codexbar_version()}")
        about.set_sensitive(False)
        self.menu.append(about)

        q = Gtk.MenuItem(label="Quit")
        q.connect("activate", lambda _: Gtk.main_quit())
        self.menu.append(q)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)
        return False

    def _codexbar_version(self):
        try:
            out = subprocess.run(
                [CODEXBAR, "--version"], capture_output=True, text=True, timeout=5
            )
            return (
                out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "unknown"
            )
        except Exception:
            return "unknown"


def main():
    CodexBarTray()
    Gtk.main()


if __name__ == "__main__":
    main()
