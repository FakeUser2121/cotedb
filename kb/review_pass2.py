#!/usr/bin/env python3
"""P1 review pass 2: 3-9 band decisions (2026-10-16).

Run AFTER pass1. Idempotent: aliases deduped by (char_id, normalized);
claims only touch unreviewed / unknown / provisional-shell candidates.
Claims always re-normalize their raw key (so 'Ryouta'->'ryota', 'Toudou'->'todo').
"""
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_mine import normalize  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "cote_kb.db")

# canonical -> existing char_id when slug(canonical) differs (seed/legacy ids)
CID_OVERRIDE = {
    "Tokitou Katsumi": "tokitou",
    "Nishimura Ryuko": "nishimura-ryuuko",
    "Hondou Ryotaro": "hondou-ryoutaro",
}

# surnames that map to >1 person (or are already claimed by another char):
# never auto-claimed from the NEW_CHARS loop
FAMILY_SKIP = {"todo", "horikita", "ishikura", "kamogawa"}

# canonical, tier, status, note  (only created if char_id missing; seed rows win)
NEW_CHARS = {
    # --- surname families with 2 people: Kou first, Wataru second (claim order) ---
    "Ijuin Kou": (3, "confirmed",
                  "Y1 bare mentions = Horikita's-class (1-C) classmate; "
                  "Y2V12 'Ijūin Kou' 2nd-Yr Class B participants"),
    "Ijuin Wataru": (4, "confirmed",
                     "Y2V10 offense-nomination list only; DIFFERENT given from "
                     "Ijūin Kou — possibly a second Ijūin (P2 verify)"),
    # --- exam-roster students, full name known ---
    "Isoyama Nagisa": (3, "confirmed",
                       "Ryuuen-class member; Y1 expel-vote nominee; Y2 rosters"),
    "Iguchi Yuri": (4, "confirmed",
                    "Y2V12 2nd-Yr Class D participants; Y2V11 roster Class C"),
    "Hagiwara Chihaya": (4, "confirmed", "Y2V11 exam roster list"),
    "Namekawa Azuki": (4, "confirmed", "Y2V11 exam roster list"),
    "Tatewaki Aoi": (4, "confirmed", "Y2V11 exam roster list"),
    "Osaki Noa": (4, "confirmed", "Y2V11 exam roster list"),
    "Aragaki Itsuki": (4, "confirmed", "Y2V12 2nd-Yr Class D participants"),
    "Ishimaru Yuriko": (4, "confirmed", "Y1 participant list"),
    "Onuki Nagisa": (4, "confirmed", "Y1 participant list ('Ōnuki Nagisa')"),
    "Yoshimoto Kosetsu": (4, "confirmed",
                          "Y2V12 participants ('Yoshimoto Kōsetsu'; also V0)"),
    "Inoue Toa": (4, "confirmed",
                  "Y2 roster list w/ Ibuki, Okabe, Morofuji; exam round w/ Tanihara"),
    "Ayase Natsu": (4, "confirmed", "third-year Class C group representative (Y1)"),
    "Ikari Momoko": (4, "confirmed", "third-year Class B group representative (Y1)"),
    "Nakaizumi Shouhei": (4, "confirmed", "Y2V12 Class C discussion roster"),
    # --- known-list students (3-9 band) ---
    "Takarajima Miko": (4, "confirmed", "Y2V12 Class C discussion roster"),
    "Shintoku Taro": (4, "confirmed", "Y2V11 roster, first-year Class C"),
    "Yanagi Yasuhisa": (4, "confirmed", "Y2V11 roster, first-year Class B"),
    "Eikura Mani": (4, "confirmed", "Y2V11 roster, first-year Class B"),
    "Fukuchi Hinano": (4, "confirmed", "Y2V11 roster list (year block P2-verify)"),
    "Suminokura Mami": (4, "confirmed", "Y2V12 Class C discussion roster"),
    "Dodo Michimichi": (4, "confirmed", "Y2V4: 'most gifted third-year student'"),
    "Hatate Kaoru": (4, "confirmed", "Y2V12 Class C discussion roster"),
    "Todo Chikon": (4, "confirmed",
                    "Y2V8 Ryuuen-group member (with Kaneda, Ishizaki)"),
    "Toudou Rin": (4, "confirmed", "Y2V11 roster (same block as Amasawa Ichika)"),
    "Suzukake Tanji": (4, "confirmed",
                       "y0 adult: resume + voice-recording logs (V0)"),
    # --- single-name people ---
    "Negishi": (4, "provisional", "first-year girl, Y2V12.5; given unknown"),
    "Ibeyama": (4, "provisional", "3-D information source, Y2V9.5; given unknown"),
    "Moeka": (3, "confirmed",
              "2-C girl who quits school (Y2V9); also called Suchi/Succhii"),
    "Ohba": (4, "provisional",
             "y0 adult: phone contact + 'Ohba group' black market (V0)"),
    "Mikuru": (4, "provisional", "y0 child in V0 training scene (kicked by instructor)"),
    "Miyako": (4, "provisional", "y0 'Minister Miyako', fourth faction (V0)"),
    "Taguri": (4, "provisional", "second-year, QR-code game scene (Y2)"),
    "Miya": (4, "provisional",
             "1-B girl, Y1 ('Miya-san from Class 1-B'); single name — surname?"),
    # --- people with known given from other mentions ---
    "Kiryuin Fuuka": (3, "confirmed",
                      "3rd-year Class B (Y2V9.5); Fuuka SS (Y2V4.5); "
                      "canonical matches seed 'Kiryuin, Fuuka' (no dup slug)"),
    "Morofuji Rika": (4, "confirmed", "2-B girl, Y2V4 + Y2V12 rosters"),
    "Kamogawa Toshizou": (3, "confirmed",
                          "y0/y1 Senator; father of the y0 student Kamogawa"),
    "Nishimura Ryuko": (4, "confirmed", "Y1V11 Event Selection Class C team"),
    "Tsukasaki Taiga": (4, "confirmed", "Y1V11 Event Selection Class A team"),
    "Ishida Yuusuke": (4, "confirmed", "Y1V11 Event Selection Class A team"),
    "Tokitou Katsumi": (4, "confirmed",
                        "given from Y2V4.5 'Ichinose's classmate Tokitō Katsumi'"),
}

