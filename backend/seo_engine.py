"""
JETBOX v3 â€” SEO Metadata Engine
Title format: [FREE] Artist1 x Artist2 Type Beat - "Beat Name"
Manual artist selection from 100-artist database.

YouTube upload constraints (Data API): tags total â‰¤ 500 characters; category Music = 10;
metadata should be accurate (no misleading titles/tags) â€” aligns with platform rules.

Project root may include YT_ALGO_EN_2026_.pdf for policy notes; keep templates honest and
keyword-relevant (no clickbait unrelated to audio).
"""

from datetime import datetime
from typing import Any, Optional

# â”€â”€â”€ 100 GLOBAL TRAP ARTISTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TRAP_ARTISTS = {
    "legends": [
        "Travis Scott", "Playboi Carti", "Future", "Young Thug", "Lil Baby",
        "Gunna", "21 Savage", "Metro Boomin", "Lil Uzi Vert", "Migos",
        "Pop Smoke", "Juice WRLD", "XXXTentacion", "Lil Durk", "NBA YoungBoy",
        "Kodak Black", "DaBaby", "Roddy Ricch", "Polo G", "Lil Tjay",
    ],
    "major": [
        "Don Toliver", "Yeat", "Ken Carson", "Destroy Lonely", "Homixide Gang",
        "Sofaygo", "Lancey Foux", "Baby Keem", "JID", "Denzel Curry",
        "Trippie Redd", "Ski Mask The Slump God", "Smokepurpp", "Comethazine", "Lil Tecca",
        "Lil Mosey", "Iann Dior", "24kGoldn", "The Kid LAROI", "Lil Keed",
    ],
    "rising": [
        "Yung Lean", "Bladee", "Chief Keef", "Gucci Mane", "2 Chainz",
        "Young Dolph", "Key Glock", "Moneybagg Yo", "EST Gee", "42 Dugg",
        "Lil Yachty", "Offset", "Quavo", "Takeoff", "Young Nudy",
        "Pi'erre Bourne", "Southside", "TM88", "Wheezy", "ATL Jacob",
    ],
    "producers": [
        "Mike Dean", "Murda Beatz", "Tay Keith", "London On Da Track", "Turbo",
        "Cubeatz", "808 Mafia", "Zaytoven", "Lex Luger", "Honorable C.N.O.T.E.",
    ],
    "new_wave": [
        "Fivio Foreign", "Sheff G", "Sleepy Hallow", "Lil Gotit", "Lil Loaded",
        "NLE Choppa", "Blueface", "Shoreline Mafia", "Drakeo The Ruler", "03 Greedo",
        "Rich The Kid", "Famous Dex", "YBN Nahmir", "Tee Grizzley", "Sada Baby",
        "BabyTron", "Rio Da Yung OG", "Veeze", "Babyface Ray", "Icewear Vezzo",
    ],
    "melodic_trap": [
        "Lil Peep", "Lil Tracy", "Night Lovell", "Bones", "Xavier Wulf",
        "Chris King", "Cochise", "$NOT", "Jasiah", "ZillaKami",
    ],
    "uk_international": [
        "Central Cee", "Dave", "Headie One", "Skepta", "AJ Tracey",
        "Stormzy", "Digga D", "M1llionz", "Tion Wayne", "Russ Millions",
    ],
    "classic": [
        "T.I.", "Jeezy", "Rick Ross", "Waka Flocka Flame", "OJ Da Juiceman",
    ],
    "niche_targets": [
        "Lancey Foux", "Rich Amiri", "Glokk40Spaz", "Destroy Lonely", "Ken Carson",
        "Homixide Gang", "Sofaygo", "Yeat", "BabyTron", "Cochise", "Nine Vicious",
    ],
    "tr_rap": [
        "Ufo361", "Capo", "Summer Cem", "Mero", "Eno", "Lil Lano",
        "Bonez MC", "RAF Camora", "Capital Bra", "Luciano", "Bausa",
    ],
}


# â”€â”€â”€ MOOD HOOKS (first lines â€” strong CTR + keyword relevance) â”€â”€â”€â”€â”€â”€â”€â”€â”€

MOOD_HOOKS = {
    "rage": (
        "Dark, aggressive energy â€” built for heavy rap flows, punchy delivery, and high-energy content."
    ),
    "melodic": (
        "Melodic and emotional â€” airy textures with room for hooks, melodies, and storytelling."
    ),
    "trap": (
        "Hard-hitting trap drums and 808s â€” studio-ready for artists, freestyles, and YouTube content."
    ),
}


