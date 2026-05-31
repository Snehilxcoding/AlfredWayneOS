import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEXT_ONLY = "--text" in sys.argv

from colorama import init as colorama_init, Fore, Style
colorama_init()

import config.settings as settings
if TEXT_ONLY:
    settings.TEXT_ONLY_MODE = True

from core.context           import get_full_context, build_context_summary
from core.greeting          import get_greeting, get_startup_banner, get_status_comment
from core.voice_output      import speak
from core.command_parser    import parse_command, Intent
from core.ai_engine         import ask_alfred
from core.logger            import log_action, log_conversation
from core.coding_assistant  import (
    run_command, read_file,
    get_project_structure, format_command_result,
    is_safe_command,
)
from memory.memory_manager import (
    load_memory, update_last_seen,
    add_conversation_summary, build_memory_context,
    log_workflow, build_longterm_context,
)
from memory.memory_extractor import extract_and_store
from automation.launcher import (
    open_application, open_website, search_web, create_text_file
)

history          = []
_last_api_call   = 0
_pending_command = None


def alfred_speak(text: str):
    """Speak a response. Always blocking — no threading conflicts."""
    speak(text, silent=settings.TEXT_ONLY_MODE)


def _api_cooldown(min_gap: float = 4.0):
    """Enforces minimum gap between API calls to avoid rate limits."""
    global _last_api_call
    elapsed = time.time() - _last_api_call
    if elapsed < min_gap:
        wait = min_gap - elapsed
        print(
            f"{Fore.YELLOW}[Alfred] Pacing API call "
            f"({wait:.1f}s)...{Style.RESET_ALL}"
        )
        time.sleep(wait)
    _last_api_call = time.time()


def get_input() -> str:
    """Get input from user — voice or text depending on mode."""
    if settings.TEXT_ONLY_MODE:
        try:
            print(f"\n{Fore.CYAN}You: {Style.RESET_ALL}", end="")
            return input().strip()
        except (KeyboardInterrupt, EOFError):
            return "goodbye"
    else:
        from core.voice_input import listen
        # Print instead of speak — avoids "Listening" being said out loud
        print(f"{Fore.CYAN}[Alfred] Listening...{Style.RESET_ALL}")
        text = listen()
        if not text:
            alfred_speak(f"I didn't catch that, {settings.USER_NAME}.")
            return ""
        return text