# raw form, canonical target, form_type, note  (raw normalized here)
ALIASES = [
    # nicknames / dialogue / TL variants
    ("Ayanon", "Ayanokouji Kiyotaka", "nickname", "Hasebe nickname (Y1V6)"),
    ("Ayano", "Ayanokouji Kiyotaka", "variant", "Hirata address form"),
    ("Ayanakouji", "Ayanokouji Kiyotaka", "variant", "typo/MTL"),
    ("Ayanokouji-dono", "Ayanokouji Kiyotaka", "honorific", "Sotomura form"),
    ("Ayanokouji-shi", "Ayanokouji Kiyotaka", "honorific", "-shi address form"),
    ("Ayanokōji-boy", "Ayanokouji Kiyotaka", "nickname", "Ryuuen-group slang (Y1V10)"),
    ("Ayanokouji-boy", "Ayanokouji Kiyotaka", "nickname", "slang (ascii macron)"),
    ("Horikita-shi", "Horikita Suzune", "honorific", "-shi address form"),
    ("Horikita-girl", "Horikita Suzune", "nickname", "Ryuuen-group slang (Y1V10)"),
    ("Horiikta", "Horikita Suzune", "variant", "MTL typo"),
    ("Ryuuen-shi", "Ryuuen Kakeru", "honorific", "-shi address form"),
    ("Miyatchi", "Miyake Akito", "nickname", "nickname spelling variant"),
    ("Miyacchi", "Miyake Akito", "nickname", "nickname spelling variant"),
    ("Suchi", "Moeka", "nickname", "nickname (Y2V9, TL note)"),
    ("Reon", "Kondou Reo", "variant", "TL spelling variant of Reo"),
    ("Inokashira", "Inogashira Kokoro", "variant", "TL spelling variant"),
    ("Tsutsube", "Tsube Hitomi", "variant", "TL typo of surname (Y1V11 line)"),
    # given names verified against full-name / class-list hits
    ("Hitomi", "Tsube Hitomi", "given",
     "every corpus Hitomi = Tsube (order variants 'Hitomi Tsube', 'Hitomi Tsutsube')"),
    ("Kenta", "Yoshida Kenta", "given", "given name"),
    ("Yui", "Ninomiya Yui", "given", "given name"),
    ("Hiroya", "Tokitou Hiroya", "given", "given name"),
    ("Yasumi", "Sawada Yasumi", "given", "given name"),
    ("Yuji", "Nomura Yuuji", "given", "given name (Yuuji/Yūji variants)"),
    ("Koharu", "Yano Koharu", "given", "given name"),
    ("Hidetoshi", "Suzuki Hidetoshi", "given", "given name"),
    ("Masashi", "Sonoda Masashi", "given", "given name"),
    ("Takurou", "Morishige Takurou", "given", "given name (key: takuro)"),
    ("Ryouta", "Beppu Ryouta", "given", "given name (key: ryota)"),
    ("Ryouko", "Nishikawa Ryouko", "given", "given name"),
    ("Ryūko", "Nishimura Ryuko", "given", "given name (Y1V11)"),
    ("Hiroshi", "Sugio Hiroshi", "given", "given name (Y1V11 list)"),
    ("Kayoko", "Ishikura Kayoko", "given",
     "eval-sheet lists 'Ishikura Kayoko' (Y1V1-era); surname shared w/ "
     "3rd-yr Class B Ishikura (Y1V8) — split at P2 (see char 'ishikura')"),
    ("Makoto", "Sumida Makoto", "given", "given name"),
    ("Shinji", "Matoba Shinji", "given", "given name"),
    ("Sana", "Azuma Sana", "given", "given name"),
    ("Taiga", "Tsukasaki Taiga", "given", "given name"),
    ("Yūsuke", "Ishida Yuusuke", "given", "given name (Y1V11)"),
    ("Shihori", "Tsukaji Shihori", "given", "given name"),
    ("Mao", "Tanihara Mao", "given", "given name"),
    ("Mariko", "Yajima Mariko", "given",
     "given name ('Yashima Mariko' Y1V4 roster = TL typo of Yajima)"),
    ("Emi", "Tamiya Emi", "given", "given name"),
    ("Haruto", "Yonezu Haruto", "given", "given name"),
    ("Mani", "Eikura Mani", "given", "given name"),
    ("Taro", "Shintoku Taro", "given", "given name"),
    ("Miko", "Takarajima Miko", "given", "given name"),
    ("Setsuya", "Minami Setsuya", "given", "given name"),
    ("Hakuo", "Minami Hakuo", "given", "given name"),
    ("Susumu", "Makida Susumu", "given", "given name (Makida/Makita TL)"),
    ("Yasuhisa", "Yanagi Yasuhisa", "given", "given name"),
    ("Katsumi", "Tokitou Katsumi", "given", "given name (Y2V4.5)"),
    ("Kozue", "Minamikata Kozue", "given", "given name"),
    ("Chiyo", "Sonoda Chiyo", "given", "given name"),
    ("Shinobu", "Fukuyama Shinobu", "given", "given name (Y1V11) — upgrades pass1 unknown"),
    ("Hinano", "Fukuchi Hinano", "given", "given name"),
    ("Chikon", "Todo Chikon", "given", "given name"),
    ("Rin", "Toudou Rin", "given", "given name (Y2V11) — watch for other Rin"),
    ("Michimichi", "Dodo Michimichi", "given", "given name"),
    ("Shouhei", "Nakaizumi Shouhei", "given", "given name (Y2V12)"),
    ("Fuuka", "Kiryuin Fuuka", "given", "given name"),
    ("Mami", "Suminokura Mami", "given", "given name"),
    ("Kaoru", "Hatate Kaoru", "given", "given name"),
    ("Ryotarō", "Hondou Ryotaro", "given",
     "confirmed: 'Hondō Ryotarō' event roster (1-C group)"),
    ("Kyogo", "Komiya Kyogo", "given", "Y3V1 'Class 2-B's Komiya Kyogo'"),
    ("Soshi", "Miyamoto Soshi", "given", "'Sōshi Miyamoto' — key soshi"),
    ("Ruri", "Ichihashi Ruri", "given", "given name"),
    ("Takumi", "Oda Takumi", "given", "given name (participant lists)"),
    ("Wataru", "Ijuin Wataru", "given", "Y2V10 nomination list"),
    ("Natsu", "Ayase Natsu", "given", "given name"),
    ("Momoko", "Ikari Momoko", "given", "given name"),
    ("Toa", "Inoue Toa", "given", "given name"),
    ("Itsuki", "Aragaki Itsuki", "given", "given name"),
    ("Chihaya", "Hagiwara Chihaya", "given", "given name"),
    ("Azuki", "Namekawa Azuki", "given", "given name"),
    ("Aoi", "Tatewaki Aoi", "given", "given name"),
    ("Noa", "Osaki Noa", "given", "given name"),
    ("Yuriko", "Ishimaru Yuriko", "given", "given name"),
    ("Kosetsu", "Yoshimoto Kosetsu", "given", "given name ('Kōsetsu')"),
    ("Toshizou", "Kamogawa Toshizou", "given",
     "Senator Kamogawa Toshizou (y0/y1 politics) — NOT the y0 student Kamogawa"),
    ("Tanji", "Suzukake Tanji", "given",
     "y0 adult: resume + voice-recording logs (V0)"),
]

