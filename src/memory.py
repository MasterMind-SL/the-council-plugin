"""Three-tier, budget-aware, goal-filtered memory engine for The Council."""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Topic extraction (zero-dependency, keyword-based)
# ---------------------------------------------------------------------------
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "database": ["database", "sql", "query", "schema", "migration", "postgres", "mysql", "sqlite", "orm", "table", "index", "pgbouncer", "pool"],
    "authentication": ["auth", "login", "token", "jwt", "oauth", "session", "password", "credential", "sso", "saml"],
    "api": ["api", "endpoint", "rest", "graphql", "grpc", "route", "request", "response", "middleware", "cors", "rate-limit"],
    "frontend": ["react", "vue", "angular", "component", "css", "dom", "ui", "ux", "layout", "responsive", "tailwind"],
    "performance": ["performance", "cache", "latency", "throughput", "optimize", "bottleneck", "profil", "benchmark", "pool", "batch"],
    "security": ["security", "vulnerability", "xss", "injection", "encrypt", "hash", "cert", "tls", "ssl", "firewall", "audit"],
    "testing": ["test", "spec", "assert", "mock", "fixture", "coverage", "ci", "integration", "unit", "e2e"],
    "infrastructure": ["deploy", "docker", "kubernetes", "k8s", "terraform", "aws", "cloud", "container", "pipeline", "cd", "ci"],
    "architecture": ["architecture", "pattern", "monolith", "microservice", "monorepo", "module", "layer", "decouple", "interface", "abstract"],
    "data": ["data", "etl", "pipeline", "stream", "kafka", "queue", "event", "message", "pubsub", "webhook"],
}


def extract_topics(text: str, topic_index: dict | None = None) -> set[str]:
    """Extract topic tags from text using keyword matching."""
    words = set(re.findall(r"[a-z0-9-]+", text.lower()))
    topics = set()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in words or any(kw in w for w in words) for kw in keywords):
            topics.add(topic)
    return topics


# ---------------------------------------------------------------------------
# Importance scoring
# ---------------------------------------------------------------------------
def compute_importance(
    base: int,
    created: str,
    referenced_count: int = 0,
    superseded: bool = False,
) -> int:
    """Compute importance score for a memory entry."""
    try:
        created_date = datetime.fromisoformat(created)
        days_old = (datetime.now(timezone.utc) - created_date).days
    except (ValueError, TypeError):
        days_old = 0

    # Recency bonus
    if days_old <= 7:
        recency = 2
    elif days_old <= 30:
        recency = 1
    else:
        recency = 0

    # Reference bonus (max +3)
    ref_bonus = min(referenced_count, 3)

    # Staleness penalty
    staleness = 0
    if superseded:
        staleness = 5

    score = base + recency + ref_bonus - staleness
    return max(1, min(10, score))


# ---------------------------------------------------------------------------
# Relevance scoring (goal-aware retrieval)
# ---------------------------------------------------------------------------
def compute_relevance(entry: dict, goal: str, topic_index: dict | None = None) -> float:
    """Score how relevant a memory entry is to the current goal."""
    entry_topics = set(entry.get("topics", []))
    goal_topics = extract_topics(goal, topic_index)

    # Topic overlap
    if entry_topics:
        topic_score = len(entry_topics & goal_topics) / max(len(entry_topics), 1)
    else:
        topic_score = 0.0

    # Keyword overlap
    goal_words = set(re.findall(r"[a-z0-9-]+", goal.lower()))
    entry_text = entry.get("text", "") + " " + entry.get("headline", "")
    entry_words = set(re.findall(r"[a-z0-9-]+", entry_text.lower()))
    if goal_words:
        keyword_overlap = len(goal_words & entry_words) / max(len(goal_words), 1)
    else:
        keyword_overlap = 0.0

    # Recency factor
    try:
        created = datetime.fromisoformat(entry.get("created", ""))
        days_old = (datetime.now(timezone.utc) - created).days
    except (ValueError, TypeError):
        days_old = 0
    recency = max(0.0, 0.3 - (days_old * 0.01))

    return topic_score * 0.5 + keyword_overlap * 0.3 + recency * 0.2