DEFAULT_CHANNEL_CONFIG: dict[str, Any] = {
    "channel_name": "ENNY TANG",
    "channel_handle": "@enny-tang",
    "contact_email": "",
    "social_links": [],
    "default_license": (
        "FREE FOR NON-PROFIT USE - credit the producer ENNY TANG in the video title or description. "
        "Commercial use, monetized streams, and exclusive rights require a lease."
    ),
    "lease_url": "",
    "producer_credit": "ENNY TANG",
    "youtube_category": "10",
    "youtube_region": "US",
    "default_language": "en",
}


def merge_channel_config(channel_config: Optional[dict]) -> dict:
    """Merge user config.json (or API body) over defaults."""
    cfg = dict(DEFAULT_CHANNEL_CONFIG)
    if channel_config:
        for k, v in channel_config.items():
            if v is None:
                continue
            if k == "social_links" and isinstance(v, list):
                cfg[k] = [str(x).strip() for x in v if str(x).strip()]
            else:
                cfg[k] = v
    return cfg


def get_all_artists() -> list:
    """Return flat list of all unique artists."""
    seen = set()
    all_artists = []
    for tier_artists in TRAP_ARTISTS.values():
        for artist in tier_artists:
            if artist not in seen:
                seen.add(artist)
                all_artists.append(artist)
    return all_artists


def get_artists_by_tier() -> dict:
    """Return artists organized by tier for dashboard display."""
    return TRAP_ARTISTS


def search_artists(query: str) -> list:
    """Search artists by partial name match."""
    query_lower = query.lower()
    results = []
    for artist in get_all_artists():
        if query_lower in artist.lower():
            results.append(artist)
    return results


# â”€â”€â”€ TITLE & SEO GENERATION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def generate_title(artist1: str, artist2: Optional[str], beat_name: str) -> str:
    """
    Generate YouTube title in standard format.
    Format: [FREE] Artist1 x Artist2 Type Beat - "Beat Name" (with artist2)
    Format: [FREE] Artist1 Type Beat - "Beat Name" (without artist2)
    """
    if artist2 and artist2.strip():
        return f'[FREE] {artist1} x {artist2} Type Beat - "{beat_name}"'
    return f'[FREE] {artist1} Type Beat - "{beat_name}"'


def _mood_line(vibe: str) -> str:
    v = (vibe or "trap").lower()
    if "rage" in v:
        return MOOD_HOOKS["rage"]
    if "melodic" in v:
        return MOOD_HOOKS["melodic"]
    return MOOD_HOOKS["trap"]


