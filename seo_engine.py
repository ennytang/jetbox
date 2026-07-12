"""
JETBOX v3 â€” SEO Metadata Engine
Title format: [FREE] Artist1 x Artist2 Type Beat - "Beat Name"
Manual artist selection from 100-artist database
"""

from datetime import datetime

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
    ]
}


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

def generate_title(artist1: str, artist2: str, beat_name: str) -> str:
    """
    Generate YouTube title in standard format.
    Format: [FREE] Artist1 x Artist2 Type Beat - "Beat Name"
    """
    return f'[FREE] {artist1} x {artist2} Type Beat - "{beat_name}"'


def generate_description(
    artist1: str,
    artist2: str,
    beat_name: str,
    bpm: int,
    key: str,
    drop_timestamp: str,
    vibe: str = "trap"
) -> str:
    """Generate YouTube description with SEO optimization."""
    
    year = datetime.now().year
    
    description = f"""ğŸ”¥ {artist1} x {artist2} Type Beat - "{beat_name}"

Produced by ENNYTANG

ğŸ”¥ DROP: {drop_timestamp}

ğŸ¹ Key: {key}
ğŸ’¿ BPM: {bpm}
ğŸ¨ Vibe: {vibe.capitalize()}
ğŸ“… {year}

âœ… FREE FOR NON-PROFIT USE
ğŸ“§ DM for exclusive rights / lease

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

ğŸ”” Subscribe for daily type beats
ğŸ‘ Like & Comment for more {artist1} type beats

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

#{artist1.replace(' ', '')}TypeBeat #{artist2.replace(' ', '')}TypeBeat #FreeBeats #TypeBeat{year} #{vibe.capitalize()}Beat #RapBeats #TrapBeats #FreeInstrumental #ProducerLife #ENNYTANG"""

    return description


def generate_tags(
    artist1: str,
    artist2: str,
    beat_name: str,
    bpm: int,
    vibe: str = "trap"
) -> list:
    """Generate YouTube tags for maximum SEO coverage."""
    
    year = datetime.now().year
    
    tags = [
        # Primary artist tags
        f"{artist1} Type Beat",
        f"{artist1} Type Beat {year}",
        f"Free {artist1} Type Beat",
        f"Free {artist1} Type Beat {year}",
        
        # Secondary artist tags
        f"{artist2} Type Beat",
        f"{artist2} Type Beat {year}",
        f"Free {artist2} Type Beat",
        
        # Combined
        f"{artist1} x {artist2} Type Beat",
        f"Free {artist1} x {artist2} Type Beat",
        
        # Beat name
        beat_name,
        
        # Vibe tags
        f"{vibe} type beat",
        f"{vibe} type beat {year}",
        f"{vibe} beat",
        f"{vibe} instrumental",
        
        # Generic high-volume
        "Free Type Beat",
        f"Free Type Beat {year}",
        "Rap Beat",
        "Trap Beat",
        "Free Beats",
        "Free Instrumental",
        "Rap Instrumental",
        f"{bpm} BPM Beat",
        "Type Beat",
        "Producer",
        "Beat Making",
    ]
    
    # YouTube tag limit: 500 characters total
    # Filter to stay under limit
    total_chars = 0
    filtered = []
    for tag in tags:
        if total_chars + len(tag) + 1 <= 495:  # +1 for comma separator
            filtered.append(tag)
            total_chars += len(tag) + 1
    
    return filtered


def calculate_seo_score(title: str, description: str, tags: list) -> dict:
    """Calculate SEO optimization score with breakdown."""
    
    # Title score (0-1): length 50-100 chars optimal
    title_len = len(title)
    if 50 <= title_len <= 100:
        title_score = 1.0
    elif title_len < 50:
        title_score = title_len / 50
    else:
        title_score = max(0.5, 1.0 - (title_len - 100) / 100)
    
    # Description score: length, keywords, structure
    desc_len = len(description)
    desc_score = min(desc_len / 800, 1.0) * 0.6
    has_drop = "DROP:" in description
    has_bpm = "BPM:" in description
    has_key = "Key:" in description
    has_cta = "Subscribe" in description or "Like" in description
    desc_score += 0.1 * sum([has_drop, has_bpm, has_key, has_cta])
    desc_score = min(desc_score, 1.0)
    
    # Tag score: count and total character coverage
    tag_count = len(tags)
    tag_chars = sum(len(t) for t in tags)
    tag_score = min(tag_count / 20, 1.0) * 0.5 + min(tag_chars / 400, 1.0) * 0.5
    
    overall = round(title_score * 0.3 + desc_score * 0.35 + tag_score * 0.35, 2)
    
    return {
        "overall": overall,
        "title_score": round(title_score, 2),
        "description_score": round(desc_score, 2),
        "tag_score": round(tag_score, 2),
        "tag_count": tag_count,
        "tag_chars": tag_chars,
        "title_length": title_len
    }


def generate_full_seo(
    artist1: str,
    artist2: str,
    beat_name: str,
    bpm: int,
    key: str,
    drop_timestamp: str,
    vibe: str = "trap"
) -> dict:
    """Generate complete SEO package ready for YouTube upload."""
    
    title = generate_title(artist1, artist2, beat_name)
    description = generate_description(artist1, artist2, beat_name, bpm, key, drop_timestamp, vibe)
    tags = generate_tags(artist1, artist2, beat_name, bpm, vibe)
    seo_score = calculate_seo_score(title, description, tags)
    
    return {
        "title": title,
        "description": description,
        "tags": tags,
        "seo_score": seo_score,
        "metadata": {
            "artist1": artist1,
            "artist2": artist2,
            "beat_name": beat_name,
            "bpm": bpm,
            "key": key,
            "drop_timestamp": drop_timestamp,
            "vibe": vibe,
            "category_id": "10",  # Music
            "region_code": "US",
            "privacy_status": "public",
            "default_language": "en",
        }
    }

