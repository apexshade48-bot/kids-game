"""Word lists for kids word game by difficulty mode."""

import random

# Letters — ABC names + a picture word (learners who already know the alphabet)
LETTER_BANK = (
    ("a", "apple", "🍎"),
    ("b", "ball", "⚽"),
    ("c", "cat", "🐱"),
    ("d", "dog", "🐶"),
    ("e", "egg", "🥚"),
    ("f", "fish", "🐟"),
    ("g", "gift", "🎁"),
    ("h", "hat", "🎩"),
    ("i", "ice", "🧊"),
    ("j", "jam", "🍓"),
    ("k", "key", "🔑"),
    ("l", "leaf", "🍃"),
    ("m", "moon", "🌙"),
    ("n", "nest", "🪺"),
    ("o", "orange", "🍊"),
    ("p", "pig", "🐷"),
    ("q", "queen", "👑"),
    ("r", "rain", "🌧️"),
    ("s", "sun", "☀️"),
    ("t", "tree", "🌳"),
    ("u", "up", "⬆️"),
    ("v", "van", "🚐"),
    ("w", "web", "🕸️"),
    ("x", "xray", "🩻"),
    ("y", "yam", "🍠"),
    ("z", "zebra", "🦓"),
)
LETTERS = [row[0] for row in LETTER_BANK]
LETTER_EXAMPLE = {row[0]: row[1] for row in LETTER_BANK}
LETTER_EMOJI = {row[0]: row[2] for row in LETTER_BANK}

# Sounds — CVC blending / word families (hear the sounds, say the word)
SOUND_WORDS = [
    "cat", "hat", "bat", "sat", "mat", "rat",
    "can", "pan", "man", "fan",
    "dog", "log", "hog",
    "sun", "bun", "run",
    "pig", "big", "dig",
    "bed", "red",
    "box", "fox",
    "hen", "pen", "ten",
    "cup", "pup",
    "hop", "top", "mop",
    "bug", "rug", "mug",
    "cap", "map", "nap",
    "sit", "hit", "bit",
    "pot", "hot", "dot",
]

# Beginner — sight words + short words (know ABC, building English + speaking)
BEGINNER_WORDS = [
    "i", "me", "we", "you", "am", "is", "my",
    "the", "yes", "no", "up", "in", "on", "go",
    "see", "eat", "run", "mom", "dad", "cat", "dog",
    "sun", "hat", "cup", "bed", "red", "big", "pig",
    "bus", "toy", "car", "eye", "ear", "arm",
]

# Concrete, picturable 3-letter words (ages ~4–5)
EASY_WORDS = [
    "cat", "dog", "bat", "hat", "rat", "cap", "map", "bag",
    "pig", "sun", "bun", "cup", "pup", "bus", "jam", "pan",
    "van", "bed", "pen", "hen", "box", "fox", "key", "toy",
    "boy", "cow", "bee", "ear", "ice", "bug", "mud", "tub",
    "cub", "web", "egg", "owl", "ant", "jet", "net", "pet",
    "pot", "hot", "zip", "lip", "pie", "ham", "nut", "pea",
    "tea", "mug", "jar", "lid", "rug", "sky", "sea", "yam",
    "gum", "hop", "top", "mop", "mom", "dad", "kid", "arm",
    "leg", "toe", "eye", "car", "fan", "can", "red", "ten",
    "six", "cow",
]

# Four-letter words (normal mode) — all length 4
NORMAL_WORDS = [
    "book", "ball", "bird", "fish", "frog", "duck", "lion", "bear",
    "goat", "lamb", "milk", "cake", "rice", "corn", "pear", "plum",
    "tree", "leaf", "seed", "rain", "wind", "moon", "star", "ship",
    "boat", "road", "park", "home", "door", "hand", "foot", "nose",
    "eyes", "face", "head", "hair", "play", "jump", "walk", "sing",
    "read", "stop", "help", "good", "blue", "pink", "kite", "doll",
    "sock", "toys", "baby", "bell", "belt", "coat", "cold", "farm",
    "fire", "flag", "game", "gift", "gold", "hill", "king", "lake",
    "love", "nest", "note", "open", "path", "pool", "ring", "sand",
    "snow", "swim", "tail", "town", "wall", "warm", "lamp", "fork",
    "soup", "meat", "bean", "chip", "soda", "wolf", "deer", "crab",
    "seal", "pony", "crow", "dove", "beak", "wing", "claw", "desk",
    "glue", "clip", "tape", "song", "band", "drum", "horn", "soap",
]