# explicit family claims: (raw, target canonical, note) — used for single-name
# people (family == whole name), upgrades of E1 shells, and noted cases.
FAMILY_CLAIMS = [
    ("Negishi", "Negishi", "surname-only student"),
    ("Ibeyama", "Ibeyama", "surname-only student"),
    ("Moeka", "Moeka", "single-name student"),
    ("Ohba", "Ohba", "y0 adult surname"),
    ("Mikuru", "Mikuru", "single-name y0 child"),
    ("Miyako", "Miyako", "y0 Minister surname"),
    ("Taguri", "Taguri", "single-name second-year"),
    ("Miya", "Miya", "single-name 1-B girl"),
    ("Nakaizumi", "Nakaizumi Shouhei", "surname (upgrades E1 shell)"),
    ("Suzukake", "Suzukake Tanji", "surname (upgrades E1 shell)"),
    ("Ijuin", "Ijuin Kou",
     "family: bare mentions all Horikita-class (Kou); 'Wataru Ijūin' Y2V10 is second, distinct given"),
    ("Inoue", "Inoue Toa", "surname (normalize Inoue->inoe)"),
    ("Ikari", "Ikari Momoko", "surname"),
    ("Ayase", "Ayase Natsu", "surname — NOT a place (also a cherry name 'Omuro')"),
    ("Yoshimoto", "Yoshimoto Kosetsu", "surname"),
    ("Isoyama", "Isoyama Nagisa", "surname"),
    ("Iguchi", "Iguchi Yuri", "surname"),
    ("Hagiwara", "Hagiwara Chihaya", "surname"),
    ("Namekawa", "Namekawa Azuki", "surname"),
    ("Tatewaki", "Tatewaki Aoi", "surname"),
    ("Osaki", "Osaki Noa", "surname"),
    ("Aragaki", "Aragaki Itsuki", "surname"),
    ("Ishimaru", "Ishimaru Yuriko", "surname"),
    ("Onuki", "Onuki Nagisa", "surname"),
    ("Kamogawa", "Kamogawa Toshizou",
     "SKIP-auto: bare 'Kamogawa' = y0 student char; senator keeps family alias only"),
]