# ---------------------------------------------------------------------------
# Token estimation (simple word-based heuristic)
# ---------------------------------------------------------------------------
def estimate_tokens(text: str) -> int:
    """Rough token count: ~0.75 words per token for English."""
    return max(1, int(len(text.split()) * 1.33))


# ---------------------------------------------------------------------------
# Memory file I/O
# ---------------------------------------------------------------------------
def _memory_dir(project_dir: str) -> Path:
    return Path(project_dir) / ".council" / "memory"


def load_index(project_dir: str) -> dict:
    """Load Tier 0 index. Returns empty structure if missing."""
    index_path = _memory_dir(project_dir) / "index.json"
    if index_path.exists():
        try:
            return json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "version": 1,
        "consultation_count": 0,
        "last_updated": "",
        "compaction_watermark": "",
        "recent_decisions": [],
        "pinned": [],
        "topic_index": {},
    }


def save_index(project_dir: str, index: dict) -> None:
    """Write Tier 0 index."""
    index_path = _memory_dir(project_dir) / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def load_active(project_dir: str, role: str) -> dict:
    """Load Tier 1 active memory for a role."""
    active_path = _memory_dir(project_dir) / f"{role}-active.json"
    if active_path.exists():
        try:
            return json.loads(active_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"version": 1, "role": role, "entries": []}


def save_active(project_dir: str, role: str, data: dict) -> None:
    """Write Tier 1 active memory for a role."""
    active_path = _memory_dir(project_dir) / f"{role}-active.json"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Budget-aware memory retrieval
# ---------------------------------------------------------------------------
def build_memory_response(
    project_dir: str,
    goal: str = "",
    max_tokens: int = 4000,
    role_filter: str = "",
) -> str:
    """Build budget-aware memory response. Never exceeds max_tokens.

    Packing order:
    1. Always: Tier 0 index (~200-500 tokens)
    2. Goal-relevant Tier 1 entries, sorted by relevance*0.6 + importance*0.4
    3. If budget remains: top non-relevant entries by importance alone
    4. If budget tight (< 1000 after index): index + top 3 as 1-line summaries
    """
    index = load_index(project_dir)
    topic_idx = index.get("topic_index", {})

    # --- Tier 0: Index section (always included) ---
    tier0_parts = []
    tier0_parts.append(f"## Your Memory ({index.get('consultation_count', 0)} consultations, budget: {max_tokens} tokens)\n")

    # Pinned items
    pinned = index.get("pinned", [])
    if pinned:
        tier0_parts.append("### Critical (always remember)")
        for p in pinned:
            tier0_parts.append(f"- [pinned] {p.get('text', '')}")
        tier0_parts.append("")

    # Recent decisions
    recent = index.get("recent_decisions", [])[-3:]
    if recent:
        tier0_parts.append("### Recent decisions")
        for d in recent:
            tier0_parts.append(f"- {d.get('session_id', '?')}: {d.get('goal_oneliner', '')} -> {d.get('decision_oneliner', '')}")
        tier0_parts.append("")

    tier0_text = "\n".join(tier0_parts)
    tier0_tokens = estimate_tokens(tier0_text)
    remaining = max_tokens - tier0_tokens

    # --- Budget tight? Minimal response ---
    if remaining < 1000:
        roles = [role_filter] if role_filter else ["strategist", "critic", "hub"]
        summaries = []
        for role in roles:
            active = load_active(project_dir, role)
            entries = active.get("entries", [])
            top3 = sorted(entries, key=lambda e: e.get("importance", 0), reverse=True)[:3]
            for e in top3:
                summaries.append(f"- {e.get('id', '?')} [imp:{e.get('importance', 0)}]: {e.get('headline', e.get('text', '')[:80])}")
        if summaries:
            return tier0_text + "### Key memories (budget-limited)\n" + "\n".join(summaries)
        return tier0_text.strip()

    # --- Tier 1: Active memory entries ---
    roles = [role_filter] if role_filter else ["strategist", "critic", "hub"]
    all_entries: list[tuple[float, dict]] = []

    for role in roles:
        active = load_active(project_dir, role)
        for entry in active.get("entries", []):
            if goal:
                relevance = compute_relevance(entry, goal, topic_idx)
            else:
                relevance = 0.0
            importance = entry.get("importance", 5) / 10.0
            score = relevance * 0.6 + importance * 0.4
            all_entries.append((score, entry))

    # Sort by combined score descending
    all_entries.sort(key=lambda x: x[0], reverse=True)

    # Pack entries within budget
    relevant_parts = []
    other_parts = []
    used_tokens = 0
    relevance_threshold = 0.2

    for score, entry in all_entries:
        # Choose detail level based on remaining budget
        if remaining - used_tokens > 2000:
            text = entry.get("text", "")
        else:
            text = entry.get("headline", entry.get("text", "")[:80])

        line = f"- {entry.get('id', '?')} [imp:{entry.get('importance', 0)}]: {text}"
        line_tokens = estimate_tokens(line)

        if used_tokens + line_tokens > remaining:
            break

        if score >= relevance_threshold and goal:
            relevant_parts.append(line)
        else:
            other_parts.append(line)
        used_tokens += line_tokens

    # Assemble response
    sections = [tier0_text]
    if relevant_parts:
        sections.append("### Relevant to this goal")
        sections.extend(relevant_parts)
        sections.append("")
    if other_parts:
        sections.append("### Other important context")
        sections.extend(other_parts)
        sections.append("")

    return "\n".join(sections).strip()