# Five–six letter words only (hard mode)
HARD_WORDS = [
    "apple", "flower", "banana", "rocket", "purple", "yellow", "orange",
    "garden", "animal", "button", "circle", "family", "friend", "happy",
    "kitten", "monkey", "pencil", "rabbit", "school", "turtle", "window",
    "zebra", "cheese", "dragon", "guitar", "planet", "summer", "winter",
    "butter", "castle", "candle", "cookie", "dancer", "forest", "market",
    "mother", "nature", "ocean", "panda", "pirate", "shadow", "silver",
    "spider", "sunset", "tiger", "basket", "bridge", "candy", "crown",
    "dream", "fairy", "magic", "pizza", "train", "water", "whale",
    "doctor", "farmer", "singer", "soccer", "tennis", "jungle", "island",
    "valley", "stream", "cloudy", "sunny", "pepper", "carrot", "potato",
    "tomato", "grapes", "muffin", "waffle", "saddle", "helmet",
]

# Seven–eight letter words (top mode)
TOP_WORDS = [
    "kingdom", "morning", "evening", "holiday", "library", "kitchen", "bedroom",
    "outside", "diamond", "dolphin", "penguin", "chicken", "picture", "weather",
    "monster", "tractor", "blanket", "glitter", "village", "teacher", "cottage",
    "sunrise", "popcorn", "airport", "balloon", "captain", "freedom", "giraffe",
    "harvest", "journey", "lantern", "mermaid", "octopus", "rooster", "treasure",
    "dinosaur", "elephant", "mountain", "sandwich", "birthday", "campfire",
    "hospital", "magazine", "sandals", "panther", "quarter",
    "backpack", "baseball", "football", "notebook", "homework", "painting",
    "sunshine", "raincoat", "firefly", "seashell", "starfish", "volcano",
    "carnival", "festival", "princess", "wizardry", "cupcake",
]

# Family spoken English — grown-ups (and kids who unlock it)
IMPOSSIBLE_PHRASES = [
    "i love you",
    "good night",
    "sweet dreams",
    "i am hungry",
    "please help me",
    "thank you mom",
    "thank you dad",
    "can we play",
    "i am ready",
    "let us go home",
    "wash your hands",
    "brush your teeth",
    "hello how are you",
    "good morning",
    "good afternoon",
    "good evening",
    "nice to meet you",
    "how was your day",
    "what is your name",
    "my name is",
    "where are you from",
    "how old are you",
    "can you help me",
    "please speak slowly",
    "i do not understand",
    "could you repeat that",
    "thank you very much",
    "you are welcome",
    "excuse me please",
    "i am sorry",
    "no problem",
    "see you later",
    "have a nice day",
    "what time is it",
    "i need some water",
    "where is the bathroom",
    "how much does it cost",
    "i would like coffee",
    "can i have the bill",
    "do you speak english",
    "i am learning english",
    "please say that again",
    "what does this mean",
    "the weather is nice",
    "it is very hot today",
    "it is raining outside",
    "i am feeling happy",
    "i am a little tired",
    "let us practice speaking",
    "please listen carefully",
    "i understand a little",
    "speak clearly please",
    "one more time please",
    "that sounds good",
    "what do you think",
    "this is my mother",
    "this is my father",
    "i live with my family",
    "drive safely please",
    "call me later",
    "open the door please",
    "close the window",
    "turn on the light",
    "turn off the fan",
    "let us eat dinner",
    "the food is delicious",
    "i am full thank you",
    "have a good night",
    "see you tomorrow",
    "happy birthday to you",
    "congratulations",
    "good luck today",
    "take care of yourself",
    "i miss you",
    "i love my family",
    "practice makes perfect",
    "never give up",
    "keep trying please",
    "you are doing great",
    "let us try again",
]