# kept unresolved
UNKNOWN_NOTES = {
    "Todo": "family ambiguous: Chikon Todo (Y2V8) vs Toudou Rin (Y2V11, same key 'todo')",
    "Goro": "ambiguous given: Toyohashi Goro (Y2 1-A) vs Gorou Ishigami (y0 chairman, 60+)",
    "Kiyo": "unidentified nickname: 'Kiryūin and Kiyo' (Y2V9.5 afterword)",
    "Ko": "stammer fragment 'Inogashira Ko-Ko' (Y1V1) — not a name",
    "Kouji": "given of Machida Kouji (seed 1-A); uniqueness unverified",
    "Ryuji": "ambiguous given: Kanzaki Ryuuji (1-B) OR y0 boy (Ryuuji/Fuji/Nogi)",
    "Satoru": "ambiguous given: Satonaka Satoru + Kaneda Satoru",
    "Kyōsuke": "ambiguous given: Okiya Kyōsuke + Okitani Kyōsuke",
    "Shigeru": "ambiguous given (seed-shared): Takemoto Shigeru + others",
    "Nagisa": "ambiguous given: Isoyama Nagisa + Ōnuki Nagisa",
    "Fujirika": "TL mangled form of 'Morofuji Rika' (reversed) — not a separate person",
}

