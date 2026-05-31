import random
from config.settings import USER_NAME

def get_greeting(ctx):
    period  = ctx.get("period", "day")
    is_late = ctx.get("working_late", False)
    weekend = ctx.get("is_weekend", False)

    if is_late:
        return random.choice([
            f"Working late again, {USER_NAME}? I've prepared the study.",
            f"The city never sleeps, and neither do you, {USER_NAME}.",
            f"Past midnight, {USER_NAME}. Shall I brew some tea?",
        ])
    if period == "morning":
        opts = [
            f"Good morning, {USER_NAME}. Ready to face the day?",
            f"Good morning, {USER_NAME}. The manor is yours.",
        ]
        if weekend:
            opts.append(f"Good morning, {USER_NAME}. The weekend — though I suspect you still have work to do.")
        return random.choice(opts)
    if period == "afternoon":
        return random.choice([
            f"Good afternoon, {USER_NAME}. What shall we accomplish?",
            f"Good afternoon, {USER_NAME}. At your service.",
        ])
    if period == "evening":
        return random.choice([
            f"Good evening, {USER_NAME}. Shall we review the day?",
            f"Good evening, {USER_NAME}. The night is still young.",
        ])
    return random.choice([
        f"Still at it, {USER_NAME}? I'll keep the lights on.",
        f"Working through the night, {USER_NAME}.",
    ])

def get_startup_banner():
    return """
╔══════════════════════════════════════════════╗
║       A L F R E D   W A Y N E   O S         ║
║             Phase 1 — Alfred Core            ║
╚══════════════════════════════════════════════╝
"""

def get_status_comment(ctx):
    comments = []
    if not ctx.get("online"):
        comments.append(f"We are currently offline, {USER_NAME}.")
    b = ctx.get("battery", {})
    if b.get("low"):
        comments.append(f"Battery at {b['percent']}%, {USER_NAME}. Please connect the charger.")
    return " ".join(comments)