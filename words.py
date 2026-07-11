"""Word lists for kids word game by difficulty mode."""

import random

# ~80 three-letter words (ages ~4–5 easy reading)
EASY_WORDS = [
    "cat", "dog", "bat", "hat", "mat", "rat", "sat", "cap", "map", "tap",
    "lap", "nap", "bag", "tag", "wag", "log", "fog", "hog", "big", "pig",
    "dig", "fig", "run", "fun", "sun", "bun", "cup", "pup", "bus", "jam",
    "can", "fan", "pan", "van", "bed", "red", "fed", "pen", "hen", "ten",
    "box", "fox", "six", "key", "toy", "boy", "cow", "bee", "ear", "ice",
    "bug", "mud", "tub", "rub", "cub", "web", "egg", "owl", "ant", "jet",
    "net", "wet", "pet", "get", "let", "set", "bet", "dot", "pot", "hot",
    "lot", "not", "got", "bit", "fit", "hit", "sit", "zip", "lip", "tip",
]

# ~80 four-letter words (normal mode)
NORMAL_WORDS = [
    "book", "ball", "bird", "fish", "frog", "duck", "lion", "bear", "goat", "lamb",
    "milk", "cake", "rice", "corn", "pear", "plum", "tree", "leaf", "seed", "rain",
    "wind", "moon", "star", "ship", "boat", "road", "park", "home", "door", "hand",
    "foot", "nose", "eyes", "face", "head", "hair", "play", "jump", "walk", "sing",
    "read", "stop", "help", "good", "blue", "pink", "kite", "doll", "sock", "toys",
    "baby", "bell", "belt", "coat", "cold", "farm", "fire", "flag", "game", "gift",
    "gold", "hill", "hope", "king", "lake", "love", "nest", "note", "open", "path",
    "pool", "ring", "sand", "snow", "soft", "swim", "tail", "town", "wall", "warm",
]

# ~50 five–six letter words (hard mode)
HARD_WORDS = [
    "apple", "flower", "banana", "rocket", "purple", "yellow", "orange",
    "garden", "animal", "button", "circle", "family", "friend", "happy",
    "kitten", "monkey", "pencil", "rabbit", "school", "turtle", "window",
    "zebra", "cheese", "dragon", "guitar", "planet", "summer", "winter",
    "butter", "castle", "candle", "cookie", "dancer", "forest", "market",
    "mother", "nature", "ocean", "panda", "pirate", "rainbow", "shadow",
    "silver", "spider", "sunset", "tiger", "basket", "bridge", "candy",
    "crown", "dream", "fairy", "magic", "pizza", "train", "water", "whale",
]

# ~45 seven–eight letter words (top mode — long-term players)
TOP_WORDS = [
    "kingdom", "morning", "evening", "holiday", "library", "kitchen", "bedroom",
    "outside", "diamond", "dolphin", "penguin", "chicken", "picture", "weather",
    "monster", "tractor", "blanket", "glitter", "village", "teacher", "cottage",
    "sunrise", "popcorn", "airport", "balloon", "captain", "freedom", "giraffe",
    "harvest", "journey", "lantern", "mermaid", "octopus", "rooster", "treasure",
    "dinosaur", "elephant", "mountain", "sandwich", "birthday", "campfire",
    "hospital", "magazine", "sandals", "panther", "quarter",
]

MODE_ORDER = ("easy", "normal", "hard", "top")

MODE_CONFIG = {
    "easy": {
        "label": "Easy",
        "word_count": 10,
        "letter_len": 3,
        "points": 10,
        "words": EASY_WORDS,
        "emoji": "🟢",
    },
    "normal": {
        "label": "Normal",
        "word_count": 10,
        "letter_len": 4,
        "points": 15,
        "words": NORMAL_WORDS,
        "emoji": "🟡",
    },
    "hard": {
        "label": "Hard",
        "word_count": 12,
        "letter_min": 5,
        "letter_max": 6,
        "points": 20,
        "words": HARD_WORDS,
        "emoji": "🔴",
    },
    "top": {
        "label": "Top",
        "word_count": 15,
        "letter_min": 7,
        "letter_max": 8,
        "points": 35,
        "words": TOP_WORDS,
        "emoji": "💎",
    },
}