def handle(parsed: dict, ctx: dict, memory: dict) -> str:
    """Routes parsed intent to the correct handler."""
    global _pending_command

    intent = parsed["intent"]
    target = parsed.get("target")
    raw    = parsed.get("raw", "")
    import random

    # ── Pending command confirmation ──────────────────────────
    if _pending_command:
        cmd              = _pending_command
        _pending_command = None
        if raw.lower().strip() in ["yes", "y", "proceed", "go ahead", "do it"]:
            result = run_command(cmd, require_confirmation=False)
            log_action("run_command", cmd, success=result["success"])
            return format_command_result(result)
        else:
            return f"Understood, {settings.USER_NAME}. Command cancelled."

    # ── Farewell ─────────────────────────────────────────────
    if intent == Intent.FAREWELL:
        return f"Good night, {settings.USER_NAME}. I'll be here when you return."

    # ── Gratitude ────────────────────────────────────────────
    if intent == Intent.GRATITUDE:
        return random.choice([
            f"Think nothing of it, {settings.USER_NAME}.",
            f"Always a pleasure, {settings.USER_NAME}.",
            f"Happy to be of service, {settings.USER_NAME}.",
        ])

    # ── Time query ───────────────────────────────────────────
    if intent == Intent.TIME_QUERY:
        return (
            f"It is {ctx['time']} on {ctx['day']}, "
            f"{ctx['date']}, {settings.USER_NAME}."
        )

    # ── System info ──────────────────────────────────────────
    if intent == Intent.SYSTEM_INFO:
        s = ctx["system"]
        b = ctx.get("battery", {})
        msg = (
            f"CPU: {s['cpu_percent']}%. "
            f"RAM: {s['ram_used_gb']}GB of {s['ram_total_gb']}GB "
            f"used ({s['ram_percent']}%)."
        )
        if b.get("available"):
            plug = "charging" if b["plugged"] else "on battery"
            msg += f" Battery: {b['percent']}% ({plug})."
        msg += f" Internet: {'online' if ctx['online'] else 'offline'}."
        return msg

    # ── Open app ─────────────────────────────────────────────
    if intent == Intent.OPEN_APP:
        ok, msg = open_application(target or raw)
        log_workflow(memory, f"open_app:{target}")
        return msg

    # ── Open website ─────────────────────────────────────────
    if intent == Intent.OPEN_WEBSITE:
        _, msg = open_website(target or raw)
        return msg

    # ── Web search ───────────────────────────────────────────
    if intent == Intent.SEARCH_WEB:
        _, msg = search_web(target or raw)
        return msg

    # ── Create file ──────────────────────────────────────────
    if intent == Intent.CREATE_FILE:
        fname = target or "new_file"
        if "." not in fname:
            fname += ".txt"
        _, msg = create_text_file(fname)
        return msg

    # ── Run terminal command ──────────────────────────────────
    if intent == Intent.RUN_COMMAND:
        command = target or raw
        if is_safe_command(command):
            result = run_command(command, require_confirmation=False)
            log_action("run_command", command, success=result["success"])
            return format_command_result(result)
        else:
            _pending_command = command
            return (
                f"I'd like to run the following command, "
                f"{settings.USER_NAME}:\n\n"
                f"  {command}\n\n"
                f"Shall I proceed?"
            )

    # ── Read file ─────────────────────────────────────────────
    if intent == Intent.READ_FILE:
        filepath = target or raw
        result   = read_file(filepath)
        if result["success"]:
            content = result["content"]
            if len(content) > 2000:
                _api_cooldown()
                cs = build_context_summary(ctx)
                mc = build_memory_context(memory)
                lc = build_longterm_context(memory)
                summary_prompt = (
                    f"Master Wayne asked me to read this file: {filepath}\n\n"
                    f"Contents:\n\n{content[:3000]}\n\n"
                    f"Give a brief summary of what this file does."
                )
                return ask_alfred(summary_prompt, cs, mc, lc, history)
            return (
                f"Here are the contents of {filepath}, "
                f"{settings.USER_NAME}:\n\n{content}"
            )
        return result["message"]

    # ── Show project structure ────────────────────────────────
    if intent == Intent.SHOW_STRUCTURE:
        structure = get_project_structure(".")
        return (
            f"Here is your current project structure, "
            f"{settings.USER_NAME}:\n\n{structure}"
        )

    # ── Recalibrate microphone ────────────────────────────────
    if intent == "recalibrate_mic":
        from core.voice_input import recalibrate
        recalibrate()
        return f"Microphone recalibrated, {settings.USER_NAME}."

    # ── Default: ask AI ───────────────────────────────────────
    _api_cooldown()

    cs = build_context_summary(ctx)
    mc = build_memory_context(memory)
    lc = build_longterm_context(memory)

    response = ask_alfred(raw, cs, mc, lc, history)

    history.append({"role": "user",      "content": raw})
    history.append({"role": "assistant", "content": response})
    if len(history) > 30:
        history.pop(0)
        history.pop(0)

    log_conversation(raw, response, intent)
    add_conversation_summary(memory, raw, response)

    # Extract and store facts every 3rd AI turn
    if len(history) % 6 == 0:
        count = extract_and_store(raw, response)
        if count > 0:
            print(
                f"{Fore.GREEN}[Memory] {count} new fact(s) stored."
                f"{Style.RESET_ALL}"
            )

    return response


def main():
    print(Fore.YELLOW + get_startup_banner() + Style.RESET_ALL)
    mode = "Text-only" if settings.TEXT_ONLY_MODE else "Voice"
    print(Fore.CYAN + f"[{mode} mode | Type 'goodbye' to exit]\n" + Style.RESET_ALL)

    memory = load_memory()
    update_last_seen(memory)
    ctx = get_full_context()

    # Greeting — blocking, no threading conflicts
    greeting = get_greeting(ctx)
    status   = get_status_comment(ctx)
    alfred_speak(f"{greeting} {status}".strip())
    log_action("startup", "Alfred started")

    while True:
        try:
            ctx        = get_full_context()
            user_input = get_input()
            if not user_input:
                continue

            parsed   = parse_command(user_input)
            print(
                f"{Fore.YELLOW}[Intent: {parsed['intent']}]"
                f"{Style.RESET_ALL}"
            )
            response = handle(parsed, ctx, memory)
            alfred_speak(response)

            if parsed["intent"] == Intent.FAREWELL:
                log_action("shutdown", "Graceful exit")
                break

        except KeyboardInterrupt:
            alfred_speak(f"Until next time, {settings.USER_NAME}.")
            break
        except Exception as e:
            alfred_speak(
                f"I encountered an error, {settings.USER_NAME}: "
                f"{str(e)[:80]}"
            )
            log_action("error", str(e), success=False)
            continue


if __name__ == "__main__":
    main()