import os
import re

# In-memory caches populated at startup by _preload_logos
_logo_cache = {}
_logo_lookup = {}


def _generate_logo_candidates(team_name: str):
    """Return a list of candidate filename stems for a team name.

    Examples:
      "Milwaukee Bucks" -> ["milwaukee bucks", "bucks", "milwaukee", "milwaukeebucks"]
      "Trail Blazers" -> ["trail blazers", "blazers", "trail", "trailblazers"]
    """
    if not team_name:
        return []

    name = team_name.lower().strip()
    # Remove punctuation except spaces and digits/letters
    normalized = re.sub(r"[^a-z0-9 ]+", "", name)

    parts = [p for p in re.split(r"\s+", normalized) if p]
    candidates = []

    # full normalized name
    if normalized:
        candidates.append(normalized)

    # last word (e.g., 'bucks')
    if parts:
        candidates.append(parts[-1])

    # last two words (e.g., 'trail blazers')
    if len(parts) >= 2:
        candidates.append(" ".join(parts[-2:]))

    # first word (sometimes logos use city or nickname alone)
    if parts:
        candidates.append(parts[0])

    # concatenated variants
    candidates.append("".join(parts))
    candidates.append("_".join(parts))
    candidates.append("-".join(parts))

    # Deduplicate while preserving order
    seen = set()
    dedup = []
    for c in candidates:
        if c and c not in seen:
            dedup.append(c)
            seen.add(c)
    return dedup


def _find_logo_file(team_name: str):
    """Return an existing logo file path for team_name or None.

    Looks in the local `nba-logos/` folder and tries several filename patterns.
    """
    # Check in-memory lookup first (populated by _preload_logos)
    candidates = _generate_logo_candidates(team_name)
    for stem in candidates:
        if stem in _logo_lookup:
            return _logo_lookup[stem]

    # Fallback: attempt to find a matching image file on disk using candidates
    logos_dir = os.path.join(os.path.dirname(__file__), "nba-logos")
    if not os.path.isdir(logos_dir):
        logos_dir = "nba-logos"

    for stem in candidates:
        for variant in (f"{stem}.png", f"{stem}.PNG", f"{stem}.jpg", f"{stem}.jpeg"):
            path = os.path.join(logos_dir, variant)
            if os.path.exists(path):
                return os.path.abspath(path)

    raw_path = os.path.join(logos_dir, f"{team_name}.png")
    if os.path.exists(raw_path):
        return os.path.abspath(raw_path)

    return None


def _preload_logos(sizes=(40, 60)):
    """Scan `nba-logos/`, populate `_logo_lookup` (stem -> abs path) and
    preload scaled QPixmaps into `_logo_cache` for the provided sizes.
    """
    logos_dir = os.path.join(os.path.dirname(__file__), "nba-logos")
    if not os.path.isdir(logos_dir):
        logos_dir = "nba-logos"

    try:
        files = os.listdir(logos_dir)
    except Exception:
        return

    # Build lookup mapping from file stems to absolute path
    for fname in files:
        lower = fname.lower()
        if not (lower.endswith('.png') or lower.endswith('.jpg') or lower.endswith('.jpeg')):
            continue

        stem = os.path.splitext(fname)[0]
        path = os.path.join(logos_dir, fname)
        abs_path = os.path.abspath(path)

        candidates = _generate_logo_candidates(stem)
        for c in candidates:
            if c not in _logo_lookup:
                _logo_lookup[c] = abs_path

    # Try to preload pixmaps for requested sizes if PyQt is available
    try:
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtCore import Qt
        qt_available = True
    except Exception:
        qt_available = False

    if not qt_available:
        return

    for abs_path in set(_logo_lookup.values()):
        for size in sizes:
            cache_key = f"{abs_path}::{size}"
            if cache_key in _logo_cache:
                continue
            try:
                pix = QPixmap(abs_path)
                if not pix.isNull():
                    scaled = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    _logo_cache[cache_key] = scaled
            except Exception:
                continue


def _load_logo_pixmap(team_name: str, size: int):
    """Load and return a scaled QPixmap for team_name, or None if not found.

    Uses an internal cache keyed by absolute path + size to avoid repeated loads.
    """
    try:
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtCore import Qt
    except Exception:
        return None

    logo_file = _find_logo_file(team_name)
    if not logo_file:
        return None

    abs_path = os.path.abspath(logo_file)
    cache_key = f"{abs_path}::{size}"
    if cache_key in _logo_cache:
        return _logo_cache[cache_key]

    try:
        pixmap = QPixmap(abs_path)
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            _logo_cache[cache_key] = scaled
            return scaled
    except Exception:
        return None

    return None