MODE_ORDER = (
    "letters",
    "sounds",
    "beginner",
    "easy",
    "normal",
    "hard",
    "top",
    "impossible",
)

MODE_CONFIG = {
    "letters": {
        "label": "Letters",
        "word_count": 8,
        "letter_len": 1,
        "points": 8,
        "words": LETTERS,
        "emoji": "🔤",
        "hide_word": False,
        "speak_focus": True,
        "letter_label": "A–Z",
        "blurb": "You know ABC — hear the letter, say it, then the picture word.",
        "path": "start",
    },
    "sounds": {
        "label": "Sounds",
        "word_count": 8,
        "letter_len": 3,
        "points": 12,
        "words": SOUND_WORDS,
        "emoji": "🔊",
        "hide_word": False,
        "speak_focus": True,
        "letter_label": "blend 3 sounds",
        "blurb": "Hear /c/ /a/ /t/ — then say the word out loud.",
        "path": "start",
    },
    "beginner": {
        "label": "Beginner",
        "word_count": 8,
        "letter_min": 1,
        "letter_max": 3,
        "points": 15,
        "words": BEGINNER_WORDS,
        "emoji": "🌱",
        "hide_word": False,
        "speak_focus": True,
        "letter_label": "sight + short words",
        "blurb": "Little words you will say every day — I, you, yes, cat…",
        "path": "start",
    },
    "easy": {
        "label": "Easy",
        "word_count": 8,
        "letter_len": 3,
        "points": 20,
        "words": EASY_WORDS,
        "emoji": "🟢",
        "hide_word": False,
        "path": "words",
    },
    "normal": {
        "label": "Normal",
        "word_count": 8,
        "letter_len": 4,
        "points": 35,
        "words": NORMAL_WORDS,
        "emoji": "🟡",
        "hide_word": True,
    },
    "hard": {
        "label": "Hard",
        "word_count": 10,
        "letter_min": 5,
        "letter_max": 6,
        "points": 50,
        "words": HARD_WORDS,
        "emoji": "🔴",
        "hide_word": True,
    },
    "top": {
        "label": "Top",
        "word_count": 10,
        "letter_min": 7,
        "letter_max": 8,
        "points": 80,
        "words": TOP_WORDS,
        "emoji": "💎",
        "hide_word": True,
    },
    "impossible": {
        "label": "Family",
        "word_count": 8,
        "points": 100,
        "words": IMPOSSIBLE_PHRASES,
        "emoji": "🗣️",
        "phrases": True,
        "speak_focus": True,
        "hide_word": False,
        "blurb": "Grown-up spoken English — hear it, then say the phrase out loud.",
    },
}

