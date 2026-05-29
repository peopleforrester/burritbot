# Running Chatbot Research (Non-Headless) on WSL2

## Prerequisites

You need a GUI-capable WSL2 setup so Playwright can open a real Chrome window.
Windows 11 has WSLg built in. Windows 10 needs an X server.

### Windows 11 (WSLg — no extra setup)

WSLg ships with Windows 11 22000+. Verify it works:

```bash
# Should show something like :0 or :1
echo $DISPLAY
```

If `$DISPLAY` is set, skip to **Step 1**.

### Windows 10 (manual X server)

Install [VcXsrv](https://sourceforge.net/projects/vcxsrv/) or [X410](https://x410.dev/) on the Windows side, then:

```bash
# Add to your ~/.bashrc or ~/.zshrc:
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
export LIBGL_ALWAYS_INDIRECT=1
```

Restart your shell and verify with `echo $DISPLAY`.

---

## Step 1 — Clone / pull the repo

```bash
cd ~/repos/events/Kubecon-NA-2026-Whitney-BurritoBot
git pull origin main
```

## Step 2 — Install dependencies

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync the project (installs playwright + all dev deps)
uv sync

# Install the Chromium browser binary for Playwright
uv run playwright install chromium

# Playwright also needs some system libraries:
uv run playwright install-deps chromium
```

## Step 3 — Run (non-headless, all targets)

```bash
# This opens a real Chrome window for each of the 19 targets.
# Each gets ONE lighthearted off-topic prompt — no adversarial behavior.
# ~5 minutes total (5s pause between targets, 15s wait for responses).
uv run python chatbot-research/research.py
```

The browser window will be visible. You'll see it navigate to each site,
find (or fail to find) the chat widget, type a prompt, and wait for a
response. Screenshots are captured automatically.

### Pause mode (recommended for best results)

Most chat widgets require manual interaction to open. Use `--pause` to
let the script navigate to each site, then manually open the chat widget
in the browser before the script auto-types the prompt:

```bash
uv run python chatbot-research/research.py --pause
uv run python chatbot-research/research.py --pause --target homedepot
```

For each target the script will:
1. Open the page and wait for widgets to load
2. Print a prompt in the terminal: "Open the chat widget manually..."
3. **You** click the chat button in the browser window
4. Press Enter in the terminal when the chat input is visible
5. The script finds the input, types the prompt, waits, and screenshots

This gives the best results because many chat widgets use anti-bot
heuristics that block automated opening but work fine once manually
triggered.

### Run a single target

```bash
uv run python chatbot-research/research.py --target homedepot
uv run python chatbot-research/research.py --target chipotle
uv run python chatbot-research/research.py --target dominos
```

### Available targets

chipotle, dominos, doordash, ubereats, delta, united, southwest,
american-airlines, target, bestbuy, walmart, homedepot, geico,
progressive, bankofamerica, marriott, hilton, tmobile, verizon

## Step 4 — Review results

Screenshots land in `chatbot-research/screenshots/` (committed to git).
JSON results land in `chatbot-research/results/` (committed to git).

```bash
# Regenerate the summary table from all result JSONs:
uv run python chatbot-research/research.py --summary-only

# View it:
cat chatbot-research/summary.md
```

After reviewing, manually set `"played_along": true` or `false` in each
result JSON — the script can't always tell from the DOM whether the bot
actually answered the off-topic question.

## Step 5 — Copy best screenshots to Windows

```bash
# From WSL2, your Windows desktop is at:
cp chatbot-research/screenshots/*-after.png /mnt/c/Users/YOUR_USERNAME/Desktop/
```

## What to expect

From the headless run, most chat widgets don't load or actively hide from
automated browsers. Non-headless will do better because:

- Real Chrome window bypasses most bot-detection heuristics
- Cookie consent banners render and get dismissed properly
- JavaScript-heavy lazy-loaded widgets fully initialize
- Iframe-embedded chats (Sprinklr, Intercom, Drift) load correctly

**Home Depot** is the most reliable target — its Sprinklr-based chat opens
consistently. In our headless testing it both refused (dance moves) and
played along (birthday toast), showing inconsistent guardrails.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `playwright install chromium` fails | Run `uv run playwright install-deps chromium` first for system libs |
| Browser window doesn't appear | Check `echo $DISPLAY` — needs WSLg or an X server |
| Site blocks / shows CAPTCHA | Skip it with `Ctrl+C`, move to the next target manually |
| Chat widget loads but script can't find input | The DOM selectors are heuristic. Open an issue or add a site-specific selector to `research.py` |
| `uv: command not found` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` then restart shell |