# noise: raws chosen so normalize(raw) matches the candidate key exactly
NOISE = [
    # English / grammar / interjections
    "Citizens", "Getting", "Unexpected", "Truth", "Guess", "Surprisingly", "Level",
    "Oi", "Cards", "A-rated", "General", "Civic", "Does", "Do", "Karate",
    "Favorite", "Standard", "Sign", "Scouts", "Hunt", "Expel", "Changing",
    "Ignoring", "Lovely", "Expulsion", "Arrow", "Calm", "Voting", "Leaving",
    "Tennis", "Became", "Evaluation", "Golden", "Be", "Different", "Strength",
    "Against", "Gun", "Choice", "Support", "Meeting", "Japanese-style",
    "Plan", "Child", "Judo", "Hawaii", "Hawai", "Victory", "Troubles", "Move",
    "Extra", "First-year", "Spend", "Being", "Sensing", "Participation",
    "Swimming", "More", "Fire", "Grip", "Water", "Tug", "Indeed", "Name",
    "Father", "Looking", "Failures", "She'd", "His", "Has", "Invitation",
    "Relationship", "Whose", "Android", "Individual", "Rule", "Relay", "Proof",
    "Farewell", "Prologue", "Secret", "Due", "Cruise", "Facing", "Results",
    "Person", "Restriction", "Jumping", "Saying", "Heart", "I'mma", "Average",
    "Survival", "Groups", "Deadline", "Limit", "Condition", "Measurement",
    "Chicken", "Full", "Little", "Ticket", "Clock", "Elimination", "Interval",
    "Whenever", "Care", "Facilities", "Society", "Strategy", "Gymnasium",
    "Violence", "Normally", "Rep", "Ocean", "You've", "Past", "Celsius",
    "Turning", "Ranking", "Suddenly", "Put", "Intentions", "Classmates",
    "Reading", "Head", "Registration", "Sea", "Open", "Earth", "Penalty",
    "Up", "Limited", "Translation", "City", "University", "Structure", "Dreams",
    "Association", "Mobilize", "Midterm", "Downloading", "App", "Symphony",
    "French", "Watch", "Friendship", "Sudden", "Tumultuous", "Excluding",
    "Saving", "Taking", "Boundary", "Meaning", "False", "Teamwork", "Rises",
    "Regarding", "Gentle", "Infinite", "Troubled", "Dangers", "Lurk", "Smiles",
    "Calculations", "Curtains", "Allocation", "Competitors", "Recommended",
    "Grade", "Dash", "Meter", "Ds", "Formation", "Settle", "Intersecting",
    "Thoughts", "Heights", "Disastrous", "Turbulent", "Landed", "Choosing",
    "Nature", "Girls", "Ubiquitous", "Lost", "Blind", "Spot", "Intention",
    "Works", "Ancient", "World", "Heritage", "Woah", "B-but", "Deserted",
    "Storm", "Brother", "Sister", "Dropouts", "Using", "Votes", "Education",
    "Allotted", "Studies", "Archery", "Rock", "Dear", "Operating", "Stage",
    "Problematic", "Intensifying", "Fuss", "Them", "Alone", "Tapestry",
    "Voice", "Based", "Back", "Strategies", "Amidst", "Travel", "Companion",
    "Invisible", "Aloof", "Colors", "Seeds", "Enjoyable", "Link", "Pair",
    "Mobile", "Correct", "Problems", "Haaa", "Second-", "Confidential",
    "C-class", "D-class", "Unable", "Translations", "Color", "Fun", "Growth",
    "Us", "Filled", "Women", "Inevitable", "Hearts", "Touch", "Bit", "Favour",
    "Older", "Definitely", "Feelings", "Run", "Member", "Activity", "Letter",
    "Requiring", "Approaching", "Premonition", "Concern", "Especially",
    "End-of-", "Lives", "Sake", "Car", "Zero", "Read", "Waiting", "Friends",
    "Prediction", "Lies", "Generation", "Heaven", "Hell", "Regardless",
    "Spartan", "Difference", "Escape", "Zodiac", "Outcomes", "Beside",
    "Horse", "Suppose", "Rat", "Rooster", "Angel", "Halloween", "He'd",
    "Number", "Luck", "Raising", "Lane", "Wins", "Deciding", "Including",
    "Footsteps", "Whatever", "Revocation", "Letting", "Written", "Evil",
    "Nevertheless", "Thereupon", "Apparent", "Sun", "Basketball", "Going",
    "Ceremony", "Begin", "Phone", "Call", "Reflected", "Note", "Calculated",
    "Senpais", "Observing", "Wunderkind", "Further", "Win", "Main", "Tears",
    "Sky", "Mode", "Laughing", "Treasure", "Conditions", "Increased",
    "Complicated", "Weapon", "Shuttle", "Oh", "Action", "Situations",
    "Confused", "Thursdays", "Feeling", "Offense", "Awakening", "Exchange",
    "Experience", "Ordinary", "Recess", "Promise", "Thump", "Seems", "Ears",
    "Yo", "Mornin", "Bacon", "Palate", "Prince", "Saint", "Alerts", "Harbors",
    "Favor", "Prof", "King", "Panda", "Boston", "Saitama", "Class", "Scots",
    "Shed", "Hose", "Fol", "Sems", "Hed", "Find", "Immediately", "Roster",
    # typos / TL manglings seen in the band
    "Meting", "Trobles", "Trobled", "Inded", "Quen", "Loking", "Grops",
    "Yove", "Artbok", "Hallowen", "Bethoven", "Darjeling", "Disastros",
    "Ubiquitos", "Dropots", "Bondary", "Tumultuos", "Chosing", "Thoghts",
    "Enginers", "Toch", "Alof", "Otcomes", "Fotsteps", "Felings", "Feling",
    "Seds",
    # chapter/TOC/meta/TL credits
    "Cast", "Copyrights", "Monkey", "Offensive's", "Offensive", "Twitter",
    "Novels", "Daedalus", "Illustrations", "Translator", "Bombdam", "Diet",
    "Gatling", "Reaper", "Daifugo", "Devil", "Raymond", "Chandler", "Queen",
    "Ellery", "Sagittarius", "Francis", "Illustrator", "Kinusaga", "Haneda",
    "Tower", "Mont", "Santa", "Small-", "Drago", "Ganryujima", "Traditional",
    "Olympic", "York", "Re", "Elise", "Minos", "Ball", "Secretaries", "Tzu",
    "Lamb", "Blanc", "Claus", "Bottleman", "Beadaman", "Pacific", "Für",
    "Milgram", "Kokugikan", "Hanshin", "Pokémon", "Vegas", "Christie",
    "Wuthering", "Juyondai", "Muromachi", "Pingyao", "Ariake", "Kinuko",
    "U-lock", "Quiz", "Hesse", "Chancellor", "Kinu", "Cheki", "Darjeeling",
    "Shin", "Boston", "Museum", "Utonai", "Kaminai", "Tigers", "Yasaseru",
    "Paisen", "Colibri", "Yuuichi",
    # outside-world / orgs / places / in-universe media
    "Kazuya",   # Japanese soccer player named in an Y1 anecdote
    "Hana",     # real-world 'RIP Hana Kimura' forum line (y2)
    "Kyoei",    # y0 Kyōei Party (political)
    "Koei",     # ascii-ou variant of Kyōei Party
    "Chitose",  # Shin-Chitose Airport
    "Omuro",    # 'Omuro Ariake' cherry variety
    "Tokubetsushoku",  # Japanese 'special meal' (menu/meal talk, not a name)
    "Oba",      # y0 'Oba clan' (thieves organization) — world/org, not a person-key
    "Tsushi",    # Kaminai Tsushi — in-universe mystery author (Y2V9.5)
    "Jnovels",  # TL site credit
    "Instagram",
    "Dashu",
    "Jane",
    "Hans",
    "Werewolf",
    "Cavalier",
    "Secrets", "Cow", "Grim", "Art", "Hans", "Shogi", "Side", "Third",
    "Lake", "Rice", "Events", "Tug-of-",
    # outside-world media / systems seen in pair-scan false positives
    "Deja",      # 'Deja Vu'
    "Chitanda",  # outside anime name-drop
    "Kuroda",    # Kuroda Kanbei — historical figure mention
    "Zhuge",     # Zhuge Liang — historical figure mention
    "Kodō",      # Kodō Ikusei system (school system name)
    "Ikusei",
    "Rakkan",    # Rakkan Ichiba — shop/place
    "Ichiba",
    "Futsatsu",  # sightseeing-spot name (Y2V12.5)
    "Horoporo",
    # outside-world person-drop / location pairs caught by pass3 gate
    "Isaac",     # Isaac Asimov — author drop (y1v7 translator note)
    "Asimov",
    "Jeet",      # Jeet Kune — martial-arts reference (y0)
    "Kune",
    "Naona",     # Naona Ee — world politician news mention
    "Shiroi",    # Shiroi Koibito — sightseeing/food (y2v8)
    "Koibito",
    # exam/system words still living in this band
    "Starter", "Relay", "Vanguard", "Interval",
]


