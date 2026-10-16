# Orbit UI

An interface-design Skill for AI agents, focused on **space-tech** UI. It first lays out several genuinely different space directions — Mission Control, Orbital Blueprint, Deepfield, Frontier (NASA-punk, after the game Starfield), Holographic HUD, Space-Race Retro — for you to compare, then refines the chosen one against real screenshots, instead of shipping "black background + neon cyan + particles" every time.

For aerospace sites, launch livestream pages, satellite data platforms, ops dashboards, sci-fi game HUDs and single components.

[中文](README.md)

## Principles

- **Instrument honesty**: every line measures something, every glow comes from a real signal; at most two decorative languages per page.
- **Translate "techy"** into decisions: tabular monospace numbers, meaningful lines, accent area under 5%.
- **Three directions that really differ**: layout, type, color and hero visual — any two directions share at most one.
- **Ask in words first**, build side-by-side first screens only when you want to see them.
- **One memorable moment**, everything else quiet. Screenshot on desktop and mobile, then subtract.

## Install

```bash
npx skills add pei92/orbit-ui
```

Or copy this folder into your agent's skills directory (Claude Code: `~/.claude/skills/orbit-ui`).

## Try it

```bash
python scripts/build_explorer.py examples/launch-page/manifest.json --force
```

```bash
node scripts/shoot.mjs examples/components.html --size both
```

```bash
python -m unittest discover tests
```

Workflow structure inspired by [oil-oil/oil-ui](https://github.com/oil-oil/oil-ui) (MIT); all text, styles and scripts here are rewritten for the space-tech focus.

## License

MIT