def generate_full_description_v2(
    artist1: str,
    artist2: Optional[str],
    beat_name: str,
    bpm: int,
    key: str,
    drop_timestamp: str,
    vibe: str,
    channel_config: Optional[dict],
    outro_timestamp: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> str:
    """
    Minimalist, human-like US-market description: beat line, specs, license, contact, hashtags.
    Supports both single-artist and dual-artist format.
    """
    cfg = merge_channel_config(channel_config)
    year = datetime.now().year
    ch = cfg.get("channel_name", "ENNY TANG")
    producer = cfg.get("producer_credit", ch)
    license_text = cfg.get("default_license", "Free for non-commercial use. You MUST credit (Prod. by ENNY TANG) in the title or description.")
    lease = (cfg.get("lease_url") or "").strip()
    email = "ennytangdecc@gmail.com"
    socials = cfg.get("social_links") or []

    has_artist2 = bool(artist2 and str(artist2).strip())
    a2 = str(artist2).strip() if has_artist2 else ""

    if has_artist2:
        beat_line = f'"{beat_name}" - {artist1} x {a2} Type Beat'
    else:
        beat_line = f'"{beat_name}" - {artist1} Type Beat'

    social_block = "\n".join(f"{u}" for u in socials if u) if socials else ""
    email_block = f"{email}" if email else ""
    lease_block = f"Lease: {lease}" if lease else ""

    v = (vibe or "trap").lower()

    if has_artist2:
        style_desc = f"This instrumental is inspired by the sounds of {artist1} and {a2}."
    else:
        style_desc = f"This instrumental is inspired by the sounds of {artist1}."

    specs_desc = f"BPM: {bpm} | Key: {key}"

    if has_artist2:
        tag_block = (
            f"{artist1.lower()} type beat, {a2.lower()} type beat, {v} type beat {year}, "
            f"free type beat, free {v} instrumental, type beat {year}, rap instrumental, "
            f"dark trap beat, hard trap beat, free beat for vocals"
        )
        hashtags = (
            f"#{artist1.replace(' ', '')} #{a2.replace(' ', '')} "
            f"#typebeat #instrumental"
        )
    else:
        tag_block = (
            f"{artist1.lower()} type beat, {v} type beat {year}, "
            f"free type beat, free {v} instrumental, type beat {year}, rap instrumental, "
            f"dark trap beat, hard trap beat, free beat for vocals"
        )
        hashtags = f"#{artist1.replace(' ', '')} #typebeat #instrumental"

    drop_clean = str(drop_timestamp or "0:25").strip()

    if outro_timestamp and str(outro_timestamp).strip():
        outro_clean = str(outro_timestamp).strip()
    elif duration_seconds and duration_seconds > 0:
        total_m = int(duration_seconds) // 60
        total_s = int(duration_seconds) % 60
        outro_clean = f"{total_m}:{total_s:02d}"
    else:
        outro_clean = "2:30"

    parts = [
        beat_line,
        f"Prod. by {producer}",
        "",
        f"0:00 Intro",
        f"{drop_clean} Drop",
        f"{outro_clean} Outro",
        "",
        style_desc,
        specs_desc,
        "",
        "[ Usage ]",
        license_text,
    ]

    if lease_block:
        parts.append(lease_block)

    contact_parts = []
    if email_block:
        contact_parts.append(email_block)
    if social_block:
        contact_parts.append(social_block)

    if contact_parts:
        parts.append("")
        parts.append("[ Contact ]")
        parts.extend(contact_parts)

    parts.extend([
        "",
        tag_block,
        hashtags,
    ])
    return "\n".join(parts)


def build_tags_candidate_list(
    artist1: str,
    artist2: Optional[str],
    beat_name: str,
    bpm: int,
    vibe: str,
    year: int,
) -> list:
    """Ordered candidates; normalized later to API limits. artist2 may be None."""
    v = (vibe or "trap").lower()
    has_artist2 = bool(artist2 and str(artist2).strip())
    a2 = str(artist2).strip() if has_artist2 else ""

    tags = [f"{artist1} type beat"]
    if has_artist2:
        tags += [
            f"{a2} type beat",
            f"{artist1} x {a2} type beat",
            f"free {artist1} type beat",
            f"free {a2} type beat",
            f"{artist1} type beat {year}",
            f"{a2} type beat {year}",
        ]
    else:
        tags += [
            f"free {artist1} type beat",
            f"{artist1} type beat {year}",
        ]

    tags += [
        beat_name[:30],
        f"{v} type beat",
        f"{v} instrumental",
        "free type beat",
        f"free type beat {year}",
        "trap beat",
        "trap instrumental",
        "rap instrumental",
        "type beat",
        "instrumental",
        "free beat",
        f"{bpm} bpm",
        f"{bpm} bpm type beat",
        "beats",
        "producer",
        "melodic trap" if "melodic" in v else "dark trap",
        "hip hop instrumental",
        "youtube type beat",
    ]

    # de-dupe preserving order
    seen = set()
    out = []
    for t in tags:
        t = str(t).strip()
        if not t:
            continue
        low = t.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(t)
    return out


def normalize_tags_for_youtube(tags: list, max_total_chars: int = 500, max_tag_len: int = 30) -> list:
    """
    YouTube: sum of tag string lengths must stay within ~500 characters total (API constraint).
    Individual tags are commonly kept â‰¤ 30 chars.
    """
    out: list[str] = []
    total = 0
    seen: set[str] = set()
    for raw in tags:
        t = str(raw).strip()
        if not t:
            continue
        if len(t) > max_tag_len:
            # Truncate at word boundary to avoid cutting mid-word (e.g. "typ" instead of "type beat")
            truncated = t[:max_tag_len]
            last_space = truncated.rfind(' ')
            t = truncated[:last_space].rstrip() if last_space > 10 else truncated.rstrip()
        low = t.lower()
        if low in seen:
            continue
        sep = 1 if out else 0
        if total + sep + len(t) <= max_total_chars:
            out.append(t)
            seen.add(low)
            total += sep + len(t)
    return out


def generate_tags(
    artist1: str,
    artist2: Optional[str],
    beat_name: str,
    bpm: int,
    vibe: str = "trap"
) -> list:
    year = datetime.now().year
    return normalize_tags_for_youtube(
        build_tags_candidate_list(artist1, artist2, beat_name, bpm, vibe, year),
        500,
    )


def generate_description(
    artist1: str,
    artist2: Optional[str],
    beat_name: str,
    bpm: int,
    key: str,
    drop_timestamp: str,
    vibe: str = "trap",
    outro_timestamp: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> str:
    """Backward-compatible wrapper."""
    return generate_full_description_v2(
        artist1, artist2, beat_name, bpm, key, drop_timestamp, vibe, None,
        outro_timestamp=outro_timestamp,
        duration_seconds=duration_seconds,
    )


def calculate_seo_score(title: str, description: str, tags: list) -> dict:
    """Calculate SEO optimization score with breakdown."""
    title_len = len(title)
    if 50 <= title_len <= 100:
        title_score = 1.0
    elif title_len < 50:
        title_score = title_len / 50
    else:
        title_score = max(0.5, 1.0 - (title_len - 100) / 100)

    desc_len = len(description)
    desc_score = min(desc_len / 1200, 1.0) * 0.55
    has_license = "LICENSE" in description.upper() or "NON-PROFIT" in description.upper()
    has_drop = "drop" in description.lower()
    has_bpm = "bpm" in description.lower()
    has_key = "key" in description.lower()
    has_cta = "subscribe" in description.lower()
    desc_score += 0.09 * sum([has_license, has_drop, has_bpm, has_key, has_cta])
    desc_score = min(desc_score, 1.0)

    tag_count = len(tags)
    tag_chars = sum(len(t) for t in tags)
    tag_score = min(tag_count / 18, 1.0) * 0.45 + min(tag_chars / 450, 1.0) * 0.55

    overall = round(title_score * 0.3 + desc_score * 0.35 + tag_score * 0.35, 2)

    return {
        "overall": overall,
        "title_score": round(title_score, 2),
        "description_score": round(desc_score, 2),
        "tag_score": round(tag_score, 2),
        "tag_count": tag_count,
        "tag_chars": tag_chars,
        "title_length": title_len,
    }


def generate_publish_package(
    artist1: str,
    artist2: Optional[str],
    beat_name: str,
    bpm: int,
    key: str,
    drop_timestamp: str,
    vibe: str = "trap",
    channel_config: Optional[dict] = None,
    outro_timestamp: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> dict:
    """
    Full publish payload for YouTube: title, description, tags (â‰¤500 chars total),
    category, language, region, channel display fields.
    """
    cfg = merge_channel_config(channel_config)
    year = datetime.now().year
    title = generate_title(artist1, artist2, beat_name)
    description = generate_full_description_v2(
        artist1, artist2, beat_name, bpm, key, drop_timestamp, vibe, cfg,
        outro_timestamp=outro_timestamp,
        duration_seconds=duration_seconds,
    )
    tags = normalize_tags_for_youtube(
        build_tags_candidate_list(artist1, artist2, beat_name, bpm, vibe, year),
        500,
    )
    seo_score = calculate_seo_score(title, description, tags)
    tag_chars = sum(len(t) for t in tags)

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "tags_char_total": tag_chars,
        "tags_joined_length": len(",".join(tags)),
        "category": cfg.get("youtube_category", "10"),
        "category_name": "Music",
        "defaultLanguage": cfg.get("default_language", "en"),
        "region_code": cfg.get("youtube_region", "US"),
        "channel_name": cfg.get("channel_name"),
        "channel_handle": cfg.get("channel_handle"),
        "seo_score": seo_score,
        "metadata": {
            "artist1": artist1,
            "artist2": artist2,
            "beat_name": beat_name,
            "bpm": bpm,
            "key": key,
            "drop_timestamp": drop_timestamp,
            "vibe": vibe,
            "category_id": cfg.get("youtube_category", "10"),
            "region_code": cfg.get("youtube_region", "US"),
            "default_language": cfg.get("default_language", "en"),
            "privacy_status": "public",
        },
    }


def generate_full_seo(
    artist1: str,
    artist2: Optional[str],
    beat_name: str,
    bpm: int,
    key: str,
    drop_timestamp: str,
    vibe: str = "trap"
) -> dict:
    """Generate complete SEO package (defaults only â€” no config.json merge)."""
    return generate_publish_package(
        artist1, artist2, beat_name, bpm, key, drop_timestamp, vibe, channel_config=None
    )