def slug(canonical):
    s = canonical.lower()
    for a, b in (("ā", "a"), ("ē", "e"), ("ī", "i"), ("ō", "o"), ("ū", "u")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def cid_of(canonical):
    return CID_OVERRIDE.get(canonical, slug(canonical))


def add_alias(db, cid, raw, ftype, note=""):
    key = normalize(raw)
    dup = db.execute(
        "SELECT 1 FROM aliases WHERE char_id=? AND normalized=?",
        (cid, key)).fetchone()
    if dup:
        return
    db.execute(
        "INSERT INTO aliases (char_id, raw_form, normalized, form_type, is_noise) "
        "VALUES (?,?,?,?,0)", (cid, raw, key, ftype))


def claim(db, raw, cid, note):
    key = normalize(raw)
    db.execute(
        "UPDATE roster_candidates SET classification='character', char_id=?, "
        "reviewer_note=? WHERE normalized=? AND "
        "(classification='unreviewed' OR classification='unknown' "
        " OR char_id LIKE 'provisional-%')",
        (cid, note, key))


def ensure_char(db, cid, canonical, tier, status, notes):
    db.execute(
        "INSERT OR IGNORE INTO characters "
        "(char_id, canonical_name, name_order, tier, status, notes) VALUES (?,?,?,?,?,?)",
        (cid, canonical, "family-given" if len(canonical.split()) > 1 else "unknown",
         tier, status, notes))


def merge_albert(db):
    a = db.execute("SELECT 1 FROM characters WHERE char_id='albert'").fetchone()
    b = db.execute("SELECT 1 FROM characters WHERE char_id='yamada-albert'").fetchone()
    if not (a and b):
        return
    for tbl, col in (("roster_candidates", "char_id"), ("quotes", "char_id"),
                     ("event_participants", "char_id"), ("coverage", "char_id"),
                     ("claims", "char_id")):
        try:
            db.execute(f"UPDATE {tbl} SET char_id='yamada-albert' WHERE char_id='albert'")
        except sqlite3.Error:
            pass
    db.execute("DELETE FROM aliases WHERE char_id='albert'")
    db.execute("DELETE FROM characters WHERE char_id='albert'")


def main():
    db = sqlite3.connect(DB)

    # canonical upgrade for the bare seed Tokitou
    db.execute(
        "UPDATE characters SET canonical_name=?, notes=? WHERE char_id='tokitou'",
        ("Tokitou Katsumi",
         "seed bare 'Tokitou' (1-B); given from Y2V4.5 Ichinose-classmate context"),
    )
    # duplicate: KNOWN 'Albert' == seed 'Yamada Albert'
    merge_albert(db)

    # 1. new characters (+ family claim from loop, except FAMILY_SKIP)
    for canonical, (tier, status, note) in NEW_CHARS.items():
        cid = cid_of(canonical)
        exists = db.execute(
            "SELECT 1 FROM characters WHERE char_id=?", (cid,)).fetchone()
        ensure_char(db, cid, canonical, tier, status, note)
        parts = canonical.split()
        if not exists and len(parts) > 1:
            add_alias(db, cid, parts[0], "family")
            add_alias(db, cid, parts[1], "given")
        if len(parts) > 1 and normalize(parts[0]) not in FAMILY_SKIP:
            claim(db, parts[0], cid, f"P1 pass2 new char: {note}")

    # 2. explicit family claims (single-name people, shell upgrades, noted cases)
    for raw, target, note in FAMILY_CLAIMS:
        cid = cid_of(target)
        if not db.execute("SELECT 1 FROM characters WHERE char_id=?", (cid,)).fetchone():
            print(f"WARN: family target missing: {raw} -> {cid}")
            continue
        if normalize(raw) not in FAMILY_SKIP:
            add_alias(db, cid, raw, "family")
            claim(db, raw, cid, f"P1 pass2 family: {note}")
        else:
            # keep an alias for the senator-style duplicate surname only if absent
            add_alias(db, cid, raw, "family")
            # but never re-point the bare candidate

    # 3. given / variant / nickname aliases
    for raw, target, ftype, note in ALIASES:
        cid = cid_of(target)
        if not db.execute("SELECT 1 FROM characters WHERE char_id=?", (cid,)).fetchone():
            print(f"WARN: alias target missing: {raw} -> {cid}")
            continue
        add_alias(db, cid, raw, ftype)
        claim(db, raw, cid, f"P1 pass2 alias ({ftype}): {note}")

    # 4. noise (only still-unreviewed rows)
    for raw in NOISE:
        db.execute(
            "UPDATE roster_candidates SET classification='noise', "
            "reviewer_note=? WHERE normalized=? AND classification='unreviewed'",
            ("P1 pass2 noise: English/meta/TL/place", normalize(raw)),
        )

    # 5. unresolved notes (only still-unreviewed rows)
    for raw, note in UNKNOWN_NOTES.items():
        db.execute(
            "UPDATE roster_candidates SET classification='unknown', "
            "reviewer_note=? WHERE normalized=? AND classification='unreviewed'",
            (f"P1 pass2: {note}", normalize(raw)),
        )

    # 6. shell cleanup: re-point provisional shells now owned by real chars
    shells = [r[0] for r in db.execute(
        "SELECT char_id FROM characters WHERE char_id LIKE 'provisional-%'")]
    repointed = dropped = 0
    for sh in shells:
        key = sh[len("provisional-"):]
        owner = db.execute(
            "SELECT a.char_id FROM aliases a JOIN characters c ON c.char_id=a.char_id "
            "WHERE a.normalized=? AND c.char_id NOT LIKE 'provisional-%' LIMIT 1",
            (key,)).fetchone()
        if owner:
            repointed += db.execute(
                "UPDATE roster_candidates SET char_id=?, "
                "reviewer_note=COALESCE(reviewer_note,'') || ' [shell->real]' "
                "WHERE char_id=? AND classification='character'",
                (owner[0], sh)).rowcount
            db.execute("UPDATE quotes SET char_id=? WHERE char_id=?", (owner[0], sh))
        nrefs = db.execute(
            "SELECT COUNT(*) FROM roster_candidates WHERE char_id=?", (sh,)).fetchone()[0]
        if nrefs == 0:
            db.execute("DELETE FROM aliases WHERE char_id=?", (sh,))
            used = False
            for tbl in ("event_participants", "claims", "coverage", "quotes"):
                try:
                    if db.execute(f"SELECT COUNT(*) FROM {tbl} WHERE char_id=?",
                                  (sh,)).fetchone()[0]:
                        used = True
                except sqlite3.Error:
                    pass
            if not used:
                db.execute("DELETE FROM characters WHERE char_id=?", (sh,))
                dropped += 1

    db.commit()
    stats = dict(db.execute(
        "SELECT classification, COUNT(*) FROM roster_candidates "
        "GROUP BY classification").fetchall())
    chars = db.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    shells_left = db.execute(
        "SELECT COUNT(*) FROM characters WHERE char_id LIKE 'provisional-%'").fetchone()[0]
    orphans = db.execute(
        "SELECT COUNT(*) FROM roster_candidates c "
        "LEFT JOIN characters ch ON ch.char_id=c.char_id "
        "WHERE c.classification='character' AND ch.char_id IS NULL").fetchone()[0]
    db.close()
    print("candidates:", stats)
    print(f"characters: {chars}  shells left: {shells_left}  "
          f"shell cleanup: {repointed} re-pointed, {dropped} dropped  "
          f"orphan candidates: {orphans}")


if __name__ == "__main__":
    main()
