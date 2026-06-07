# ABOUTME: Playwright-based research script that visits public chatbot widgets with lighthearted prompts.
# ABOUTME: Captures before/after screenshots and response text for talk-submission collateral.

"""Chatbot Dance Moves Research — screenshot capture for the CFP.

Usage:
    # Run all targets (one prompt each, round-robin):
    uv run python chatbot-research/research.py

    # Run a single target by name:
    uv run python chatbot-research/research.py --target chipotle

    # Run with headless browser (fallback when no display):
    uv run python chatbot-research/research.py --headless

    # Generate summary only (from existing results):
    uv run python chatbot-research/research.py --summary-only

Rules:
    - ONE prompt per chatbot. No repeat visits.
    - No prompt injection. No adversarial behavior.
    - Skip anything that requires login.
    - Use obviously fake data if asked for PII.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

logger = logging.getLogger("chatbot-research")

SCRIPT_DIR = Path(__file__).resolve().parent
TARGETS_FILE = SCRIPT_DIR / "targets.yaml"
SCREENSHOTS_DIR = SCRIPT_DIR / "screenshots"
RESULTS_DIR = SCRIPT_DIR / "results"
SUMMARY_FILE = SCRIPT_DIR / "summary.md"

# Fake PII for chatbots that ask before connecting to an agent.
FAKE_NAME = "Test User"
FAKE_EMAIL = "test@example.com"
FAKE_ORDER = "12345"

# Common selectors for chat widgets across sites. The script tries these
# in order; the first match wins. Site-specific overrides go in targets.yaml.
CHAT_OPEN_SELECTORS = [
    # --- Vendor-specific (most reliable — match exact widget implementations) ---
    # LivePerson / T-Mobile
    "#bubble",
    '#PrimaryCTALP',
    '[aria-label*="open up help chat" i]',
    '.chat-bubble-pri',
    "#lpChat",
    ".LPMcontainer button",
    ".LPMcontainer",
    '[id*="liveperson" i] button',
    '[class*="liveperson" i]',
    'div[id*="lpChat"] button',
    '[class*="LPM" i]',
    # Intercom
    "#intercom-container iframe",
    ".intercom-lightweight-app-launcher",
    # Drift
    "#drift-widget",
    ".drift-open-chat",
    # Zendesk
    "#launcher",
    ".zEWidget-launcher",
    # NICE CXone / inContact
    '[id*="cxone" i] button',
    '[class*="cxone" i]',
    # GEICO / generic embedded chat triggers
    '[class*="virtual-assistant" i]',
    '[id*="virtual-assistant" i]',

    # --- Text-based (match visible button text) ---
    'button:has-text("Chat with us")',
    'button:has-text("Chat Now")',
    'button:has-text("Chat")',
    'a:has-text("Chat with us")',
    'a:has-text("Chat Now")',
    'button:has-text("Message us")',
    'button:has-text("Message Us")',
    'button:has-text("Need help")',
    'button:has-text("Ask")',
    # Removed: Feedback buttons are surveys (Qualtrics/Medallia), not chatbots

    # --- Aria-based on buttons only ---
    'button[aria-label*="chat" i]',
    'button[aria-label*="assistant" i]',

    # --- Common class/id patterns ---
    "#chat-button",
    "#chat-widget",
    ".chat-button",
    ".chat-launcher",
    ".chat-toggle",
    '[data-testid="chat-button"]',
    '[data-testid="ChatButton"]',
    'div[class*="chat-bubble" i]',
    'div[class*="chatBubble" i]',
    'img[alt*="chat" i]',
    # Removed: feedback-tab and feedback id are surveys, not chat

    # --- Generic floating button bottom-right (last resort) ---
    'div[style*="position: fixed"][style*="bottom"][style*="right"] button',
]

CHAT_INPUT_SELECTORS = [
    # Placeholder-based (most reliable — matches actual input elements).
    'textarea[placeholder*="message" i]',
    'textarea[placeholder*="type" i]',
    'textarea[placeholder*="ask" i]',
    'textarea[placeholder*="question" i]',
    'input[placeholder*="message" i]',
    'input[placeholder*="type" i]',
    'input[placeholder*="ask" i]',
    'input[placeholder*="question" i]',
    # Aria-label on real input elements only (not divs or iframes).
    'textarea[aria-label*="message" i]',
    'textarea[aria-label*="type" i]',
    'textarea[aria-label*="chat" i]',
    'textarea[aria-label*="compose" i]',
    'input[aria-label*="message" i]',
    'input[aria-label*="type" i]',
    'input[aria-label*="chat" i]',
    'input[aria-label*="compose" i]',
    # Name-based.
    'textarea[name*="message" i]',
    'input[name*="message" i]',
    # Class/id-based.
    ".chat-input textarea",
    ".chat-input input",
    "#chat-input",
    '[data-testid="chat-input"]',
    # LivePerson / T-Mobile (exact classes from DOM inspection)
    'textarea.lpview_form_textarea',
    '.lpc_composer__text-area',
    '.lpc_composer textarea',
    '.lp-composer textarea',
    '.lp-composer input',
    '.lp_input_area textarea',
    '[class*="composer" i] textarea',
    '[class*="composer" i] input',
    '[id*="lpChat" i] textarea',
    '[id*="lpChat" i] input',
    # NICE / Five9 / Nuance
    '[class*="message-input" i] textarea',
    '[class*="message-input" i] input',
    '[class*="chat-compose" i] textarea',
    '[class*="user-input" i] textarea',
    '[class*="user-input" i] input',
    # Sprinklr (already works for Home Depot, but add more)
    '[class*="spr-" i] textarea',
    '[class*="spr-" i] input',
    # Generic role-based
    'textarea[role="textbox"]',
    '[role="textbox"][contenteditable="true"]',
    # Contenteditable as last resort.
    '[contenteditable="true"]',
]

CHAT_SEND_SELECTORS = [
    '[aria-label*="send" i]',
    'button:has-text("Send")',
    'button[type="submit"]',
    '.chat-send',
    '[data-testid="send-button"]',
    # LivePerson
    '.lp_send_button',
    '.lpc_composer__send-button',
]


def load_targets(path: Path = TARGETS_FILE) -> dict:
    """Load the targets YAML file and return the parsed dict."""
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text)


def pick_prompt(config: dict, index: int, product_action: str) -> str:
    """Round-robin a prompt template from the config and fill in the action."""
    templates = config["prompts"]
    template = templates[index % len(templates)]
    return template.replace("{product_action}", product_action)


async def try_selectors(page, selectors: list[str], *, timeout: int = 3000, label: str = ""):
    """Try a list of CSS/text selectors and return the first visible match."""
    for sel in selectors:
        try:
            locator = page.locator(sel).first
            if await locator.is_visible(timeout=timeout):
                # Reject tel: links and search inputs — these are not chat widgets.
                tag = await locator.evaluate("el => el.tagName") if locator else ""
                href = await locator.get_attribute("href") or "" if locator else ""
                input_type = await locator.get_attribute("type") or "" if locator else ""
                if href.startswith("tel:"):
                    logger.debug("[%s] skipping tel: link %r", label, sel)
                    continue
                if tag == "INPUT" and input_type == "search":
                    logger.debug("[%s] skipping search input %r", label, sel)
                    continue
                logger.info("[%s] selector matched: %s", label, sel)
                return locator
        except Exception:
            continue
    return None


async def check_for_iframe_chat(page) -> list:
    """Some sites embed the chat in an iframe. Return all matching frames.

    Returns a list so the caller can try each one until an input is found.
    """
    matches = []
    for frame in page.frames:
        name = frame.name or ""
        url = frame.url or ""
        if any(kw in name.lower() or kw in url.lower()
               for kw in ("chat", "widget", "intercom", "drift", "zendesk",
                          "salesforce", "livechat", "freshchat", "spr-",
                          "sprinklr", "ada", "kustomer", "helpshift",
                          "liveperson", "lpcdn", "nuance", "five9",
                          "egain", "genesys", "nice", "cxone",
                          "talkdesk", "gladly", "dixa", "gorgias",
                          "message", "assist", "bot", "virtual")):
            matches.append(frame)
    return matches


async def test_chatbot(
    page,
    name: str,
    url: str,
    prompt: str,
    notes: str | None = None,
    *,
    headless: bool = False,
) -> dict:
    """Visit a chatbot, send a prompt, capture screenshots and response text.

    Returns a result dict written to RESULTS_DIR.
    """
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
    result: dict = {
        "company": name,
        "url": url,
        "prompt": prompt,
        "timestamp": timestamp,
        "response": None,
        "played_along": None,
        "chat_found": False,
        "notes": notes,
    }

    ss_before = SCREENSHOTS_DIR / f"{name}-{timestamp}-before.png"
    ss_after = SCREENSHOTS_DIR / f"{name}-{timestamp}-after.png"
    ss_error = SCREENSHOTS_DIR / f"{name}-{timestamp}-error.png"

    try:
        logger.info("[%s] navigating to %s", name, url)
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        # Let deferred chat widgets and consent banners load.
        await page.wait_for_timeout(5000)

        # Dismiss common cookie/consent/modal banners that block interaction.
        # Try multiple rounds — some sites stack banners (cookie + health data).
        for _round in range(3):
            dismissed = False
            for consent_sel in (
                'button:has-text("Accept All")',
                'button:has-text("Allow All")',
                'button:has-text("Accept")',
                'button:has-text("Got it")',
                'button:has-text("I agree")',
                'button:has-text("Continue shopping")',
                'button:has-text("Continue")',
                'button:has-text("Reject All")',
                'button:has-text("Close")',
                'button:has-text("No thanks")',
                'button:has-text("Not now")',
                'button:has-text("Dismiss")',
                '[aria-label*="accept" i]',
                '[aria-label*="close" i]:not([aria-label*="chat" i]):not([class*="chat" i]):not([class*="LPM" i]):not([id*="close-icon" i])',
                '[aria-label*="dismiss" i]:not([class*="chat" i]):not([class*="LPM" i]):not([id*="close-icon" i])',
                "#onetrust-accept-btn-handler",
                "#onetrust-reject-all-handler",
                'button[id*="cookie" i]',
                # Target Health Data Consent
                'button:has-text("Continue Shopping")',
                # Generic modal close buttons
                'dialog button:has-text("Close")',
                '[role="dialog"] button[aria-label*="close" i]',
                '[role="dialog"] button:has-text("×")',
            ):
                try:
                    btn = page.locator(consent_sel).first
                    if await btn.is_visible(timeout=800):
                        await btn.click()
                        await page.wait_for_timeout(500)
                        dismissed = True
                        logger.info("[%s] dismissed banner with %r", name, consent_sel)
                        break
                except Exception:
                    continue
            if not dismissed:
                break

        await page.screenshot(path=str(ss_before), full_page=False)
        logger.info("[%s] before-screenshot saved", name)

        # --- Find the chat widget ---
        chat_opened = False

        # Step 1: try clicking an open-chat button on the main page.
        opener = await try_selectors(page, CHAT_OPEN_SELECTORS, timeout=2000, label=name)
        if opener:
            logger.info("[%s] found chat open button", name)
            await opener.click()
            await page.wait_for_timeout(6000)
            chat_opened = True

        # Step 2: check for iframe-embedded chat.
        chat_frames = await check_for_iframe_chat(page)

        # Step 3: find the input field.
        # Try each chat iframe's interior first, then fall back to the
        # main page. Never run selectors against the page if the match
        # would land on an <iframe> element — that causes fill() to fail.
        input_field = None
        context = page
        for cf in chat_frames:
            input_field = await try_selectors(cf, CHAT_INPUT_SELECTORS, timeout=3000)
            if input_field:
                context = cf
                logger.info("[%s] found input inside chat iframe %r", name, cf.name)
                break
        if not input_field:
            input_field = await try_selectors(page, CHAT_INPUT_SELECTORS, timeout=5000)
            context = page

        # Second pass: if we clicked a chat opener but didn't find input,
        # wait longer for the widget iframe/DOM to fully render, then retry.
        if not input_field and chat_opened:
            logger.info("[%s] chat opened but no input yet — waiting 5s for widget to render", name)
            await page.wait_for_timeout(5000)

            # Re-check iframes (new ones may have appeared)
            chat_frames = await check_for_iframe_chat(page)
            for cf in chat_frames:
                input_field = await try_selectors(cf, CHAT_INPUT_SELECTORS, timeout=5000)
                if input_field:
                    context = cf
                    logger.info("[%s] found input in iframe %r on second pass", name, cf.name)
                    break

            # Also try ALL iframes, not just keyword-matched ones
            if not input_field:
                for frame in page.frames:
                    if frame == page.main_frame:
                        continue
                    input_field = await try_selectors(frame, CHAT_INPUT_SELECTORS, timeout=2000)
                    if input_field:
                        context = frame
                        logger.info("[%s] found input in non-keyword iframe %r", name, frame.name or frame.url)
                        break

            # Last try on main page
            if not input_field:
                input_field = await try_selectors(page, CHAT_INPUT_SELECTORS, timeout=3000)
                context = page

        if not input_field:
            result["notes"] = (result["notes"] or "") + " | Could not find chat input field"
            logger.warning("[%s] no chat input found — screenshotting and moving on", name)
            await page.screenshot(path=str(ss_error), full_page=False)
            _save_result(result, name, timestamp)
            return result

        result["chat_found"] = True
        logger.info("[%s] chat input found — typing prompt", name)

        # Step 4: type the prompt and send.
        await input_field.click()
        # Use type() instead of fill() to trigger input events that
        # widget frameworks (LivePerson, etc.) listen for to enable
        # their send button. type() simulates real keystrokes.
        await input_field.type(prompt, delay=20)
        await page.wait_for_timeout(1000)

        # Try send button first, but only if it's enabled.
        sent = False
        send_btn = await try_selectors(context, CHAT_SEND_SELECTORS, timeout=2000, label=name)
        if send_btn:
            try:
                is_disabled = await send_btn.is_disabled(timeout=500)
                if not is_disabled:
                    await send_btn.click()
                    sent = True
            except Exception:
                pass
        if not sent:
            # Fallback: press Enter.
            await input_field.press("Enter")

        # Step 5: wait for a response (generous timeout — some bots are slow).
        logger.info("[%s] prompt sent — waiting up to 15s for response", name)
        await page.wait_for_timeout(15_000)

        # Step 6: screenshot the chat with the response visible.
        await page.screenshot(path=str(ss_after), full_page=False)
        logger.info("[%s] after-screenshot saved", name)

        # Step 7: try to extract response text.
        response_text = await _extract_response(context)
        if response_text:
            result["response"] = response_text
            logger.info("[%s] response captured (%d chars)", name, len(response_text))
        else:
            result["notes"] = (result["notes"] or "") + " | Could not extract response text"
            logger.warning("[%s] could not extract response text", name)

    except Exception as exc:
        result["notes"] = (result["notes"] or "") + f" | Error: {exc}"
        logger.error("[%s] error: %s", name, exc)
        try:
            await page.screenshot(path=str(ss_error), full_page=False)
        except Exception:
            pass

    _save_result(result, name, timestamp)
    return result


async def _extract_response(context) -> str | None:
    """Best-effort extraction of the chatbot's last response text."""
    # Common response container selectors.
    for sel in (
        # LivePerson
        '.lp_agent .lp_title_text',
        '.lpc_message_agent .lpc_message__text',
        '[id*="lp_line_bubble"] .lp_title_text',
        # Sprinklr (Home Depot)
        '.spr-message-body',
        # Generic
        ".chat-message:last-child",
        ".message-bubble:last-child",
        '[data-testid="bot-message"]:last-child',
        ".bot-response:last-child",
        ".agent-message:last-child",
        ".chat-response:last-child",
        '[class*="botMessage"]:last-of-type',
        '[class*="agent"]:last-of-type',
        '[class*="response"]:last-of-type',
    ):
        try:
            el = context.locator(sel).last
            if await el.is_visible(timeout=1000):
                text = await el.inner_text(timeout=2000)
                if text and len(text.strip()) > 10:
                    return text.strip()
        except Exception:
            continue
    return None


