"""Word lists for kids word game by difficulty mode."""

import random

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

MODE_ORDER = ("easy", "normal", "hard", "top", "impossible")

MODE_CONFIG = {
    "easy": {
        "label": "Easy",
        "word_count": 8,
        "letter_len": 3,
        "points": 20,
        "words": EASY_WORDS,
        "emoji": "🟢",
        "hide_word": False,
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
    if cfg.get("phrases"):
        return "phrases"
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
    key = word.lower().strip()
    if key in WORD_EMOJI:
        return WORD_EMOJI[key]
    if " " in key:
        return "🗣️"
    return "✨"


def _letter_indexes(word: str) -> list[int]:
    return [i for i, ch in enumerate(word) if ch.isalpha()]


def get_quiz_questions(mode: str, num_choices: int = 4) -> list[dict]:
    """
    Fill-in-the-blank quiz: one letter is missing from the word.
    Phrase modes are not used for quiz (see app routes).
    """
    if mode not in MODE_CONFIG:
        raise ValueError(f"Unknown mode: {mode}")
    if MODE_CONFIG[mode].get("phrases"):
        return []
    pool = _pool_for_mode(mode)
    if not pool:
        raise ValueError(f"No valid words for mode: {mode}")

    count = min(MODE_CONFIG[mode]["word_count"], len(pool))
    targets = random.sample(pool, count)
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
                "hint": word_hint(word),
                "blank_index": blank_index,
                "missing": missing,
                "display": display,
                "choices": choices,
                "quiz_type": "letter",
            }
        )
    return questions


def get_picture_quiz_questions(mode: str, num_choices: int = 4) -> list[dict]:
    """
    Picture quiz: show emoji, pick the correct word from choices.
    Skips words with no real picture. Phrase modes return no questions.
    """
    if mode not in MODE_CONFIG:
        raise ValueError(f"Unknown mode: {mode}")
    if MODE_CONFIG[mode].get("phrases"):
        return []
    pool = [w for w in _pool_for_mode(mode) if w in WORD_EMOJI]
    if not pool:
        raise ValueError(f"No valid words for mode: {mode}")

    count = min(MODE_CONFIG[mode]["word_count"], len(pool))
    targets = random.sample(pool, count)
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
                "hint": word_hint(word),
                "choices": choices,
                "quiz_type": "picture",
            }
        )
    return questions
