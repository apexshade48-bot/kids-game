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
    # food / home / nature
    "pie", "ham", "nut", "pea", "tea", "mug", "jar", "lid", "rug", "sky",
    "sea", "mud", "yam", "gum", "pop", "hop", "top", "mop", "cop", "mom",
    "dad", "kid", "man", "arm", "leg", "toe", "eye", "jaw", "gum", "wax",
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
    # school / food / animals
    "desk", "lamp", "fork", "soup", "meat", "bean", "chip", "soda", "wolf", "deer",
    "crab", "seal", "pony", "mule", "crow", "dove", "beak", "wing", "claw", "bark",
    "desk", "glue", "clip", "tape", "math", "song", "band", "drum", "flute", "horn",
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
    # extra school / food / adventure
    "doctor", "farmer", "singer", "soccer", "tennis", "jungle", "island",
    "valley", "stream", "cloudy", "sunny", "pepper", "carrot", "potato",
    "tomato", "orange", "grapes", "muffin", "waffle", "saddle", "helmet",
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
    # longer adventure / school
    "backpack", "baseball", "football", "notebook", "homework", "painting",
    "sunshine", "raincoat", "firefly", "seashell", "starfish", "volcano",
    "treasure", "carnival", "festival", "princess", "wizardry", "cupcake",
]

# Spoken English practice for adults (parents) — short everyday phrases
IMPOSSIBLE_PHRASES = [
    "hello how are you",
    "good morning",
    "good afternoon",
    "good evening",
    "nice to meet you",
    "how was your day",
    "what is your name",
    "my name is",
    "where are you from",
    "i am from",
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
    "i work every day",
    "i go to the market",
    "the weather is nice",
    "it is very hot today",
    "it is raining outside",
    "i am feeling happy",
    "i am a little tired",
    "let us practice speaking",
    "please listen carefully",
    "i understand a little",
    "can you help my english",
    "speak clearly please",
    "one more time please",
    "that sounds good",
    "i agree with you",
    "what do you think",
    "tell me about yourself",
    "i live with my family",
    "this is my mother",
    "this is my father",
    "how was work today",
    "let us go home",
    "drive safely please",
    "call me later",
    "i will call you",
    "send me a message",
    "open the door please",
    "close the window",
    "turn on the light",
    "turn off the fan",
    "wash your hands",
    "let us eat dinner",
    "the food is delicious",
    "i am full thank you",
    "have a good night",
    "sweet dreams",
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
    "impossible": {
        "label": "Impossible",
        "word_count": 10,
        "points": 100,  # big reward for spoken English practice
        "words": IMPOSSIBLE_PHRASES,
        "emoji": "🔥",
        "phrases": True,
        "speak_focus": True,
        "blurb": "Adult spoken English — say full phrases out loud.",
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
    "pink": "💗", "kite": "🪁", "doll": "🪆", "sock": "🧦", "toys": "🧸",
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
    """Words/phrases allowed for this mode."""
    cfg = MODE_CONFIG[mode]
    raw = [w.lower().strip() for w in cfg["words"] if w and str(w).strip()]
    # Spoken-English phrase mode (Impossible): keep full phrases
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
    # Phrase mode: use a speaking mic emoji
    if " " in key:
        return "🗣️"
    return "✨"


def get_quiz_questions(mode: str, num_choices: int = 4) -> list[dict]:
    """
    Fill-in-the-blank quiz: one letter is missing from the word.
    Each item:
      word, hint, blank_index, missing (letter), display (list of letters with '' for blank),
      choices (letter options including the correct one).
    """
    if mode not in MODE_CONFIG:
        raise ValueError(f"Unknown mode: {mode}")
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
        # Prefer blanking a middle letter when possible (easier for kids).
        if len(word) >= 3:
            blank_index = random.randint(1, len(word) - 2)
        else:
            blank_index = random.randint(0, len(word) - 1)

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
    Each item: {word, hint, choices, quiz_type: 'picture'}
    """
    if mode not in MODE_CONFIG:
        raise ValueError(f"Unknown mode: {mode}")
    pool = _pool_for_mode(mode)
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