WORD_EMOJI = {
    # Easy (3-letter)
    "cat": "🐱", "dog": "🐶", "bat": "🦇", "hat": "🎩", "mat": "🟩",
    "rat": "🐀", "sat": "🪑", "cap": "🧢", "map": "🗺️", "tap": "🚰",
    "lap": "🦵", "nap": "😴", "bag": "👜", "tag": "🏷️", "wag": "🐕",
    "log": "🪵", "fog": "🌫️", "hog": "🐗", "big": "🐘", "pig": "🐷",
    "dig": "⛏️", "fig": "🫐", "run": "🏃", "fun": "😄", "sun": "☀️",
    "bun": "🍞", "cup": "☕", "pup": "🐶", "bus": "🚌", "jam": "🍓",
    "can": "🥫", "fan": "🪭", "pan": "🍳", "van": "🚐", "bed": "🛏️",
    "red": "🔴", "fed": "🍽️", "pen": "🖊️", "hen": "🐔", "ten": "🔟",
    "box": "📦", "fox": "🦊", "six": "6️⃣", "key": "🔑", "toy": "🧸",
    "boy": "👦", "cow": "🐄", "bee": "🐝", "ear": "👂", "ice": "🧊",
    "bug": "🐛", "mud": "🟤", "tub": "🛁", "rub": "🧽", "cub": "🐻",
    "web": "🕸️", "egg": "🥚", "owl": "🦉", "ant": "🐜", "jet": "✈️",
    "net": "🥅", "wet": "💧", "pet": "🐾", "get": "👋", "let": "✋",
    "set": "🎯", "bet": "🎲", "dot": "⚫", "pot": "🍲", "hot": "🔥",
    "lot": "📦", "not": "🚫", "got": "✅", "bit": "🦷", "fit": "💪",
    "hit": "👊", "sit": "🪑", "zip": "🤐", "lip": "👄", "tip": "💡",
    # Normal (4-letter)
    "book": "📖", "ball": "⚽", "bird": "🐦", "fish": "🐟", "frog": "🐸",
    "duck": "🦆", "lion": "🦁", "bear": "🐻", "goat": "🐐", "lamb": "🐑",
    "milk": "🥛", "cake": "🎂", "rice": "🍚", "corn": "🌽", "pear": "🍐",
    "plum": "🟣", "tree": "🌳", "leaf": "🍃", "seed": "🌱", "rain": "🌧️",
    "wind": "💨", "moon": "🌙", "star": "⭐", "ship": "🚢", "boat": "⛵",
    "road": "🛣️", "park": "🏞️", "home": "🏠", "door": "🚪", "hand": "✋",
    "foot": "🦶", "nose": "👃", "eyes": "👀", "face": "😊", "head": "🗣️",
    "hair": "💇", "play": "🎮", "jump": "🦘", "walk": "🚶", "sing": "🎤",
    "read": "📚", "stop": "🛑", "help": "🆘", "good": "👍", "blue": "🔵",
    "pink": "🩷", "kite": "🪁", "doll": "🪆", "sock": "🧦", "toys": "🧸",
    "baby": "👶", "bell": "🔔", "belt": "👔", "coat": "🧥", "cold": "🥶",
    "farm": "🚜", "fire": "🔥", "flag": "🚩", "game": "🎮", "gift": "🎁",
    "gold": "🥇", "hill": "⛰️", "hope": "🌟", "king": "👑", "lake": "🏞️",
    "love": "❤️", "nest": "🪺", "note": "📝", "open": "📂", "path": "🛤️",
    "pool": "🏊", "ring": "💍", "sand": "🏖️", "snow": "❄️", "soft": "🧸",
    "swim": "🏊", "tail": "🐕", "town": "🏘️", "wall": "🧱", "warm": "☀️",
    # Hard
    "apple": "🍎", "flower": "🌸", "banana": "🍌", "rocket": "🚀",
    "purple": "🟣", "yellow": "💛", "orange": "🍊", "garden": "🌻",
    "animal": "🐾", "button": "🔘", "circle": "⭕", "family": "👨‍👩‍👧‍👦",
    "friend": "🤝", "happy": "😊", "kitten": "😺", "monkey": "🐵",
    "pencil": "✏️", "rabbit": "🐰", "school": "🏫", "turtle": "🐢",
    "window": "🪟", "zebra": "🦓", "cheese": "🧀", "dragon": "🐉",
    "guitar": "🎸", "planet": "🪐", "summer": "☀️", "winter": "⛄",
    "butter": "🧈", "castle": "🏰", "candle": "🕯️", "cookie": "🍪",
    "dancer": "💃", "forest": "🌲", "market": "🏪", "mother": "👩",
    "nature": "🌿", "ocean": "🌊", "panda": "🐼", "pirate": "🏴‍☠️",
    "rainbow": "🌈", "shadow": "🌑", "silver": "🥈", "spider": "🕷️",
    "sunset": "🌅", "tiger": "🐯", "basket": "🧺", "bridge": "🌉",
    "candy": "🍬", "crown": "👑", "dream": "💭", "fairy": "🧚",
    "magic": "✨", "pizza": "🍕", "train": "🚂", "water": "💧", "whale": "🐋",
    # Top (7–8 letter)
    "kingdom": "🏰", "morning": "🌅", "evening": "🌆", "holiday": "🎉",
    "library": "📚", "kitchen": "🍳", "bedroom": "🛏️", "outside": "🌳",
    "diamond": "💎", "dolphin": "🐬", "penguin": "🐧", "chicken": "🐔",
    "picture": "🖼️", "weather": "⛅", "monster": "👾", "tractor": "🚜",
    "blanket": "🛏️", "glitter": "✨", "village": "🏘️", "teacher": "👩‍🏫",
    "cottage": "🏡", "sunrise": "🌄", "popcorn": "🍿", "airport": "✈️",
    "balloon": "🎈", "captain": "🧑‍✈️", "freedom": "🕊️", "giraffe": "🦒",
    "harvest": "🌾", "journey": "🗺️", "lantern": "🏮", "mermaid": "🧜‍♀️",
    "octopus": "🐙", "rooster": "🐓", "treasure": "💰", "dinosaur": "🦕",
    "elephant": "🐘", "mountain": "⛰️", "sandwich": "🥪", "birthday": "🎂",
    "campfire": "🔥", "hospital": "🏥", "magazine": "📰", "sandals": "🩴",
    "panther": "🐆", "quarter": "🪙",
}