WORD_EMOJI = {
    # Beginner sight words
    "i": "😊", "me": "🙋", "we": "👫", "you": "👉", "am": "🙋",
    "is": "➡️", "my": "💛", "the": "⭐", "yes": "👍", "no": "👎",
    "up": "⬆️", "in": "📥", "on": "📍", "go": "🏃", "see": "👀",
    "eat": "🍽️", "run": "🏃", "big": "🐘", "dig": "⛏️", "nap": "😴",
    "sit": "🪑", "hit": "🏏", "bit": "🍪", "dot": "⚫", "man": "👨",
    "log": "🪵", "hog": "🐗", "mat": "🧘", "sat": "😌",
    # Easy
    "cat": "🐱", "dog": "🐶", "bat": "🦇", "hat": "🎩", "rat": "🐀",
    "cap": "🧢", "map": "🗺️", "bag": "👜", "pig": "🐷", "sun": "☀️",
    "bun": "🍞", "cup": "☕", "pup": "🐶", "bus": "🚌", "jam": "🍓",
    "pan": "🍳", "van": "🚐", "bed": "🛏️", "pen": "🖊️", "hen": "🐔",
    "box": "📦", "fox": "🦊", "key": "🔑", "toy": "🧸", "boy": "👦",
    "cow": "🐄", "bee": "🐝", "ear": "👂", "ice": "🧊", "bug": "🐛",
    "mud": "🟤", "tub": "🛁", "cub": "🐻", "web": "🕸️", "egg": "🥚",
    "owl": "🦉", "ant": "🐜", "jet": "✈️", "net": "🥅", "pet": "🐾",
    "pot": "🍲", "hot": "🔥", "zip": "🤐", "lip": "👄", "pie": "🥧",
    "ham": "🍖", "nut": "🥜", "pea": "🟢", "tea": "🍵", "mug": "☕",
    "jar": "🫙", "lid": "🫙", "rug": "🧶", "sky": "🌌", "sea": "🌊",
    "yam": "🍠", "gum": "🫧", "hop": "🦘", "top": "🔝", "mop": "🧹",
    "mom": "👩", "dad": "👨", "kid": "🧒", "arm": "💪", "leg": "🦵",
    "toe": "🦶", "eye": "👁️", "car": "🚗", "fan": "🪭", "can": "🥫",
    "red": "🔴", "ten": "🔟", "six": "6️⃣",
    # Normal
    "book": "📖", "ball": "⚽", "bird": "🐦", "fish": "🐟", "frog": "🐸",
    "duck": "🦆", "lion": "🦁", "bear": "🐻", "goat": "🐐", "lamb": "🐑",
    "milk": "🥛", "cake": "🎂", "rice": "🍚", "corn": "🌽", "pear": "🍐",
    "plum": "🟣", "tree": "🌳", "leaf": "🍃", "seed": "🌱", "rain": "🌧️",
    "wind": "💨", "moon": "🌙", "star": "⭐", "ship": "🚢", "boat": "⛵",
    "road": "🛣️", "park": "🏞️", "home": "🏠", "door": "🚪", "hand": "✋",
    "foot": "🦶", "nose": "👃", "eyes": "👀", "face": "😊", "head": "🗣️",
    "hair": "💇", "play": "🎮", "jump": "🦘", "walk": "🚶", "sing": "🎤",
    "read": "📚", "stop": "🛑", "help": "🆘", "good": "👍", "blue": "🔵",
    "pink": "💗", "kite": "🪁", "doll": "🪆", "sock": "🧦", "toys": "🧸",
    "baby": "👶", "bell": "🔔", "belt": "👔", "coat": "🧥", "cold": "🥶",
    "farm": "🚜", "fire": "🔥", "flag": "🚩", "game": "🎮", "gift": "🎁",
    "gold": "🥇", "hill": "⛰️", "king": "👑", "lake": "🏞️", "love": "❤️",
    "nest": "🪺", "note": "📝", "open": "📂", "path": "🛤️", "pool": "🏊",
    "ring": "💍", "sand": "🏖️", "snow": "❄️", "swim": "🏊", "tail": "🐕",
    "town": "🏘️", "wall": "🧱", "warm": "☀️", "lamp": "💡", "fork": "🍴",
    "soup": "🍲", "meat": "🥩", "bean": "🫘", "chip": "🍟", "soda": "🥤",
    "wolf": "🐺", "deer": "🦌", "crab": "🦀", "seal": "🦭", "pony": "🐴",
    "crow": "🐦", "dove": "🕊️", "beak": "🐤", "wing": "🪶", "claw": "🐾",
    "desk": "🪑", "glue": "🧴", "clip": "📎", "tape": "📏", "song": "🎵",
    "band": "🎸", "drum": "🥁", "horn": "📯", "soap": "🧼",
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
    "shadow": "🌑", "silver": "🥈", "spider": "🕷️", "sunset": "🌅",
    "tiger": "🐯", "basket": "🧺", "bridge": "🌉", "candy": "🍬",
    "crown": "👑", "dream": "💭", "fairy": "🧚", "magic": "✨",
    "pizza": "🍕", "train": "🚂", "water": "💧", "whale": "🐋",
    "doctor": "🩺", "farmer": "🚜", "singer": "🎤", "soccer": "⚽",
    "tennis": "🎾", "jungle": "🌴", "island": "🏝️", "valley": "🏞️",
    "stream": "🏞️", "cloudy": "☁️", "sunny": "☀️", "pepper": "🌶️",
    "carrot": "🥕", "potato": "🥔", "tomato": "🍅", "grapes": "🍇",
    "muffin": "🧁", "waffle": "🧇", "saddle": "🐴", "helmet": "🪖",
    # Top
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
    "panther": "🐆", "quarter": "🪙", "backpack": "🎒", "baseball": "⚾",
    "football": "🏈", "notebook": "📓", "homework": "📝", "painting": "🎨",
    "sunshine": "☀️", "raincoat": "🧥", "firefly": "✨", "seashell": "🐚",
    "starfish": "⭐", "volcano": "🌋", "carnival": "🎡", "festival": "🎉",
    "princess": "👸", "wizardry": "🧙", "cupcake": "🧁",
}