def _save_result(result: dict, name: str, timestamp: str) -> None:
    """Write a result JSON to the results directory."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{name}-{timestamp}.json"
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    logger.info("[%s] result saved to %s", name, path.name)


def generate_summary() -> str:
    """Read all result JSONs and produce a markdown summary."""
    results: list[dict] = []
    for p in sorted(RESULTS_DIR.glob("*.json")):
        results.append(json.loads(p.read_text(encoding="utf-8")))

    played_along: list[dict] = []
    refused: list[dict] = []
    no_chat: list[dict] = []

    for r in results:
        if not r.get("chat_found"):
            no_chat.append(r)
        elif r.get("played_along") is True:
            played_along.append(r)
        elif r.get("played_along") is False:
            refused.append(r)
        else:
            # Unclassified — put in played_along bucket with a note.
            played_along.append(r)

    lines = [
        "# Chatbot Dance Moves Research — Results\n",
        f"*Generated {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*\n",
        "",
        "## Played Along (off-topic response given)\n",
        "| Company | Prompt Used | Response Summary | Screenshot |",
        "|---------|------------|------------------|------------|",
    ]
    for r in played_along:
        resp = (r.get("response") or "see screenshot")[:80]
        ss = f"{r['company']}-{r['timestamp']}-after.png"
        lines.append(f"| {r['company']} | {r['prompt'][:60]}... | {resp} | {ss} |")

    lines += [
        "",
        "## Refused (redirected to on-topic)\n",
        "| Company | Prompt Used | How It Refused | Screenshot |",
        "|---------|------------|----------------|------------|",
    ]
    for r in refused:
        resp = (r.get("response") or "see screenshot")[:80]
        ss = f"{r['company']}-{r['timestamp']}-after.png"
        lines.append(f"| {r['company']} | {r['prompt'][:60]}... | {resp} | {ss} |")

    lines += [
        "",
        "## No Chat Widget Found\n",
        "| Company | URL | Notes |",
        "|---------|-----|-------|",
    ]
    for r in no_chat:
        notes = (r.get("notes") or "").strip(" |")
        lines.append(f"| {r['company']} | {r['url']} | {notes} |")

    lines += [
        "",
        "## Best Screenshots for Talk\n",
        "*Review the `screenshots/` directory and fill in manually:*\n",
        "1. [company] — [why this screenshot is gold]",
        "2. ...",
        "",
    ]

    return "\n".join(lines)


async def run(
    targets: list[dict],
    prompts: list[str],
    *,
    headless: bool = False,
) -> list[dict]:
    """Run the research against a list of targets."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error(
            "playwright is not installed. Run: uv add --dev playwright && "
            "uv run playwright install chromium"
        )
        sys.exit(1)

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        browser_context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )

        for i, target in enumerate(targets):
            prompt = pick_prompt(
                {"prompts": prompts},
                i,
                target["product_action"],
            )
            page = await browser_context.new_page()
            try:
                result = await test_chatbot(
                    page,
                    name=target["name"],
                    url=target["url"],
                    prompt=prompt,
                    notes=target.get("notes"),
                    headless=headless,
                )
                results.append(result)
            finally:
                await page.close()

            # Manually paced — 5s between targets.
            if i < len(targets) - 1:
                logger.info("--- pausing 5s before next target ---")
                await asyncio.sleep(5)

        await browser.close()

    return results


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Chatbot Dance Moves Research — screenshot capture",
    )
    parser.add_argument(
        "--target",
        help="Run only this target (by name from targets.yaml)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (some chatbots detect this)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Generate summary.md from existing results without running browsers",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.summary_only:
        summary = generate_summary()
        SUMMARY_FILE.write_text(summary, encoding="utf-8")
        logger.info("Summary written to %s", SUMMARY_FILE)
        return

    config = load_targets()
    targets = config["targets"]
    prompts = config["prompts"]

    if args.target:
        targets = [t for t in targets if t["name"] == args.target]
        if not targets:
            logger.error("Target %r not found in targets.yaml", args.target)
            sys.exit(1)

    results = asyncio.run(run(targets, prompts, headless=args.headless))

    # Generate summary after all runs.
    summary = generate_summary()
    SUMMARY_FILE.write_text(summary, encoding="utf-8")
    logger.info("Summary written to %s", SUMMARY_FILE)
    logger.info("Done. %d targets attempted.", len(results))


if __name__ == "__main__":
    main()
