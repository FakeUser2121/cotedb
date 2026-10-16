"""P5b: authored main-character analysis — data + idempotent applier.

python3 kb/main_analysis.py

Hand-authored evidence-linked readings for tier-1 dossiers, applied to
the DB tables status_timeline / interpretations / relations (none are
in the structural digest). Replace-per-char semantics: every apply
wipes that char's rows and re-inserts this file's content, so the file
is the sole authored source. basis/evidence refs are JSON lists;
"y1v4 p.93"-style strings pass through as anchors, "q<id>"/"claim<id>"
resolve to quotes/claims. Builder: kb/build_main_dossiers.py.
"""
import json
import sqlite3

from roster_mine import DB_PATH

ANALYSIS = {
    "ayanokouji-kiyotaka": {
        "status_timeline": [
            {"vol_id": "y1v1",
             "situation": "Enrolled into the school's lowest class; lives "
             "as an invisible loner while Horikita's cold war with Kushida's "
             "social web begins.",
             "knowledge_state": "Reads Class D's point deficit and Kushida's "
             "junior-high history with him long before either surfaces "
             "openly.",
             "changes": "Turns down Manabu Horikita's guidance-office "
             "challenge; accepts a quiet orbit around Horikita (lunch, the "
             "study group as bridge).",
             "why": "Establishes the 'no trouble' mask the rest of the "
             "series punctures.",
             "evidence_refs": ["y1v1 p.99", "y1v1 p.150", "y1v1 p.162"]},
            {"vol_id": "y1v2",
             "situation": "Sudou's assault accusation threatens the class's "
             "first island points.",
             "knowledge_state": "Understands Kushida's hostility toward "
             "Horikita is a personal grudge, not class politics.",
             "changes": "Builds the witness strategy and publicly vouches "
             "for Sakura's testimony — first real cost-taking.",
             "why": "Converts him from observer to reluctant operator while "
             "the humility mask ('don't keep overestimating me') holds.",
             "evidence_refs": ["y1v2 p.112", "y1v2 p.211", "y1v2 p.253"]},
            {"vol_id": "y1v3",
             "situation": "Island survival exam: cave occupation politics "
             "around Katsuragi and Yahiko.",
             "knowledge_state": "Maps Ryuuen's aggression style and the "
             "keycard/coercion game as they happen.",
             "changes": "Settles the cave dispute forensically from what he "
             "saw, without revealing how much he watches.",
             "why": "First full proof that his 'bystander' claim is a pose: "
             "he investigates even when uninvolved.",
             "evidence_refs": ["y1v3 p.251", "y1v4 p.109"]},
            {"vol_id": "y1v4",
             "situation": "Phone-VIP game; Ryuuen's camp targets Karuizawa's "
             "bullying past.",
             "knowledge_state": "Identifies Karuizawa as VIP and reads "
             "Ryuuen's endgame.",
             "changes": "Records Karuizawa's 'baptism' and binds her to him "
             "— the series' most morally contested act.",
             "why": "Creates the Karuizawa instrument while framing it as "
             "fear-management.",
             "evidence_refs": ["y1v4 p.173", "y1v4 p.201", "y1v4 p.232"]},
            {"vol_id": "y1v5",
             "situation": "Sports festival: predicted traitor, Kinoshita "
             "frame-up, Sudou's injury leverage.",
             "knowledge_state": "Forecasts the class leak before it happens "
             "and names the traitor by festival end.",
             "changes": "Substitutes into events, counter-frames Kinoshita, "
             "settles the million-point deal.",
             "why": "Proves the forecasting is operational, while he still "
             "visibly sandbags his own results.",
             "evidence_refs": ["y1v5 p.47", "y1v5 p.141", "y1v5 p.155"]},
            {"vol_id": "y1v6",
             "situation": "Kushida's threats escalate toward an expulsion "
             "gambit.",
             "knowledge_state": "Holds recorded proof of her coercion.",
             "changes": "Confronts her openly, drops the pretend-ignorance, "
             "and wagers on Horikita defeating her.",
             "why": "The mask drops in private: knowing and acting merge.",
             "evidence_refs": ["y1v6 p.124", "y1v6 p.195", "y1v6 p.199"]},
            {"vol_id": "y1v7",
             "situation": "His father Atsuomi appears while Ryuuen closes in "
             "on X's identity.",
             "knowledge_state": "Fights both fronts at full exposure.",
             "changes": "Defines freedom against the White Room, reveals as "
             "X, defeats Ryuuen's crew, spares Ryuuen on stated utility.",
             "why": "Centerpiece volume: self-definition plus the first "
             "stated long-term manipulation of rival classes.",
             "evidence_refs": ["y1v7 p.57", "y1v7 p.64", "y1v7 p.195"]},
            {"vol_id": "y1v8",
             "situation": "Student-council president Nagumo's attention and "
             "expulsion games.",
             "knowledge_state": "Maps Nagumo's cross-grade network.",
             "changes": "Engages the second-year war by proxy; gives "
             "Ichinose a partial, framed admission.",
             "why": "Shifts the threat model from first-years to "
             "institutional power.",
             "evidence_refs": ["y1v8 p.176", "y1v8 p.195", "y1v8 p.212"]},
            {"vol_id": "y2v4",
             "situation": "Tsukishiro's pressure and White Room students "
             "surface inside the school.",
             "knowledge_state": "Confirms the acting-director's hostility.",
             "changes": "Names Tsukishiro's approach to his face — stops "
             "hiding from institutional foes.",
             "why": "He moves from evading his past to containing it inside "
             "the school's rules.",
             "evidence_refs": ["y2v4 p.20", "y2v4 p.252"]},
            {"vol_id": "y2v8",
             "situation": "Yagami's designs press on Sakura and the class "
             "internally.",
             "knowledge_state": "Reads Yagami's pattern through Amasawa's "
             "warnings.",
             "changes": "Declares he is not running away — first explicit "
             "refusal of withdrawal.",
             "why": "Marks concealment turning into standing ground for "
             "classmates.",
             "evidence_refs": ["y2v8 p.61", "y2v8 p.64"]},
            {"vol_id": "y2v12",
             "situation": "Late second year: Karuizawa's position weakens; "
             "Horikita's class unity strains.",
             "knowledge_state": "Anticipates the relationship collapse and "
             "the coming separation.",
             "changes": "Frames secrets as shackles while advising Horikita "
             "to rely on classmates — preparing both to stand without him.",
             "why": "Sets up the third-year independence arc.",
             "evidence_refs": ["y2v12 p.53", "y2v12 p.151"]},
        ],
        "interpretations": [
            {"claim": "The trouble-avoider persona is a White Room survival "
             "reflex he inherited, not his genuine preference",
             "basis_refs": ["y1v5 p.15", "y1v4 p.109", "y1v1 p.150"],
             "confidence": 0.75,
             "notes": "Counter-reading: he repeatedly chooses engagement "
             "when stakes are personal (y1v6 p.124; y2v8 p.64), so the mask "
             "may be inherited but no longer chosen. Both readings fit the "
             "corpus; the text never settles it."},
            {"claim": "His terminal goal is self-determination, not Class A "
             "victory",
             "basis_refs": ["y1v5 p.47", "y1v7 p.59", "y1v7 p.64"],
             "confidence": 0.8,
             "notes": "Competing: he optimizes class outcomes constantly. "
             "Plainest synthesis: Class A is the arena in which "
             "self-determination is proven, not the goal itself."},
            {"claim": "The Karuizawa 'baptism' was necessity-driven "
             "instrumentation, not sadism",
             "basis_refs": ["y1v4 p.201", "y1v7 p.124", "y1v7 p.190"],
             "confidence": 0.6,
             "notes": "Contested: the method's cruelty (y1v4 p.195-199) "
             "supports a colder reading — that he reaches for White Room "
             "techniques because they are the only tools he was given. "
             "Readers split here; surface evidence supports both."},
            {"claim": "Sparing Ryuuen was utility, not mercy or respect",
             "basis_refs": ["y1v7 p.185", "y1v7 p.195"],
             "confidence": 0.65,
             "notes": "Competing: the 'fear experiment' framing (p.185-186) "
             "hints at personal curiosity toward Ryuuen; utility is only "
             "the stated reason."},
            {"claim": "His relationships shift from instruments to "
             "obligations across y1 to y2",
             "basis_refs": ["y1v1 p.73", "y1v2 p.211", "y2v8 p.64",
                            "y2v12 p.151"],
             "confidence": 0.7,
             "notes": "Counter-reading: no scene shows him acting against "
             "interest for a peer without side-benefit; the 'obligations' "
             "may be strategic consistency rather than attachment growth."},
        ],
        "relations": [
            {"char_b": "horikita-suzune", "rel_type": "ally-core",
             "direction_note": "Strategic partner from y1v1, evolving to "
             "first-name intimacy by y2v6 (p.343 'Suzune…right?'). "
             "Co-scene count in the corpus: 93 — his strongest link.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v1 p.99", "y1v2 p.112", "y2v6 p.343"]},
            {"char_b": "kushida-kikyou", "rel_type": "rival-secret",
             "direction_note": "He holds her junior-high history; mutual "
             "blackmail from y1v5-6 converts her social mask into a "
             "managed threat.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v5 p.195", "y1v6 p.199", "y1v6 p.200"]},
            {"char_b": "karuizawa-kei", "rel_type": "ward-to-fracture",
             "direction_note": "Created via the recorded baptism (y1v4), "
             "managed through y1v7-8 protection, separation prepared in "
             "y2v12 ('secrets become shackles').",
             "valid_from_vol": "y1v4", "valid_to_vol": "y2v12",
             "evidence_refs": ["y1v4 p.201", "y1v7 p.190", "y2v12 p.53"]},
            {"char_b": "ryuuen-kakeru", "rel_type": "rival-tolerated",
             "direction_note": "Wariness first (y1v4 p.67 'wary of Ryuuen "
             "by a mile'), X-endgame defeat y1v7, then kept alive as "
             "Class-D's useful enemy against Sakayanagi and Ichinose.",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.67", "y1v7 p.195"]},
            {"char_b": "horikita-manabu", "rel_type": "authority-benchmark",
             "direction_note": "Guidance-office refusal (y1v1 p.150); "
             "Manabu's unannounced observations keep shaping the path "
             "Horikita and he both walk.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v1 p.149", "y1v1 p.150"]},
            {"char_b": "ayanokouji-atsuomi", "rel_type": "family-adversary",
             "direction_note": "White Room father; y1v7 meeting inverts "
             "the contract: orders bind only inside the White Room, and he "
             "claims the right to choose his path.",
             "valid_from_vol": "y1v7", "valid_to_vol": None,
             "evidence_refs": ["y1v7 p.57", "y1v7 p.59", "y1v7 p.64"]},
            {"char_b": "chabashira-sae", "rel_type": "keeper-of-secret",
             "direction_note": "Homeroom channel for his origin; she "
             "presses and conceals in equal measure (handwriting test "
             "y2v7).",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v1 p.140", "y2v7 p.153", "y2v7 p.167"]},
            {"char_b": "sakayanagi-arisu", "rel_type": "rival-a-class",
             "direction_note": "Long-game opponent; he deliberately steers "
             "Ryuuen against her (y1v7 p.195) instead of engaging directly.",
             "valid_from_vol": "y1v7", "valid_to_vol": None,
             "evidence_refs": ["y1v7 p.195", "y2v8 p.168"]},
            {"char_b": "kouenji-rokusuke", "rel_type": "wary-unknown",
             "direction_note": "The one classmate he declines to model: "
             "quantifies everyone else, keeps Kouenji as an unquantified "
             "variable.",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.67", "y1v5 p.95"]},
        ],
    },
    "horikita-suzune": {
        "status_timeline": [
            {"vol_id": "y1v1",
             "situation": "Sorted into Class D against expectations; refuses "
             "the class and everyone in it while privately enraged at the "
             "grading she believes she deserves.",
             "knowledge_state": "Understands the point system's logic "
             "('points are just a byproduct') before anyone around her.",
             "changes": "Relents just enough to tutor Sudou and Ike — "
             "grudging entry into class life; declares she will drag "
             "herself to Class A regardless.",
             "why": "Sets the pride engine and the isolation armor that "
             "later softens under load.",
             "evidence_refs": ["y1v1 p.98", "y1v1 p.155", "y1v1 p.196"]},
            {"vol_id": "y1v2",
             "situation": "Sudou's expulsion threat forces a public stand.",
             "knowledge_state": "Reads that the trial is winnable only with "
             "Sakura's testimony and class coordination.",
             "changes": "Vouches for Sakura publicly and refuses to retreat "
             "('I will keep fighting to support your testimony until the "
             "end').",
             "why": "First proof she will spend her own standing for "
             "others — the isolation armor cracks.",
             "evidence_refs": ["y1v2 p.94", "y1v2 p.210", "y1v2 p.216"]},
            {"vol_id": "y1v3",
             "situation": "Island exam; resource collapse and Ryuuen's "
             "reckless point-burning.",
             "knowledge_state": "Maps the class's structural weakness "
             "('if the person on top is incompetent, those below him will "
             "suffer').",
             "changes": "Takes operational command of search parties and "
             "cooperation with Class A.",
             "why": "Leadership stops being a slogan and becomes practice.",
             "evidence_refs": ["y1v3 p.111", "y1v3 p.116", "y1v3 p.197"]},
            {"vol_id": "y1v4",
             "situation": "VIP phone test; an analytical duel with "
             "Ayanokouji across group strategies.",
             "knowledge_state": "Deduces the VIP selection system and "
             "catches Ryuuen's frame on Karuizawa.",
             "changes": "Outs her dependence openly — 'the closest I have "
             "would be Ayanokouji-kun' — while deflecting with barbs.",
             "why": "The partnership becomes visible even to her.",
             "evidence_refs": ["y1v4 p.65", "y1v4 p.73", "y1v4 p.239"]},
            {"vol_id": "y1v5",
             "situation": "Sports festival: traitor leaks, Kinoshita "
             "frame-up, her injured leg.",
             "knowledge_state": "Forecasts preparation gaps in advance; "
             "diagnoses the frame mid-event.",
             "changes": "Runs on an injured leg ('I'll participate, even if "
             "I have to crawl'), accepts last place without excuse, sets "
             "Sudou's non-violence penance; grants Ayanokouji first-name "
             "rights only on a win.",
             "why": "Defeat becomes her legitimacy: she leads by taking the "
             "loss honestly.",
             "evidence_refs": ["y1v5 p.55", "y1v5 p.115", "y1v5 p.192"]},
            {"vol_id": "y1v6",
             "situation": "Kushida's past arrives in the open; the final "
             "exam is rigged with malicious questions.",
             "knowledge_state": "Full picture of Kushida's junior-high "
             "destruction and her threat network.",
             "changes": "Chooses management over exposure ('This is my "
             "responsibility. I can't just abandon her'), then beats the "
             "question gambit with a pre-submitted counter-plan and "
             "publicly takes blame for the class's failed unity.",
             "why": "Her two defining choices in one volume: mercy as "
             "responsibility, victory as preparation.",
             "evidence_refs": ["y1v6 p.45", "y1v6 p.49", "y1v6 p.184"]},
            {"vol_id": "y1v7.5",
             "situation": "Nagumo's expulsion machine and student-council "
             "politics surface.",
             "knowledge_state": "Tracks Nagumo's cross-year influence and "
             "the one second-year opposing him.",
             "changes": "States her leadership creed outright: a leader "
             "should help the whole body graduate, not win by expulsion.",
             "why": "Her morality is stated as policy, not just instinct.",
             "evidence_refs": ["y1v7.5 p.88", "y1v7.5 p.90"]},
            {"vol_id": "y1v8",
             "situation": "A challenge built on principles she rejects.",
             "knowledge_state": "Sees the opponent's character gap before "
             "the match.",
             "changes": "Refuses the terms and calls the betrayal of "
             "direct competition what it is ('I trusted you... I was "
             "wrong').",
             "why": "Values become a weapon she is willing to wield in "
             "public.",
             "evidence_refs": ["y1v8 p.58", "y1v8 p.60", "y1v8 p.235"]},
            {"vol_id": "y2v5",
             "situation": "Kushida's threat resurfaces at close range.",
             "knowledge_state": "Done diagnosing — she names the "
             "destruction outright.",
             "changes": "Confronts Kushida without cushion: 'you are "
             "fundamentally stupid... you broke the class' — the "
             "responsibility posture hardens into direct confrontation.",
             "why": "The mercy-without-illusions stance reaches its "
             "limit.",
             "evidence_refs": ["y2v5 p.212"]},
            {"vol_id": "y2v9",
             "situation": "Student-council orbit; Nagumo's pressure "
             "campaign.",
             "knowledge_state": "Learns that standing comes from "
             "relationships, not office.",
             "changes": "Swallows pride for the class ('If me "
             "prostrating is beneficial for the class, then it's worth "
             "it') — a mirror of her y1v5 loss-acceptance.",
             "why": "Pride is re-tuned from personal honor to class "
             "utility.",
             "evidence_refs": ["y2v9 p.55", "y2v9 p.56"]},
        ],
        "interpretations": [
            {"claim": "Her brother complex is admiration fused with "
             "unresolved inadequacy, and it fuels both her ceiling and her "
             "blind spots",
             "basis_refs": ["y1v5 p.55", "y1v5 p.61", "y1v5 p.96"],
             "confidence": 0.75,
             "notes": "Counter-reading: the text frames Manabu purely as "
             "benchmark — she wants to equal the standard, not to be seen "
             "by him. The first-name gate (permission tied to beating him "
             "in results) reads competitive admiration either way."},
            {"claim": "Keeping Kushida managed rather than exposed is "
             "principled responsibility, not naivety or calculation",
             "basis_refs": ["y1v6 p.45", "y1v6 p.49", "y2v5 p.212"],
             "confidence": 0.7,
             "notes": "Competing readings: (a) moral — she refuses to "
             "abandon someone whose destruction she witnessed; (b) "
             "instrumental — Kushida's network is too useful to burn. "
             "Her later direct confrontation (y2v5) undercuts pure "
             "calculation but doesn't prove pure mercy either."},
            {"claim": "Her friendships form through usefulness first and "
             "warmth second",
             "basis_refs": ["y1v1 p.98", "y1v6 p.113", "y1v6 p.180"],
             "confidence": 0.65,
             "notes": "Counter-reading: the Sudou-tutoring relenting "
             "(y1v1 p.207) and her rage at being pitied (y1v6 p.50) "
             "predate any utility — attachment is present early, buried "
             "under pride."},
            {"claim": "She believes goodness is performed for reward, "
             "which is why she distrusts Ichinose's generosity",
             "basis_refs": ["y1v6 p.113", "y1v6 p.115", "y1v6 p.116"],
             "confidence": 0.55,
             "notes": "Contested: could equally be strategic caution "
             "dressed as philosophy — she tests Ichinose with a loaded "
             "question, then admits she is 'special' and must be extra "
             "careful. Motive (envy vs. analysis) is not settled by the "
             "corpus."},
            {"claim": "She leads by absorbing blame, not by shadow "
             "control — the deliberate opposite of Ayanokouji's model",
             "basis_refs": ["y1v5 p.192", "y1v6 p.180", "y1v6 p.187"],
             "confidence": 0.8,
             "notes": "Competing: her pre-submitted exam counter-plan "
             "(y1v6 p.184) is pure concealed preparation — Ayanokouji's "
             "method. So the difference is emphasis, not kind: she "
             "prepares in shadows, but claims failure in public."},
        ],
        "relations": [
            {"char_b": "ayanokouji-kiyotaka", "rel_type": "ally-core",
             "direction_note": "From grudging dependence (y1v4 'the "
             "closest I have would be Ayanokouji-kun') to first-name "
             "permission (y1v5 p.55) to a partnership others comment on "
             "(y2v6 p.211). Co-scene count: 93 — her strongest link.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.73", "y1v5 p.55", "y2v6 p.211"]},
            {"char_b": "horikita-manabu", "rel_type": "family-benchmark",
             "direction_note": "Her stated engine: 'my brother is perfect "
             "— always number one' (y1v5 p.96); she measures every step "
             "against his standard while resenting her own distance from "
             "it.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v1 p.144", "y1v5 p.61", "y1v5 p.96"]},
            {"char_b": "kushida-kikyou", "rel_type": "rival-managed",
             "direction_note": "Junior-high destruction known from y1v6; "
             "kept as a managed threat ('my responsibility') until direct "
             "confrontation in y2v5.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v6 p.45", "y1v6 p.49", "y2v5 p.212"]},
            {"char_b": "sudou-ken", "rel_type": "charge-ward",
             "direction_note": "First reclamation project: reluctant "
             "tutoring → saved at trial → non-violence penance as "
             "condition of growth.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v1 p.207", "y1v2 p.210", "y1v5 p.191"]},
            {"char_b": "hirata-yousuke", "rel_type": "co-leader",
             "direction_note": "Parallel leadership tracks: he holds the "
             "class's heart, she holds its strategy; study-group "
             "infrastructure runs through both.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v1 p.155", "y1v6 p.40"]},
            {"char_b": "ichinose-honami", "rel_type": "rival-respectful",
             "direction_note": "Tested generosity (y1v6 p.113-115): "
             "acknowledged as the kindest person she's met, and the most "
             "dangerous unknown.",
             "valid_from_vol": "y1v6", "valid_to_vol": None,
             "evidence_refs": ["y1v6 p.113", "y1v6 p.115", "y1v6 p.116"]},
            {"char_b": "ryuuen-kakeru", "rel_type": "rival-hostile",
             "direction_note": "Open contempt plus realistic fear: "
             "'Both you and Ryuuen-kun are lunatics'; keeps classmates "
             "out of his reach by decree (y1v7 p.118).",
             "valid_from_vol": "y1v3", "valid_to_vol": None,
             "evidence_refs": ["y1v3 p.116", "y1v7 p.115", "y1v7 p.118"]},
            {"char_b": "nagumo-miyabi", "rel_type": "rival-authority",
             "direction_note": "Philosophical opposition first "
             "(y1v7.5 p.88: leaders should graduate everyone), "
             "practical entanglement through the student council in y2v9.",
             "valid_from_vol": "y1v7.5", "valid_to_vol": None,
             "evidence_refs": ["y1v7.5 p.88", "y2v9 p.55", "y2v9 p.56"]},
        ],
    },
    "kushida-kikyou": {
        "status_timeline": [
            {"vol_id": "y1v1",
             "situation": "School's most social girl systematically "
             "befriends everyone while engineering Horikita's isolation.",
             "knowledge_state": "Already knows Ayanokouji from junior high "
             "and is probing how much Horikita remembers.",
             "changes": "Recruits Ayanokouji as a Horikita-convergence "
             "tool; drops the first genuine mask slip in private ('I "
             "really hate you').",
             "why": "Establishes the two-layer voice the whole series "
             "runs on: the public warmth, the private war.",
             "evidence_refs": ["y1v1 p.35", "y1v1 p.91", "y1v1 p.238"]},
            {"vol_id": "y1v2",
             "situation": "Sudou trial: she plays the tireless class "
             "organizer.",
             "knowledge_state": "Running reconnaissance on who knows what "
             "about Sakura and the witness chain.",
             "changes": "Deepens the helper persona — networks Class B, "
             "manages Sudou's image — while quietly mapping everyone's "
             "positions.",
             "why": "Peak visible usefulness: the mask earns her the "
             "class's trust she intends to weaponize.",
             "evidence_refs": ["y1v2 p.31", "y1v2 p.36", "y1v2 p.163"]},
            {"vol_id": "y1v5",
             "situation": "Sports festival leak traced back toward her; "
             "Ayanokouji forces the private confrontation.",
             "knowledge_state": "Exposed enough to pivot: she shows her "
             "hand deliberately.",
             "changes": "Declares the expulsion campaign against Horikita "
             "— and then against Ayanokouji too; admits the Ryuuen "
             "question-swap deal was her own gamble.",
             "why": "The mask comes off as a choice, not an accident: "
             "'I will have the school expel you... deal with the devil'.",
             "evidence_refs": ["y1v5 p.174", "y1v5 p.175", "y1v5 p.196"]},
            {"vol_id": "y1v6",
             "situation": "Final-exam question sabotage exposed; the bet "
             "with Horikita settles.",
             "knowledge_state": "Her junior-high destruction and her "
             "addiction to being valued are now spoken aloud to both "
             "witnesses.",
             "changes": "Confesses the mechanism ('This is what I am'), "
             "loses the blazer-swap trap, and accepts a non-aggression "
             "pact she refuses to turn into cooperation.",
             "why": "The confession reframes her from schemer to addict: "
             "visibility is the drug, sabotage the supply.",
             "evidence_refs": ["y1v6 p.125", "y1v6 p.197", "y1v6 p.199"]},
            {"vol_id": "y1v8",
             "situation": "Threat maintenance while Horikita's position "
             "hardens.",
             "knowledge_state": "Still believes exposure equals "
             "destruction — of the class as well as herself.",
             "changes": "Restates the doctrine in plain terms: leak "
             "anything and she will 'destroy the entire class, just like "
             "I did back in junior high'.",
             "why": "Mutually assured destruction becomes her governing "
             "policy.",
             "evidence_refs": ["y1v8 p.214", "y1v8 p.215"]},
            {"vol_id": "y1v9",
             "situation": "Pact period: an uneasy working channel opens.",
             "knowledge_state": "Accepts the frame where she neither "
             "antagonizes Ayanokouji nor gets full trust.",
             "changes": "Joins the agreement with a single strict "
             "condition — don't make her his enemy — and keeps feeding "
             "useful information.",
             "why": "Managed coexistence begins; hostility goes "
             "underground but never ends.",
             "evidence_refs": ["y1v9 p.195", "y1v9 p.197", "y1v9 p.200"]},
            {"vol_id": "y2v5",
             "situation": "Horikita's direct confrontation re-opens the "
             "old wound in public.",
             "knowledge_state": "Cornered by the recording/proof line of "
             "attack.",
             "changes": "Snaps ('That's enough!!!') — the composed mask "
             "failing under sustained pressure for the first time since "
             "y1v6.",
             "why": "Shows the pact did not heal anything; it only "
             "stabilized the war.",
             "evidence_refs": ["y2v5 p.199", "y2v5 p.201"]},
            {"vol_id": "y2v7",
             "situation": "Maid-café arc: she admits the relationship with "
             "Horikita in one honest half-sentence.",
             "knowledge_state": "Still embedded in Class D's social "
             "fabric, now with visible ambivalence.",
             "changes": "'Half glad we were classmates and half pissed "
             "off' — resentment and attachment finally co-exist in the "
             "same breath.",
             "why": "The series' clearest statement that her war with "
             "Horikita is personal, not purely instrumental.",
             "evidence_refs": ["y2v7 p.158"]},
        ],
        "interpretations": [
            {"claim": "Her need to be valued is an addiction that "
             "explains both the sunshine persona and the sabotage",
             "basis_refs": ["y1v1 p.185", "y1v6 p.125", "y1v6 p.126"],
             "confidence": 0.85,
             "notes": "The text states it outright ('I think that I'm "
             "probably addicted to that feeling'). Competing nuance: "
             "whether the addiction or the trauma came first — junior-"
             "high destruction is implied as the wound, the addiction as "
             "the scar tissue."},
            {"claim": "She would genuinely burn the class to protect her "
             "secret — the threat is not a bluff",
             "basis_refs": ["y1v5 p.196", "y1v8 p.214"],
             "confidence": 0.75,
             "notes": "Counter-reading: she already had leverage and "
             "chose containment (the y1v9 pact) over destruction; the "
             "threats may be calibrated deterrence rather than standing "
             "intent. Her y1v6 confession to three witnesses weakens the "
             "pure-burn reading."},
            {"claim": "The Horikita obsession is personal (witnessed "
             "popularity vs. outsider) rather than strategic",
             "basis_refs": ["y1v5 p.174", "y1v6 p.197", "y2v7 p.158"],
             "confidence": 0.7,
             "notes": "Competing: Horikita is also the one person whose "
             "knowledge threatens her — hate and threat are "
             "inseparable. The corpus supports motive entanglement, not "
             "a clean single cause."},
            {"claim": "Her later 'I always care about others' posture is "
             "sincere re-integration, not another mask",
             "basis_refs": ["y2v7 p.158", "y3v1 p.25"],
             "confidence": 0.5,
             "notes": "Contested: y3v1 ('Ayanokouji-kun is much more "
             "important than you two think') reads protective, yet she "
             "has every reason to keep him close as a watched variable. "
             "Corpus does not settle whether the thaw is real."},
            {"claim": "She is the series' clearest case of popularity as "
             "a pathology, not a gift",
             "basis_refs": ["y1v6 p.126", "y1v1 p.185", "y1v1 p.101"],
             "confidence": 0.8,
             "notes": "No serious competing reading of the mechanism; "
             "only of culpability — addiction mitigates, the sabotage "
             "actions indict."},
        ],
        "relations": [
            {"char_b": "horikita-suzune", "rel_type": "rival-obsession",
             "direction_note": "Junior-high witness of her class-"
             "destruction standing at eye level; expulsion campaign "
             "(y1v5) mutates into pact (y1v9) into entangled hate-"
             "attachment (y2v7 'half glad, half pissed').",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v5 p.174", "y1v6 p.199", "y2v7 p.158"]},
            {"char_b": "ayanokouji-kiyotaka", "rel_type": "keeper-watched",
             "direction_note": "The only one who saw the threat and the "
             "confession both; she keeps him at pact distance — never "
             "cooperative, never quite free of him.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v1 p.238", "y1v5 p.175", "y1v9 p.197"]},
            {"char_b": "ryuuen-kakeru", "rel_type": "tool-transactional",
             "direction_note": "Question-swap deal (y1v5) made and "
             "betrayed in the same arc; she gambles on his betrayal "
             "openly and loses.",
             "valid_from_vol": "y1v5", "valid_to_vol": None,
             "evidence_refs": ["y1v5 p.175", "y1v6 p.202"]},
            {"char_b": "ike-kanji", "rel_type": "social-circle",
             "direction_note": "Core of the wide net she uses to feel "
             "alive — the everyday proof of her 'everyone likes me' "
             "requirement.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v1 p.35", "y1v1 p.113"]},
            {"char_b": "ichinose-honami", "rel_type": "envy-model",
             "direction_note": "Ichinose's genuinely loved class is "
             "everything Kushida's is not: organic affection instead of "
             "manufactured demand.",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.215", "y1v6 p.118"]},
            {"char_b": "chabashira-sae", "rel_type": "authority-loose",
             "direction_note": "Uses teacher channels for class-covering "
             "moves; never the recipient of a confidence.",
             "valid_from_vol": "y1v2", "valid_to_vol": None,
             "evidence_refs": ["y1v2 p.31"]},
        ],
    },
    "ryuuen-kakeru": {
        "status_timeline": [
            {"vol_id": "y1v3",
             "situation": "Debut as Class C's self-declared tyrant, "
             "summoning Horikita to his territory.",
             "knowledge_state": "Already tracking which Class D student "
             "moves behind the scenes.",
             "changes": "Opens the hunt for the 'puppet master' — treats "
             "the whole year as a game board with everyone as a target.",
             "why": "Establishes his mode: predation as entertainment.",
             "evidence_refs": ["y1v3 p.241", "y1v3 p.108"]},
            {"vol_id": "y1v4",
             "situation": "Island and VIP tests just ended; he debriefs "
             "Horikita one-on-one.",
             "knowledge_state": "Reads Kushida's identity from body "
             "language alone; knows Class D had outside help.",
             "changes": "Admits shock ('The results of the test shocked "
             "me'), pitches a class-A-crushing alliance, and declares "
             "everyone in Horikita's orbit a target.",
             "why": "First evidence he respects outcomes over ego — and "
             "first exposure of his lie-reading.",
             "evidence_refs": ["y1v4 p.74", "y1v4 p.239", "y1v4 p.240"]},
            {"vol_id": "y1v5",
             "situation": "Sports festival: Kushida leaked Class D's "
             "participation table; Kinoshita 'accident' escalates.",
             "knowledge_state": "Holds the leak, the match rigging, and "
             "the extortion leverage.",
             "changes": "Demands Horikita kneel or pay a million points; "
             "'I wanted to crush you. That was reason enough.'",
             "why": "Peak confidence — and the moment the anonymous "
             "recording first cuts him off.",
             "evidence_refs": ["y1v5 p.155", "y1v5 p.198", "y1v5 p.199"]},
            {"vol_id": "y1v6",
             "situation": "Final exams: he runs the phone-check inquisition "
             "to find the traitor.",
             "knowledge_state": "The X recording proves someone inside "
             "his class feeds Horikita protection.",
             "changes": "Frames and breaks Kushida with planted evidence "
             "('Evidence trumps theory'), escalates to all-out war on "
             "Class D.",
             "why": "His surveillance style is rule-bound empiricism, "
             "not random cruelty — the method that later fails against X.",
             "evidence_refs": ["y1v6 p.63", "y1v6 p.67", "y1v6 p.202"]},
            {"vol_id": "y1v7",
             "situation": "School ship: he corners Karuizawa to unmask X; "
             "Ayanokouji walks in and reveals himself.",
             "knowledge_state": "Learns X's identity the hardest possible "
             "way — and that Ayanokouji's power was never in doubt.",
             "changes": "Beaten in his own stronghold; accepts "
             "responsibility ('I take responsibility for everything') "
             "and the expulsion that follows without appealing.",
             "why": "The fall is the hinge of his whole series arc.",
             "evidence_refs": ["y1v7 p.171", "y1v7 p.183", "y1v7 p.193"]},
            {"vol_id": "y1v7.5",
             "situation": "Expelled, rebuilding from outside the school's "
             "walls.",
             "knowledge_state": "Still wired in: Kushida contacts him, he "
             "tracks the Nagumo situation.",
             "changes": "'Save it. I've always been alone' — the "
             "lone-wolf self-image stated plainly while he re-plans "
             "the board.",
             "why": "Post-fall he trades terror for leverage: same "
             "appetite, no institutional power behind it.",
             "evidence_refs": ["y1v7.5 p.79", "y1v7.5 p.89"]},
            {"vol_id": "y2v6",
             "situation": "Returned and negotiating an alliance contract "
             "with Ayanokouji against Sakayanagi.",
             "knowledge_state": "Accepts that the old hierarchy inverted: "
             "the man who beat him now sets terms.",
             "changes": "'You're the man who beat me and shut me up' "
             "(y2v2) hardens into a signed contract; he agrees to hold "
             "Sakayanagi as his side's contribution.",
             "why": "Respect earned through defeat — the first relation "
             "in the series he submits to voluntarily.",
             "evidence_refs": ["y2v2 p.305", "y2v6 p.208", "y2v6 p.216"]},
            {"vol_id": "y2v12",
             "situation": "End-of-year exam concludes his long revenge "
             "line against Sakayanagi.",
             "knowledge_state": "He has ground the distance down for a "
             "full year.",
             "changes": "'...I've finally closed the gap' — the post-"
             "expulsion rebuild declared complete.",
             "why": "Fall (y1v7) → gap-closed (y2v12) is the cleanest "
             "two-point arc any main character gets.",
             "evidence_refs": ["y2v12 p.196", "y2v12 p.42"]},
            {"vol_id": "y3v1",
             "situation": "Now a working senior figure in the class "
             "game — listened to, critiqued, recruiting.",
             "knowledge_state": "Fully integrated into cooperative play "
             "he once only raided.",
             "changes": "'I'll listen. Why do you think that?' — the "
             "tyrant asks for reasoning; peers evaluate his leadership.",
             "why": "Authority replaced the terror he used to rule with.",
             "evidence_refs": ["y3v1 p.140", "y3v1 p.191"]},
        ],
        "interpretations": [
            {"claim": "He governs by appetite — fun is the sovereign "
             "value, points only instrumental",
             "basis_refs": ["y1v7 p.176", "y2v12 p.42", "y1v4 p.74"],
             "confidence": 0.8,
             "notes": "Competing reading: the 'fun' is partly persona — "
             "y1v6's rule-bound inquisition and y2v6's contract "
             "discipline show a calculating operator wearing amusement "
             "as armour. The text keeps both live."},
            {"claim": "His violence is procedural, not chaotic: every "
             "campaign has rules, evidence, and a stated price",
             "basis_refs": ["y1v6 p.64", "y1v6 p.67", "y1v5 p.155"],
             "confidence": 0.85,
             "notes": "Directly competes with the 'sadist brute' surface "
             "reading: he confiscates phones by protocol, offers "
             "kneel-or-points choices, and reasons from evidence "
             "('Evidence trumps theory')."},
            {"claim": "The y1v7 defeat made him better — humility he "
             "never had came through losing",
             "basis_refs": ["y1v7 p.193", "y2v2 p.305", "y2v12 p.196"],
             "confidence": 0.75,
             "notes": "Counter: he was already outcome-respectful before "
             "the fall (y1v4 'shocked me'); the beatdown supplied the "
             "personal motivation, not the trait. Both readings fit the "
             "corpus."},
            {"claim": "He and Ayanokouji share methods but not minds — "
             "the series' explicit mirror pair",
             "basis_refs": ["y1v7.5 p.81", "y1v7 p.183"],
             "confidence": 0.8,
             "notes": "Ryuuen states it himself: 'similar methods, but "
             "fundamentally different thought processes.' His engine is "
             "amusement; Ayanokouji's is ends. Competing nuance: after "
             "the contract (y2v6) the distinction blurs into "
             "instrumental partnership."},
            {"claim": "Post-expulsion, ruling by terror became "
             "impossible, so he rebuilt on pure leverage",
             "basis_refs": ["y1v7.5 p.89", "y1v8 p.208", "y2v6 p.211"],
             "confidence": 0.7,
             "notes": "Supported by the mercenary pricing ('make it a "
             "million') and contract diplomacy replacing school-"
             "sanctioned hierarchy. Competing: he keeps the terror as "
             "brand — Ishizaki and Ibuki still fear him."},
        ],
        "relations": [
            {"char_b": "ayanokouji-kiyotaka",
             "rel_type": "defeated-respect",
             "direction_note": "The beatdown (y1v7) inverted their "
             "order: Ryuuen now calls him 'the man who beat me and shut "
             "me up' and signs contracts on his terms (y2v6).",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v7 p.183", "y2v2 p.305", "y2v6 p.216"]},
            {"char_b": "horikita-suzune", "rel_type": "crush-campaign",
             "direction_note": "His first-year war target ('I wanted to "
             "crush you'); by y2v6 irritated but cooperating — the "
             "hostility cools into transactional respect.",
             "valid_from_vol": "y1v3", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.75", "y1v5 p.198", "y2v6 p.211"]},
            {"char_b": "kushida-kikyou", "rel_type": "asset-secretive",
             "direction_note": "She leaked for him (y1v5), he framed "
             "and burned her when caught (y1v6), yet still takes her "
             "calls (y1v7.5) and asks Ayanokouji to keep her secret "
             "(y2v8) — useful, never trusted.",
             "valid_from_vol": "y1v5", "valid_to_vol": None,
             "evidence_refs": ["y1v5 p.198", "y1v6 p.202", "y2v8 p.148"]},
            {"char_b": "karuizawa-kei", "rel_type": "leverage-target",
             "direction_note": "Cornered on the ship as the pressure "
             "point to unmask X; she endures it, he loses anyway.",
             "valid_from_vol": "y1v7", "valid_to_vol": None,
             "evidence_refs": ["y1v7 p.146", "y1v7 p.175"]},
            {"char_b": "ichinose-honami", "rel_type": "declared-prey",
             "direction_note": "'Starting next semester, I'll take a "
             "bite out of Ichinose' — the next campaign announced at "
             "his lowest moment.",
             "valid_from_vol": "y1v7", "valid_to_vol": None,
             "evidence_refs": ["y1v7 p.177"]},
            {"char_b": "sakayanagi-arisu", "rel_type": "arch-rival",
             "direction_note": "Warned her even while losing (y1v7); "
             "the y2v11 recruitment condition and y2v12 exam close the "
             "grudge line he called 'finally closed the gap'.",
             "valid_from_vol": "y1v7", "valid_to_vol": None,
             "evidence_refs": ["y1v7 p.117", "y2v11 p.203", "y2v12 p.196"]},
            {"char_b": "katsuragi-kouhei", "rel_type": "uneasy-partner",
             "direction_note": "Island-era counterpart (y1v4) and "
             "later idea-source ('willing to listen if you have a "
             "brilliant idea, Katsuragi') — respect without warmth.",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.72", "y2v9.5 p.132"]},
            {"char_b": "ibuki-mio", "rel_type": "enforcer-control",
             "direction_note": "His blunt instrument — openly told her "
             "'my control over you isn't strong enough' when she "
             "pushed back; the whip-side of his rule.",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v6 p.63", "y1v7 p.167"]},
        ],
    },
    "ichinose-honami": {
        "status_timeline": [
            {"vol_id": "y1v2",
             "situation": "Early friendship arc: she mishandles a "
             "classmate's crush and owns it immediately.",
             "knowledge_state": "Still just the popular, warm Class B "
             "girl — no strategic mask yet visible.",
             "changes": "'I didn't respect Chihiro-chan's feelings. I "
             "just wanted to avoid hurting her... That was my mistake' — "
             "honesty as first instinct, stated as policy before any "
             "exam pressure exists.",
             "why": "Establishes the baseline the later deceptions are "
             "measured against.",
             "evidence_refs": ["y1v2 p.127", "y1v2 p.152"]},
            {"vol_id": "y1v4",
             "situation": "Cruise VIP exam: she chairs the mixed-class "
             "group, runs trust-building card games, and weighs an "
             "alliance with Ryuuen.",
             "knowledge_state": "Understands the test's math better than "
             "most; privately declares her real endgame.",
             "changes": "Refuses Ryuuen outright ('you've hurt people in "
             "Class B... I can't ally with you'), and tells Ayanokouji "
             "'I want to graduate from Class A. I have a dream I want "
             "to make real.'",
             "why": "First proof her sweetness is paired with operational "
             "sharpness — she reads faction play (Morishige) and "
             "phone-swap fraud unprompted.",
             "evidence_refs": ["y1v4 p.149", "y1v4 p.215", "y1v4 p.233"]},
            {"vol_id": "y1v6",
             "situation": "Ryuuen circulates a forged letter accusing "
             "her of fraud.",
             "knowledge_state": "The accusation is false but designed to "
             "detonate her trust-based class.",
             "changes": "Meets it with calm refusal to be dragged down — "
             "'I'll report to the teachers tomorrow and prove that this "
             "is just a misunderstanding.'",
             "why": "Her anti-crisis style: transparency instead of "
             "counter-intrigue.",
             "evidence_refs": ["y1v6 p.171", "y1v6 p.174"]},
            {"vol_id": "y1v11.5",
             "situation": "Class B's points collapse under her "
             "leadership; rain, confession of exhaustion to Ayanokouji.",
             "knowledge_state": "Blames herself alone for the arithmetic "
             "of the loss.",
             "changes": "'The only miscalculation was me as the leader. "
             "If I took better action, Class B would definitely have more "
             "points than now' — plus 'I'm always showing you my weak "
             "sides… I'm so lame.'",
             "why": "The low point of the first-year arc: guilt, not "
             "ambition, is her failure mode.",
             "evidence_refs": ["y1v11.5 p.223", "y1v11.5 p.230"]},
            {"vol_id": "y2v4",
             "situation": "Her feelings for Ayanokouji surface in "
             "speech.",
             "knowledge_state": "She knows what saying it costs.",
             "changes": "The bare confession — '…..I like… you…' — turns "
             "the admired strategist into a person with a declared "
             "want.",
             "why": "Sets up the renunciation that follows; she never "
             "uses the feelings as leverage.",
             "evidence_refs": ["y2v4 p.200"]},
            {"vol_id": "y2v9",
             "situation": "Private meetings with Ayanokouji end under "
             "the pressure of her class's standing.",
             "knowledge_state": "She chooses clarity over comfort.",
             "changes": "'We won't see each other in private anymore… "
             "Because it would hurt my heart… I couldn't remain in the "
             "dark. I had to change from the ground up.'",
             "why": "The break is self-imposed discipline — feelings "
             "acknowledged, then fenced.",
             "evidence_refs": ["y2v9 p.174", "y2v9 p.175"]},
            {"vol_id": "y2v12.5",
             "situation": "Aftermath: her unwitting help got Maezono "
             "expelled; class doctrine is being restated.",
             "knowledge_state": "Guilt over the expulsion collides with "
             "the class's no-expulsion ideal.",
             "changes": "Owns it ('greatly and intensely disturbed'), "
             "then declares openly: 'I certainly respect him. But more "
             "than that, I like Ayanokouji-kun' — and defends the ideal "
             "('We have fought so far without expelling a single "
             "person… sometimes, these idealisms do bear fruit').",
             "why": "The mature synthesis: feelings stated without "
             "leverage, idealism restated with its price acknowledged.",
             "evidence_refs": ["y2v12.5 p.15", "y2v12.5 p.187", "y2v12.5 p.189"]},
            {"vol_id": "y3v1",
             "situation": "Now trading trust as equals with "
             "Ayanokouji's camp.",
             "knowledge_state": "Steady while admitting pressure.",
             "changes": "'Just like Ayanokouji-kun trusts me, I trust "
             "him too' — verbal promises, no contract; 'I'm just barely "
             "holding up against the pressure' said without pretending "
             "otherwise.",
             "why": "Closes the loop opened in y1v2: honesty scaled to "
             "the weight of year 3.",
             "evidence_refs": ["y3v1 p.60", "y3v1 p.165"]},
        ],
        "interpretations": [
            {"claim": "Her kindness is a governing strategy, not "
             "naivety — transparency is how she wins",
             "basis_refs": ["y1v4 p.151", "y2v4.5 p.151", "y1v11 p.327"],
             "confidence": 0.8,
             "notes": "She openly states class-first motives ('Everything "
             "I do is for the sake of Class B') and runs open-book point "
             "funds. Competing reading: y1v4 p.149 suggests she still "
             "plays some performance — even she says 'he saw through "
             "me' — so the strategy is layered, not pure."},
            {"claim": "The no-expulsion ideal is a real, priced "
             "constraint on her class, not a slogan",
             "basis_refs": ["y2v12.5 p.189", "y2v12.5 p.15"],
             "confidence": 0.75,
             "notes": "The corpus shows the price directly: lost class "
             "points and the Maezono guilt. Competing: her own self-"
             "blame (y1v11.5) implies she sometimes reads the ideal as "
             "her personal failing rather than a chosen trade-off."},
            {"claim": "Her bond with Ayanokouji moves confession → "
             "self-imposed renunciation → equal trust, never leverage",
             "basis_refs": ["y2v4 p.200", "y2v9 p.174", "y3v1 p.60"],
             "confidence": 0.8,
             "notes": "Distinct from every other romance line in the "
             "corpus: she ends the private contact herself. Competing: "
             "y2v12.5 p.172 ('engrave my existence into your heart') "
             "reads possessive on the surface — the dossier treats it "
             "as declared intent with restraint as track record."},
            {"claim": "Guilt and self-blame are her failure mode — "
             "she collapses inward, never outward into blame of others",
             "basis_refs": ["y1v11.5 p.230", "y2v12.5 p.15", "y1v2 p.127"],
             "confidence": 0.85,
             "notes": "Three separate crises, identical reaction shape. "
             "No serious competing reading in the corpus."},
            {"claim": "Her cheerful persona is the genuine baseline, "
             "not a Kushida-style mask",
             "basis_refs": ["y1v6 p.115", "y3v1 p.165", "y1v2 p.127"],
             "confidence": 0.7,
             "notes": "She shows weakness to others unprompted and "
             "admits limits ('I'm really not so wonderful') — the "
             "inverse of concealment. Competing: her strategic depths "
             "(y1v4 SIM-swap analysis) show the light voice carries "
             "heavy equipment; two layers exist, but only one is "
             "hidden."},
        ],
        "relations": [
            {"char_b": "ayanokouji-kiyotaka",
             "rel_type": "confidant-then-trust",
             "direction_note": "Told him her Class-A dream (y1v4), "
             "confessed (y2v4), cut private contact herself (y2v9), "
             "and rebuilt it as declared mutual trust (y3v1).",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.215", "y2v4 p.200", "y3v1 p.60"]},
            {"char_b": "ryuuen-kakeru", "rel_type": "principled-refusal",
             "direction_note": "Refused his alliance over Class B harm "
             "(y1v4) and met his forged fraud letter with calm "
             "counter-proof (y1v6) — the moral line he never crosses, "
             "she never abandons.",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.149", "y1v6 p.171"]},
            {"char_b": "horikita-suzune", "rel_type": "respectful-peer",
             "direction_note": "Card-table ally of the VIP exam; later "
             "class-leader to class-leader — closeness grew by "
             "observation, not scheming.",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.146", "y2v12 p.133"]},
            {"char_b": "karuizawa-kei", "rel_type": "supportive-ally",
             "direction_note": "Offered open support ('I want to "
             "support you and Karuizawa-san') — bridge figure across "
             "classes without strings.",
             "valid_from_vol": "y2v9.5", "valid_to_vol": None,
             "evidence_refs": ["y2v9.5 p.38"]},
            {"char_b": "kanzaki-ryuuji", "rel_type": "class-b-friction",
             "direction_note": "Class B's ideological splitter: she "
             "notes his lack of assertiveness while he pushes harder "
             "line than her trust-first doctrine allows.",
             "valid_from_vol": "y1v4.5", "valid_to_vol": None,
             "evidence_refs": ["y1v4.5 p.219", "y1v11.5 p.197"]},
            {"char_b": "kushida-kikyou", "rel_type": "warm-peripheral",
             "direction_note": "Honorami-chan social ease — Kushida is "
             "one of the few across classes who uses her first name; "
             "no entanglement with the double life.",
             "valid_from_vol": "y1v4.5", "valid_to_vol": None,
             "evidence_refs": ["y1v4.5 p.218", "y1v6 p.118"]},
        ],
    },
    "sakayanagi-arisu": {
        "status_timeline": [
            {"vol_id": "y0",
             "situation": "Childhood: touring an institution beside her "
             "father, the future chairman.",
             "knowledge_state": "Already fluent in adult doctrine — she "
             "argues policy in a child's voice.",
             "changes": "'Hundreds of children are abandoned every year… "
             "we should welcome' political action; 'this is also a form "
             "of education' — selection as a moral good, stated before "
             "she can vote.",
             "why": "The root text of everything she later becomes at "
             "school.",
             "evidence_refs": ["y0 p.38", "y0 p.87", "y0 p.145"]},
            {"vol_id": "y1v5",
             "situation": "First direct exchange with Ayanokouji in "
             "their shared history.",
             "knowledge_state": "She already knows the word 'White "
             "Room'.",
             "changes": "Names it aloud where no one else would — "
             "establishing that their game began before the school year.",
             "why": "Opens the only rivalry in the series built on prior "
             "knowledge of each other's origins.",
             "evidence_refs": ["y1v5 p.202", "y1v5 p.203"]},
            {"vol_id": "y1v7",
             "situation": "Ayanokouji Sr. attends the party; the school's "
             "admissions machinery is discussed openly.",
             "knowledge_state": "Handles the White Room architect with "
             "policy deflection, and knows Class D's island strategy "
             "through Masumi and Hashimoto.",
             "changes": "Meets Sr.'s pressure ('You intend to make him "
             "withdraw') with school doctrine — 'we only admit students "
             "we believe deserve placement' — while teasing Ryuuen "
             "aside.",
             "why": "She treats the series' darkest adult as a "
             "counterparty to be managed, not feared.",
             "evidence_refs": ["y1v7 p.66", "y1v7 p.69", "y1v7 p.115"]},
            {"vol_id": "y1v7.5",
             "situation": "Chess-phase probing of Ayanokouji, plus "
             "target-selection of Ichinose.",
             "knowledge_state": "Runs a cold reading of Ichinose's "
             "hidden side and diagnoses Masumi's secret as the same "
             "shape as Kamuro's.",
             "changes": "'You think the White Room made you "
             "remarkable, don't you?' — she argues with him as an equal "
             "on his own origin; 'I like messing around with Class B to "
             "stave off boredom.'",
             "why": "Peak of the observer-era: everything is analysis "
             "and play.",
             "evidence_refs": ["y1v7.5 p.39", "y1v7.5 p.42", "y1v7.5 p.37"]},
            {"vol_id": "y1v9",
             "situation": "Kamuro Masumi's secret — shoplifting — sits "
             "in Sakayanagi's keeping.",
             "knowledge_state": "Holds the blackmail and the rumour "
             "war's levers at once.",
             "changes": "'You were shoplifting, were you not?' — the "
             "quietest display of power in the year: one line, total "
             "control.",
             "why": "Defines her method: secrets acquired, then spent "
             "at leisure.",
             "evidence_refs": ["y1v9 p.91", "y1v9 p.171"]},
            {"vol_id": "y1v11",
             "situation": "The first real face-off with Ayanokouji "
             "arrives.",
             "knowledge_state": "She has wanted exactly this.",
             "changes": "'I was simply looking forward to facing off "
             "against you. And now, that wish has come true. I'm "
             "satisfied.'",
             "why": "Rivalry declared as satisfaction, not grievance.",
             "evidence_refs": ["y1v11 p.433"]},
            {"vol_id": "y1v11.5",
             "situation": "Post-exam: she reconstructs the manipulated "
             "instruction machine.",
             "knowledge_state": "Works out that Horikita's read input "
             "differed from Ayanokouji's real instruction — and that "
             "the school's interference cut the other way.",
             "changes": "'If she had followed Ayanokouji-kun's real "
             "instructions, I would have lost instead'; 'I won't allow "
             "the school to repeatedly interfere with the outcome of "
             "our battles.'",
             "why": "First time she is beaten by a channel she didn't "
             "control — the grievance that fuels y2's wager.",
             "evidence_refs": ["y1v11.5 p.68", "y1v11.5 p.83"]},
            {"vol_id": "y2v9.5",
             "situation": "A quiet corridor question: how does Class A "
             "look to him now?",
             "knowledge_state": "She has finished assessing him as a "
             "peer.",
             "changes": "'I recognize you as an enemy that I must "
             "defeat.'",
             "why": "The relationship hardens from curiosity to formal "
             "enmity.",
             "evidence_refs": ["y2v9.5 p.106", "y2v9.5 p.110"]},
            {"vol_id": "y2v11",
             "situation": "End-of-year exam terms are set.",
             "knowledge_state": "The stake is explicit and absolute.",
             "changes": "'For the end-of-year exam, the loser will "
             "leave this school—that's what it's about.'",
             "why": "The commitment made before the duel that defines "
             "her exit.",
             "evidence_refs": ["y2v11 p.208"]},
            {"vol_id": "y2v12",
             "situation": "The duel vs Ryuuen: discussion-game mastery "
             "on the field.",
             "knowledge_state": "She reads him to checkmate — and "
             "receives Ayanokouji's message through Hashimoto mid-"
             "endgame.",
             "changes": "Beats Ryuuen outright (he admits 'checkmate'), "
             "then chooses the other path: 'Sakayanagi Arisu is not "
             "desired by Ayanokouji Kiyotaka from now on' — she "
             "foregoes the victory she earned.",
             "why": "The pivot of her entire series: winning the battle "
             "and conceding the war in the same hour.",
             "evidence_refs": ["y2v12 p.199", "y2v12 p.216", "y2v12 p.217"]},
            {"vol_id": "y2v12.5",
             "situation": "Grace period granted, then farewell — March "
             "31, main gate, taxi at 11.",
             "knowledge_state": "Account settled with everyone: Ryuuen "
             "the victor, Hashimoto the betrayer she protects, Kamuro "
             "she will visit first.",
             "changes": "'I accepted defeat knowing the content of the "
             "message, and my strength was insufficient'; two wishes — "
             "reunion after she leaves, and Hashimoto's future "
             "treatment; her class eats a 300-point withdrawal penalty.",
             "why": "Exit written as setup: 'setting the groundwork… "
             "trials over the next year to become a more suitable "
             "opponent.'",
             "evidence_refs": ["y2v12.5 p.36", "y2v12.5 p.97", "y2v12.5 p.98"]},
        ],
        "interpretations": [
            {"claim": "Her withdrawal was a chosen move, not a "
             "suffered defeat — she accepted the loss to honor "
             "Ayanokouji's wish",
             "basis_refs": ["y2v12.5 p.34", "y2v12.5 p.36", "y2v12.5 p.35"],
             "confidence": 0.8,
             "notes": "Two readings live side by side: Ryuuen's — "
             "'you self-destructed because of that message' — and hers "
             "('my strength was insufficient… I accepted defeat knowing "
             "the content'). Her own 'setting the groundwork' (p.97) "
             "hints at further motives. The corpus supports chosen-move "
             "as primary with strategic aftertaste."},
            {"claim": "Her weapon is held secrets: she cold-reads "
             "everyone's hidden shame and waits",
             "basis_refs": ["y1v9 p.91", "y1v7.5 p.42", "y1v7.5 p.114"],
             "confidence": 0.85,
             "notes": "Kamuro's shoplifting, Ichinose's opened heart, "
             "Masumi's identical problem — one method, three targets. "
             "Competing: she is not all-seeing — Hashimoto's betrayal "
             "and Ryuuen's traitor rights both surprised her "
             "(y2v12 p.197)."},
            {"claim": "She treats rivalry as courtship — Ayanokouji is "
             "the opponent she wants to be seen by",
             "basis_refs": ["y1v11 p.433", "y2v9.5 p.110", "y2v12.5 p.97"],
             "confidence": 0.8,
             "notes": "Face-off satisfaction, formal enemy-declaration, "
             "and the reunion wish form one line. The counter-evidence "
             "is her own pain when he doesn't want her as opponent "
             "(y2v12 p.216 'even hated this thought process') — the "
             "courtship reads real precisely because it can wound."},
            {"claim": "Competence expressed as play — she handicaps, "
             "torments, and teases rather than simply crushing",
             "basis_refs": ["y1v7.5 p.37", "y1v7 p.115", "y2v12 p.199"],
             "confidence": 0.75,
             "notes": "Boredom-motivated play is her stated mode; even "
             "at checkmate she feels 'parental emotion' toward Ryuuen. "
             "Competing: the play is a luxury that collapses the moment "
             "the stakes stop amusing her (y2v11's flat wager line)."},
            {"claim": "She is her father's doctrine made flesh — "
             "elite selection as moral good, inherited not rebelled "
             "against",
             "basis_refs": ["y0 p.38", "y0 p.87", "y1v7 p.69"],
             "confidence": 0.6,
             "notes": "Childhood and adulthood repeat the same voice "
             "(facility tour → admissions doctrine at the party). "
             "Competing reading: her final wishes — protecting the "
             "betrayer, promising reunion — are personal, not "
             "doctrinal, suggesting the inheritance is manners more "
             "than belief; corpus cannot fully settle it."},
        ],
        "relations": [
            {"char_b": "ayanokouji-kiyotaka",
             "rel_type": "declared-enemy-wishful",
             "direction_note": "Prior knowledge (White Room, y1v5) → "
             "formal enemy (y2v9.5) → she forfeits the duel victory he "
             "asked for (y2v12.5) → first wish: meet again after "
             "leaving.",
             "valid_from_vol": "y1v5", "valid_to_vol": None,
             "evidence_refs": ["y1v5 p.203", "y2v9.5 p.110", "y2v12.5 p.97"]},
            {"char_b": "ryuuen-kakeru", "rel_type": "exam-victor-then-yield",
             "direction_note": "She beat him to checkmate and then "
             "placed the withdrawal on his ledger instead — a debt he "
             "never asked for; her parting: 'avoid an unsightly "
             "expulsion.'",
             "valid_from_vol": "y1v7", "valid_to_vol": None,
             "evidence_refs": ["y2v12 p.199", "y2v12.5 p.36", "y2v12.5 p.41"]},
            {"char_b": "hashimoto-masayoshi", "rel_type": "betrayed-protected",
             "direction_note": "Her own faction's traitor; she "
             "overlooked him at the critical moment and spent her "
             "second wish on his future treatment.",
             "valid_from_vol": "y1v7.5", "valid_to_vol": None,
             "evidence_refs": ["y2v12.5 p.98", "y3v1 p.49"]},
            {"char_b": "kamuro-masumi", "rel_type": "secret-keeper",
             "direction_note": "Holds her shoplifting secret ('the one "
             "in my keeping') while insisting 'she and I aren't "
             "friends' — and still visits her first after leaving.",
             "valid_from_vol": "y1v7.5", "valid_to_vol": None,
             "evidence_refs": ["y1v7.5 p.37", "y1v9 p.91", "y2v12.5 p.41"]},
            {"char_b": "katsuragi-kouhei", "rel_type": "old-familiar-rival",
             "direction_note": "Former classmate she reads like a book "
             "— tie-mess taunt at the duel (y2v12) — and whose "
             "contract instincts she cited back in y1v7.",
             "valid_from_vol": "y1v7", "valid_to_vol": None,
             "evidence_refs": ["y1v7 p.113", "y2v12 p.130"]},
            {"char_b": "horikita-suzune", "rel_type": "amused-observer",
             "direction_note": "Watches her fight-planning with genuine "
             "approval ('I'm impressed that she's carefully thought "
             "about how to fight me') and jokes herself into "
             "childhood-friend parity with Ayanokouji in her presence.",
             "valid_from_vol": "y1v11.5", "valid_to_vol": None,
             "evidence_refs": ["y1v11.5 p.66", "y2v10 p.152"]},
        ],
    },
    "karuizawa-kei": {
        "status_timeline": [
            {"vol_id": "y1v1",
             "situation": "The social-metabolism girl: points spent on "
             "image before the first exam.",
             "knowledge_state": "Surface only — no strategy visible to "
             "anyone yet.",
             "changes": "'After buying cosmetics and clothes… I've "
             "already used up almost all of my points' — the persona in "
             "one sentence.",
             "why": "The baseline she will later admit was a rebuild.",
             "evidence_refs": ["y1v1 p.117"]},
            {"vol_id": "y1v4",
             "situation": "Island exam: past-bully pressure reappears "
             "inside the class, and Ayanokouji corners her with "
             "questions.",
             "knowledge_state": "He knows more than he should; she can "
             "no longer keep the wall intact.",
             "changes": "'It's not like this is the first time someone's "
             "used force against me'; 'I'm doing this for my own sake. "
             "I want those private points' — survival logic stated "
             "aloud before the full confession.",
             "why": "First cracks in the rebuilt identity.",
             "evidence_refs": ["y1v4 p.200", "y1v4 p.222", "y1v4 p.196"]},
            {"vol_id": "y1v4.5",
             "situation": "The past is told in full, and a partnership "
             "is contracted the same day.",
             "knowledge_state": "Junior-high years of bullying, the "
             "teachers' failure, the cover-up — all on the table; "
             "Ayanokouji's second side is on hers.",
             "changes": "'No one here knows about my past. That's why I "
             "was able to become a new me' — plus 'So, I just need to "
             "carry out your orders?' The spy-partnership begins.",
             "why": "The dossier's anchor claim forms here: she is the "
             "only classmate who has seen both of him.",
             "evidence_refs": ["y1v4.5 p.158", "y1v4.5 p.162", "y1v4.5 p.160"]},
            {"vol_id": "y1v5",
             "situation": "Sports festival lead-up: her group's VIP "
             "identity is already solved in retrospect; the girls' "
             "voice channels through her.",
             "knowledge_state": "Positioned as class-bloc informant for "
             "Ayanokouji while keeping first-name distance ('Kiyotaka' "
             "trial run).",
             "changes": "Moves from asset to active feeder — Horikita's "
             "plan complaints, traitor suspicions routed by her.",
             "why": "The partnership operationalizes.",
             "evidence_refs": ["y1v5 p.13", "y1v5 p.42", "y1v5 p.129"]},
            {"vol_id": "y1v6",
             "situation": "Satou's confession lands between her "
             "partnership and her cover; exam panic peaks.",
             "knowledge_state": "She manages both fronts without "
             "exposing either.",
             "changes": "'I knew it. Everyone is my enemy' at the "
             "study-group blowup — then the same day she softens: "
             "cools off, apologizes, covers Kushida's cleaning fee.",
             "why": "The two poles of her defended self — siege and "
             "repair — in a single volume.",
             "evidence_refs": ["y1v6 p.166", "y1v6 p.167", "y1v6 p.27"]},
            {"vol_id": "y1v7",
             "situation": "School ship: Ryuuen traps her alone to break "
             "the X network.",
             "knowledge_state": "Cornered with the one thing she "
             "promised never to lose — the rebuilt identity.",
             "changes": "'If you lay one finger on me, I'll tell "
             "everyone!'; then the harder version: 'they can go ahead "
             "and tell everyone they like about my past' — she spends "
             "the fear and refuses to break.",
             "why": "The test she was built for; she passes it under "
             "direct threat.",
             "evidence_refs": ["y1v7 p.134", "y1v7 p.174", "y1v7 p.190"]},
            {"vol_id": "y1v7.5",
             "situation": "Christmas arc: the pretend-relationship with "
             "Hirata ends and the real partnership is declared.",
             "knowledge_state": "She has seen him at his least "
             "merciful and stays anyway.",
             "changes": "'Then I'm the only person who really knows "
             "you?' … 'I'll be your partner' … 'If it comes to that, "
             "I'll save you' — and the closest-person claim: 'the "
             "person I'd grown closest to over the past year.'",
             "why": "Witness becomes chosen ally, romantically and "
             "operationally at once.",
             "evidence_refs": ["y1v7.5 p.161", "y1v7.5 p.162", "y1v7.5 p.170"]},
            {"vol_id": "y1v8",
             "situation": "She voices the fear beneath the partnership "
             "in the abstract.",
             "knowledge_state": "Worried she could be made "
             "disposable — the Tachibana situation as her nightmare.",
             "changes": "'What if I wind up in the same situation that "
             "Tachibana-senpai was in…? In a situation where you can't "
             "even use a lifeline?'",
             "why": "Names the price-question of the whole "
             "arrangement without accusing him.",
             "evidence_refs": ["y1v8 p.240"]},
            {"vol_id": "y1v9",
             "situation": "Valentine's Day: the feelings route runs "
             "through a courier.",
             "knowledge_state": "She knows exactly what the chocolate "
             "is and isn't.",
             "changes": "'I've only temporarily entrusted this "
             "chocolate with Ayanokōji-kun, in order for him to give "
             "it to the person I like' — confession delivered as "
             "plausible deniability.",
             "why": "The most compact example of her two-layer "
             "communication style.",
             "evidence_refs": ["y1v9 p.130"]},
            {"vol_id": "y2v4.5",
             "situation": "Under mounting year-2 pressure, she stakes "
             "the promise out loud.",
             "knowledge_state": "Trust asserted as contract, not "
             "hope.",
             "changes": "'Even if something happens, you'll protect "
             "me so I'll be fine. Right, Kiyotaka?'",
             "why": "The partnership reaffirmed in her own words, "
             "mid-arc.",
             "evidence_refs": ["y2v4.5 p.269"]},
            {"vol_id": "y2v11",
             "situation": "Training-camp proximity: the Ichinose "
             "shadow on the partnership.",
             "knowledge_state": "Not blind to his other alliances.",
             "changes": "'You're close with Ichinose-san, Kiyotaka. "
             "Sometimes, I have doubts about various things' — jealousy "
             "said plainly instead of performed.",
             "why": "Her honesty-with-him era in one line.",
             "evidence_refs": ["y2v11 p.38", "y2v11 p.37"]},
            {"vol_id": "y3v1",
             "situation": "After the year-2 break: questions about "
             "dating arrive; the truth is being handled gently.",
             "knowledge_state": "She asks for the real thing even when "
             "it costs.",
             "changes": "'If you're holding back from telling the "
             "truth for my sake—' … 'I feel the same way' — the "
             "post-separation voice: quieter, still present.",
             "why": "The arc closes where it began: two people "
             "negotiating what knowing each other costs.",
             "evidence_refs": ["y3v1 p.166", "y3v1 p.214"]},
        ],
        "interpretations": [
            {"claim": "The 'new me' is a deliberately manufactured "
             "identity — the school was chosen as a site of "
             "anonymity",
             "basis_refs": ["y1v4.5 p.158", "y1v4 p.200"],
             "confidence": 0.8,
             "notes": "Stated almost verbatim ('No one here knows about "
             "my past…'). Her 'grateful to the people who bullied me, "
             "and the school that covered it up' reads as bitterness, "
             "not literal gratitude — the cover-up is what she needed, "
             "not what she approves of."},
            {"claim": "'For my own sake' is armour: self-interest as "
             "the declared motive keeps the partnership honest",
             "basis_refs": ["y1v4 p.222", "y1v7 p.190"],
             "confidence": 0.75,
             "notes": "She uses the identical formula at her two most "
             "exposed moments. Competing: her actual behavior "
             "contradicts pure self-interest — saving, promising, "
             "waiting ('I'll save you', 'you'll protect me') — so the "
             "formula functions as self-permission more than doctrine."},
            {"claim": "She is Ayanokouji's sole witness-partner: the "
             "only one who has seen both sides and stayed",
             "basis_refs": ["y1v4.5 p.160", "y1v7.5 p.161", "y1v7.5 p.170"],
             "confidence": 0.8,
             "notes": "Corroborated by his own claim-voice ('Kei was "
             "the person I'd grown closest to'). The open question the "
             "corpus leaves standing is her own charge — 'you only "
             "view people as tools, don't you, Kiyotaka?' — which the "
             "volumes park without answering."},
            {"claim": "Love grew out of the fake relationship — the "
             "script expired before the feelings did",
             "basis_refs": ["y1v7.5 p.164", "y1v9 p.130", "y1v11.75 p.11"],
             "confidence": 0.75,
             "notes": "Hesitation to end the 'pretend relationship', "
             "the courier-valentine, the girlfriend-voiced wish — one "
             "trajectory. Competing: the feelings predate the script "
             "(first-name 'Kiyotaka' experiments in y1v5 sit on the "
             "borderline)."},
            {"claim": "The year-2 break is handled as mutual "
             "protection, not rupture — silence chosen for both "
             "sides",
             "basis_refs": ["y2v12 p.22", "y3v1 p.166"],
             "confidence": 0.55,
             "notes": "'I won't say anything more… I don't need a "
             "detailed report' plus 'holding back the truth for my "
             "sake' — restraint as the surviving mode. Low confidence: "
             "the corpus here is thin and the motives behind the "
             "separation are asserted by others more than by her."},
        ],
        "relations": [
            {"char_b": "ayanokouji-kiyotaka",
             "rel_type": "witness-partner",
             "direction_note": "From prey of his questions (y1v4) to "
             "contracted spy (y1v4.5) to declared partner ('I'll be "
             "your partner', y1v7.5) to affectionate distrust "
             "('doubts about various things', y2v11) — and through the "
             "year-2 break without either side going silent on the "
             "other.",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v4.5 p.162", "y1v7.5 p.161", "y2v11 p.38"]},
            {"char_b": "hirata-yousuke", "rel_type": "pretend-couple-ended",
             "direction_note": "The cover relationship: 'just a pretend "
             "relationship… I've been hesitating' — unwound honestly "
             "once the Christmas arc made the real feelings undeniable.",
             "valid_from_vol": "y1v1", "valid_to_vol": None,
             "evidence_refs": ["y1v7.5 p.164", "y1v7.5 p.113"]},
            {"char_b": "ryuuen-kakeru", "rel_type": "survivor-of-pressure",
             "direction_note": "He cornered her to extract X's network; "
             "she spent the secret she swore to keep rather than break "
             "— the worst test either of them ran on her.",
             "valid_from_vol": "y1v7", "valid_to_vol": None,
             "evidence_refs": ["y1v7 p.134", "y1v7 p.174"]},
            {"char_b": "satou-maya", "rel_type": "rival-turned-closest-friend",
             "direction_note": "Manage the confession (y1v6) without "
             "losing her; by y2v6 the blame is spent: 'you are "
             "Kiyotaka's friend… I won't forgive you but I will stop "
             "blaming you' — friendship chosen over the grievance.",
             "valid_from_vol": "y1v6", "valid_to_vol": None,
             "evidence_refs": ["y1v6 p.25", "y1v7.5 p.114", "y2v6 p.229"]},
            {"char_b": "manabe-shiho", "rel_type": "past-resentment",
             "direction_note": "The harassment pressure that first "
             "exposed her fault line — 'I'm not merciful like Manabe "
             "and her friends' is someone else's description of the "
             "threat she carried alone.",
             "valid_from_vol": "y1v4", "valid_to_vol": None,
             "evidence_refs": ["y1v4 p.163", "y1v7 p.144"]},
            {"char_b": "ichinose-honami", "rel_type": "friendly-shadowed",
             "direction_note": "Gym-buddy warmth ('we tried the gym "
             "together') shadowed by her doubts about closeness to "
             "Kiyotaka — friendship and rivalry in the same thread.",
             "valid_from_vol": "y2v9", "valid_to_vol": None,
             "evidence_refs": ["y2v9 p.210", "y2v11 p.38"]},
        ],
    },
}


def apply():
    db = sqlite3.connect(DB_PATH)
    n_t = n_i = n_r = 0
    for cid, data in ANALYSIS.items():
        if not db.execute("SELECT 1 FROM characters WHERE char_id=?",
                          (cid,)).fetchone():
            raise SystemExit(f"unknown char_id: {cid}")
        db.execute("DELETE FROM status_timeline WHERE char_id=?", (cid,))
        for e in data.get("status_timeline", []):
            db.execute(
                "INSERT INTO status_timeline (char_id, vol_id, situation, "
                "knowledge_state, changes, why, evidence_refs) "
                "VALUES (?,?,?,?,?,?,?)",
                (cid, e["vol_id"], e["situation"], e["knowledge_state"],
                 e["changes"], e["why"],
                 json.dumps(e["evidence_refs"])))
            n_t += 1
        db.execute("DELETE FROM interpretations WHERE char_id=?", (cid,))
        for e in data.get("interpretations", []):
            db.execute(
                "INSERT INTO interpretations (char_id, claim, basis_refs, "
                "confidence, notes) VALUES (?,?,?,?,?)",
                (cid, e["claim"], json.dumps(e["basis_refs"]),
                 e["confidence"], e["notes"]))
            n_i += 1
        db.execute("DELETE FROM relations WHERE char_a=?", (cid,))
        for e in data.get("relations", []):
            db.execute(
                "INSERT INTO relations (char_a, char_b, rel_type, "
                "direction_note, valid_from_vol, valid_to_vol, "
                "evidence_refs) VALUES (?,?,?,?,?,?,?)",
                (cid, e["char_b"], e["rel_type"], e["direction_note"],
                 e["valid_from_vol"], e.get("valid_to_vol"),
                 json.dumps(e["evidence_refs"])))
            n_r += 1
    db.commit()
    print(f"applied: status_timeline={n_t} interpretations={n_i} "
          f"relations={n_r} for {len(ANALYSIS)} char(s)")
    db.close()


if __name__ == "__main__":
    apply()