# ---------------------------------------------------------------------------
# Recording: update all three tiers
# ---------------------------------------------------------------------------
def _next_id(role: str, active: dict) -> str:
    """Generate next memory entry ID."""
    entries = active.get("entries", [])
    max_num = 0
    for e in entries:
        eid = e.get("id", "")
        parts = eid.rsplit("-", 1)
        if len(parts) == 2:
            try:
                max_num = max(max_num, int(parts[1]))
            except ValueError:
                pass
    return f"M-{role}-{max_num + 1:03d}"


def record_consultation(
    project_dir: str,
    session_id: str,
    goal: str,
    strategist_summary: str,
    critic_summary: str,
    decision: str,
    strategist_lesson: str = "",
    critic_lesson: str = "",
    hub_lesson: str = "",
    importance: int = 5,
    pin: bool = False,
) -> str:
    """Record consultation results across all three memory tiers.

    Tier 0: Update index (consultation count, recent decisions, topic index)
    Tier 1: Add entries to active memory files
    Tier 2: Append to archive logs
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    date_str = now.strftime("%Y-%m-%d")
    memory = _memory_dir(project_dir)
    memory.mkdir(parents=True, exist_ok=True)

    goal_topics = list(extract_topics(goal))

    # --- Tier 2: Append to archive (never modified, always grows) ---
    # decisions.md
    decisions_path = memory / "decisions.md"
    with open(decisions_path, "a", encoding="utf-8") as f:
        if decisions_path.stat().st_size == 0:
            f.write("# Hub Decision Record\n")
        f.write(f"\n## {date_str} — {goal[:80]} (session {session_id})\n\n")
        f.write(f"- **Goal:** {goal}\n")
        f.write(f"- **Strategist:** {strategist_summary}\n")
        f.write(f"- **Critic:** {critic_summary}\n")
        f.write(f"- **Decision:** {decision}\n\n")

    # lessons.jsonl
    lessons_path = memory / "lessons.jsonl"
    with open(lessons_path, "a", encoding="utf-8") as f:
        for source, lesson in [("strategist", strategist_lesson), ("critic", critic_lesson), ("hub", hub_lesson)]:
            if lesson:
                f.write(json.dumps({"ts": now_iso, "lesson": lesson, "source": source, "session": session_id}) + "\n")

    # Role logs
    for role, lesson in [("strategist", strategist_lesson), ("critic", critic_lesson)]:
        if lesson:
            log_path = memory / f"{role}-log.md"
            with open(log_path, "a", encoding="utf-8") as f:
                if log_path.stat().st_size == 0:
                    f.write(f"# {role.title()} Memory Log\n")
                f.write(f"\n### Session {session_id} ({date_str})\n\n{lesson}\n")

    # --- Tier 1: Add to active memory ---
    for role, lesson in [("strategist", strategist_lesson), ("critic", critic_lesson), ("hub", hub_lesson)]:
        if lesson:
            active = load_active(project_dir, role)
            entry_id = _next_id(role, active)
            entry_topics = list(extract_topics(lesson))
            entry = {
                "id": entry_id,
                "topics": entry_topics or goal_topics,
                "detail_level": 3,
                "text": lesson,
                "headline": lesson[:100].split(".")[0] + "." if "." in lesson[:100] else lesson[:80],
                "importance": importance,
                "pinned": pin,
                "created": now_iso,
                "last_referenced": now_iso,
                "referenced_count": 0,
                "source_sessions": [session_id],
                "supersedes": [],
            }
            active.setdefault("entries", []).append(entry)
            save_active(project_dir, role, active)

    # --- Tier 0: Update index ---
    index = load_index(project_dir)
    index["consultation_count"] = index.get("consultation_count", 0) + 1
    index["last_updated"] = now_iso

    # Recent decisions (keep last 5)
    decision_entry = {
        "session_id": session_id,
        "date": date_str,
        "goal_oneliner": goal[:100],
        "decision_oneliner": decision[:100],
        "importance": importance,
        "topics": goal_topics,
    }
    recent = index.get("recent_decisions", [])
    recent.append(decision_entry)
    index["recent_decisions"] = recent[-5:]

    # Pinned
    if pin:
        pin_entry = {
            "id": f"P-{session_id}",
            "text": decision[:150],
            "importance": importance,
            "source": "hub",
        }
        index.setdefault("pinned", []).append(pin_entry)

    # Topic index
    ti = index.get("topic_index", {})
    for topic in goal_topics:
        ti.setdefault(topic, {"decision_ids": [], "memory_ids": []})
        if session_id not in ti[topic]["decision_ids"]:
            ti[topic]["decision_ids"].append(session_id)
    index["topic_index"] = ti

    save_index(project_dir, index)

    return f"Recorded consultation {session_id}. Memory updated across all tiers."


# ---------------------------------------------------------------------------
# Memory health / compaction status
# ---------------------------------------------------------------------------
def get_memory_health(project_dir: str) -> dict:
    """Get memory health stats for compaction decisions."""
    memory = _memory_dir(project_dir)
    index = load_index(project_dir)

    health = {
        "consultation_count": index.get("consultation_count", 0),
        "last_updated": index.get("last_updated", ""),
        "compaction_watermark": index.get("compaction_watermark", ""),
        "roles": {},
        "needs_compaction": False,
    }

    for role in ["strategist", "critic", "hub"]:
        active = load_active(project_dir, role)
        entries = active.get("entries", [])
        entry_count = len(entries)
        total_tokens = sum(estimate_tokens(e.get("text", "")) for e in entries)

        log_path = memory / f"{role}-log.md"
        log_lines = 0
        if log_path.exists():
            log_lines = len(log_path.read_text(encoding="utf-8").strip().split("\n"))

        needs = total_tokens > 6000 or entry_count > 20
        if needs:
            health["needs_compaction"] = True

        health["roles"][role] = {
            "active_entries": entry_count,
            "active_tokens": total_tokens,
            "log_lines": log_lines,
            "needs_compaction": needs,
        }

    return health