def _pool_for_mode(mode: str) -> list[str]:
    """Words allowed for this mode (strict letter length)."""
    cfg = MODE_CONFIG[mode]
    raw = [w.lower().strip() for w in cfg["words"] if w and str(w).strip()]
    if "letter_min" in cfg:
        lo = cfg["letter_min"]
        hi = cfg["letter_max"]
        return [w for w in raw if lo <= len(w) <= hi]
    n = cfg.get("letter_len", 3)
    return [w for w in raw if len(w) == n]


def mode_letter_label(mode: str) -> str:
    """Human-readable letter-length label for UI."""
    cfg = MODE_CONFIG[mode]
    if "letter_min" in cfg:
        if cfg["letter_min"] == cfg["letter_max"]:
            return str(cfg["letter_min"])
        return f"{cfg['letter_min']}–{cfg['letter_max']}"
    return str(cfg.get("letter_len", 3))


def get_round_words(mode: str) -> list[str]:
    """Return a small random set for one game (not the full word bank)."""
    if mode not in MODE_CONFIG:
        raise ValueError(f"Unknown mode: {mode}")
    pool = _pool_for_mode(mode)
    if not pool:
        raise ValueError(f"No valid words for mode: {mode}")
    count = min(MODE_CONFIG[mode]["word_count"], len(pool))
    return random.sample(pool, count)


def word_hint(word: str) -> str:
    return WORD_EMOJI.get(word.lower(), "✨")