def _unique(seq: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in seq:
        key = str(item).lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _pool_for_mode(mode: str) -> list[str]:
    """Words/phrases allowed for this mode."""
    cfg = MODE_CONFIG[mode]
    raw = _unique([w for w in cfg["words"] if w and str(w).strip()])
    if cfg.get("phrases"):
        return raw
    if "letter_min" in cfg:
        lo = cfg["letter_min"]
        hi = cfg["letter_max"]
        return [w for w in raw if lo <= len(w.replace(" ", "")) <= hi]
    n = cfg.get("letter_len", 3)
    return [w for w in raw if len(w) == n]


def mode_letter_label(mode: str) -> str:
    """Human-readable letter-length label for UI."""
    cfg = MODE_CONFIG[mode]
    if cfg.get("letter_label"):
        return cfg["letter_label"]
    if cfg.get("phrases"):
        return "phrases"
    if "letter_min" in cfg:
        if cfg["letter_min"] == cfg["letter_max"]:
            return str(cfg["letter_min"])
        return f"{cfg['letter_min']}–{cfg['letter_max']}"
    return str(cfg.get("letter_len", 3))


def speak_prompt(word: str, mode: str | None = None) -> str:
    """What TTS should say (Letters: 'A for apple')."""
    w = (word or "").strip().lower()
    if mode == "letters" and w in LETTER_EXAMPLE:
        return f"{w.upper()} for {LETTER_EXAMPLE[w]}"
    return word or ""


def pick_targets(
    mode: str,
    review: list[str] | None = None,
    liked: list[str] | None = None,
    disliked: list[str] | None = None,
) -> list[str]:
    """~60% new, ~40% review. Favorites first; skip 'not this one' when we can."""
    if mode not in MODE_CONFIG:
        raise ValueError(f"Unknown mode: {mode}")
    pool = _pool_for_mode(mode)
    if not pool:
        raise ValueError(f"No valid words for mode: {mode}")
    count = min(MODE_CONFIG[mode]["word_count"], len(pool))
    pool_set = set(pool)
    seen: set[str] = set()
    rev: list[str] = []
    for raw in list(liked or []) + list(review or []):
        w = str(raw).lower().strip()
        if w in pool_set and w not in seen:
            seen.add(w)
            rev.append(w)
    n_rev = min(int(round(count * 0.4)), len(rev), count)
    chosen_rev = random.sample(rev, n_rev) if n_rev else []
    skip = {str(w).lower().strip() for w in (disliked or [])}
    rest = [w for w in pool if w not in chosen_rev and w not in skip]
    if len(rest) < count - len(chosen_rev):
        rest = [w for w in pool if w not in chosen_rev]
    n_new = count - len(chosen_rev)
    chosen_new = random.sample(rest, min(n_new, len(rest))) if rest and n_new else []
    out = chosen_rev + chosen_new
    random.shuffle(out)
    return out


TALK_PACK = (
    ("hello", "👋"),
    ("thank you", "🙏"),
    ("please", "💛"),
    ("i am hungry", "🍽️"),
    ("i am fine", "😊"),
    ("can i have water", "💧"),
    ("good morning", "🌅"),
    ("i love you", "❤️"),
)


def daily_talk_items() -> list[dict]:
    """Same 6 life phrases for everyone today — hear and say."""
    from datetime import date

    start = int(date.today().strftime("%Y%m%d")) % len(TALK_PACK)
    items = []
    for i in range(6):
        w, h = TALK_PACK[(start + i) % len(TALK_PACK)]
        items.append({"word": w, "hint": h, "speak": w})
    return items


def word_of_the_day() -> dict:
    """One Easy word for everyone today."""
    from datetime import date

    pool = _pool_for_mode("easy") or ["cat", "sun", "hat"]
    idx = int(date.today().strftime("%Y%m%d")) % len(pool)
    w = pool[idx]
    return {
        "word": w,
        "hint": word_hint(w, "easy"),
        "speak": speak_prompt(w, "easy"),
    }


def pick_space_word(review: list[str] | None = None) -> dict:
    """Short word for Space collect-and-say."""
    pool = [w for w in _pool_for_mode("easy") if 3 <= len(w) <= 4]
    if not pool:
        pool = ["cat", "sun", "hat"]
    review_ok = [w for w in (review or []) if w in pool]
    if review_ok and random.random() < 0.4:
        word = random.choice(review_ok)
    else:
        word = random.choice(pool)
    letters = list(word)
    shuffled = letters[:]
    random.shuffle(shuffled)
    if shuffled == letters and len(letters) > 1:
        shuffled[0], shuffled[-1] = shuffled[-1], shuffled[0]
    return {
        "word": word,
        "hint": word_hint(word, "easy"),
        "speak": word,
        "letters": shuffled,
        "points": MODE_CONFIG["easy"]["points"],
    }


def get_round_items(
    mode: str,
    review: list[str] | None = None,
    liked: list[str] | None = None,
    disliked: list[str] | None = None,
) -> list[dict]:
    """Words plus hint + speak text for one Spell round."""
    return [
        {"word": w, "hint": word_hint(w, mode), "speak": speak_prompt(w, mode)}
        for w in get_round_words(mode, review, liked, disliked)
    ]


def get_round_words(
    mode: str,
    review: list[str] | None = None,
    liked: list[str] | None = None,
    disliked: list[str] | None = None,
) -> list[str]:
    """Return a small random set for one game (not the full word bank)."""
    return pick_targets(mode, review, liked, disliked)


def word_hint(word: str, mode: str | None = None) -> str:
    key = word.lower().strip()
    if mode == "letters" and key in LETTER_EMOJI:
        return LETTER_EMOJI[key]
    if key in WORD_EMOJI:
        return WORD_EMOJI[key]
    if len(key) == 1 and key in LETTER_EMOJI:
        return LETTER_EMOJI[key]
    if " " in key:
        return "🗣️"
    return "✨"


def _letter_indexes(word: str) -> list[int]:
    return [i for i, ch in enumerate(word) if ch.isalpha()]


def get_quiz_questions(
    mode: str,
    num_choices: int = 4,
    review: list[str] | None = None,
    liked: list[str] | None = None,
    disliked: list[str] | None = None,
) -> list[dict]:
    """
    Fill-in-the-blank quiz: one letter is missing from the word.
    Phrase modes are not used for quiz (see app routes).
    Letters: first letter of the picture word (A from apple).
    """
    if mode not in MODE_CONFIG:
        raise ValueError(f"Unknown mode: {mode}")
    if MODE_CONFIG[mode].get("phrases"):
        return []
    if mode == "letters":
        return _letter_quiz_questions(num_choices, review)
    pool = _pool_for_mode(mode)
    if not pool:
        raise ValueError(f"No valid words for mode: {mode}")

    targets = pick_targets(mode, review, liked, disliked)
    alphabet = list("abcdefghijklmnopqrstuvwxyz")
    n_choices = max(2, min(num_choices, 6))

    questions = []
    for word in targets:
        word = word.lower()
        letters = _letter_indexes(word)
        if len(letters) >= 3:
            blank_index = random.choice(letters[1:-1])
        else:
            blank_index = letters[0] if letters else 0

        missing = word[blank_index]
        display = list(word)
        display[blank_index] = ""

        wrong_letters = [c for c in alphabet if c != missing]
        distractors = random.sample(wrong_letters, n_choices - 1)
        choices = distractors + [missing]
        random.shuffle(choices)

        questions.append(
            {
                "word": word,
                "hint": word_hint(word, mode),
                "blank_index": blank_index,
                "missing": missing,
                "display": display,
                "choices": choices,
                "quiz_type": "letter",
            }
        )
    return questions


def _sample_letter_bank(count: int, review: list[str] | None = None) -> list:
    bank = list(LETTER_BANK)
    if not review:
        return random.sample(bank, min(count, len(bank)))
    prefer = [row for row in bank if row[0] in {str(w).lower() for w in review}]
    n_rev = min(int(round(count * 0.4)), len(prefer), count)
    picked = random.sample(prefer, n_rev) if n_rev else []
    rest = [row for row in bank if row not in picked]
    need = count - len(picked)
    if need and rest:
        picked += random.sample(rest, min(need, len(rest)))
    random.shuffle(picked)
    return picked[:count]


def _letter_quiz_questions(
    num_choices: int = 4, review: list[str] | None = None
) -> list[dict]:
    """'_pple' → tap A. Uses the picture word for each letter."""
    alphabet = list("abcdefghijklmnopqrstuvwxyz")
    n_choices = max(2, min(num_choices, 6))
    count = min(MODE_CONFIG["letters"]["word_count"], len(LETTER_BANK))
    bank = _sample_letter_bank(count, review)
    questions = []
    for letter, example, emoji in bank:
        word = example.lower()
        blank_index = 0
        missing = word[0] if word else letter
        display = list(word)
        if display:
            display[0] = ""
        wrong = [c for c in alphabet if c != missing]
        distractors = random.sample(wrong, n_choices - 1)
        choices = distractors + [missing]
        random.shuffle(choices)
        questions.append(
            {
                "word": word,
                "hint": emoji,
                "blank_index": blank_index,
                "missing": missing,
                "display": display,
                "choices": choices,
                "quiz_type": "letter",
            }
        )
    return questions


def _letter_picture_questions(
    num_choices: int = 4, review: list[str] | None = None
) -> list[dict]:
    """Picture → pick the letter."""
    n_choices = max(2, min(num_choices, 6))
    count = min(MODE_CONFIG["letters"]["word_count"], len(LETTER_BANK))
    bank = _sample_letter_bank(count, review)
    alphabet = [row[0] for row in LETTER_BANK]
    questions = []
    for letter, _example, emoji in bank:
        wrong = [c for c in alphabet if c != letter]
        distractors = random.sample(wrong, n_choices - 1)
        choices = distractors + [letter]
        random.shuffle(choices)
        questions.append(
            {
                "word": letter,
                "hint": emoji,
                "choices": choices,
                "quiz_type": "picture",
            }
        )
    return questions


def get_picture_quiz_questions(
    mode: str,
    num_choices: int = 4,
    review: list[str] | None = None,
    liked: list[str] | None = None,
    disliked: list[str] | None = None,
) -> list[dict]:
    """
    Picture quiz: show emoji, pick the correct word from choices.
    Skips words with no real picture. Phrase modes return no questions.
    """
    if mode not in MODE_CONFIG:
        raise ValueError(f"Unknown mode: {mode}")
    if MODE_CONFIG[mode].get("phrases"):
        return []
    if mode == "letters":
        return _letter_picture_questions(num_choices, review)
    pool = [w for w in _pool_for_mode(mode) if w in WORD_EMOJI]
    if not pool:
        raise ValueError(f"No valid words for mode: {mode}")

    targets = [w for w in pick_targets(mode, review, liked, disliked) if w in WORD_EMOJI]
    if len(targets) < min(MODE_CONFIG[mode]["word_count"], len(pool)):
        extra = [w for w in pool if w not in targets]
        need = min(MODE_CONFIG[mode]["word_count"], len(pool)) - len(targets)
        if extra and need > 0:
            targets += random.sample(extra, min(need, len(extra)))
    n_choices = max(2, min(num_choices, len(pool)))

    questions = []
    for word in targets:
        word = word.lower()
        wrong = [w for w in pool if w != word]
        if len(wrong) >= n_choices - 1:
            distractors = random.sample(wrong, n_choices - 1)
        else:
            distractors = wrong
        choices = distractors + [word]
        random.shuffle(choices)
        questions.append(
            {
                "word": word,
                "hint": word_hint(word, mode),
                "choices": choices,
                "quiz_type": "picture",
            }
        )
    return questions
