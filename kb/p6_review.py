"""P6 speaker-attribution audit fixes.

Curated corrections discovered during cross-volume verification (P6).
Post-protocol stage: runs after quote_attr/quote_infer/claim_mine;
idempotent. Each fix guards on the expected quote text fragment before
overwriting so a re-run after pipeline changes cannot clobber a
different row.

Two provenance batches:
  AUDIT_FIXES    - manual scene adjudication (narration he-said/she-said,
                   turn continuity, presence casts, self-reference reads)
  AUDIT_NARRATION - anchored narration name-tag resolution on NULL quotes
                   (verb directly after span end; single- or adjudicated
                   multi-candidate name), incl. the 18 multi-tag cases

After fixing quotes, the attribution-derived stages are re-run in
protocol order (event_build -> mention_build -> claim_mine) so
coverage/event_participants/claims stay consistent with the corrected
char_ids. All three are full-rebuild idempotent, so this is safe to
call any time; p6_review is the single owner of that refresh step.
"""

import sqlite3
import subprocess
import sys
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent
DB_PATH = KB_DIR.parent / "cote_kb.db"
REFRESH_STAGES = ("event_build", "mention_build", "claim_mine")

# quote_id -> (expected fragment, new char_id or None, reason)
AUDIT_FIXES = {
    7001463: (
        "worthy of my brother’s",
        "horikita-suzune",
        "y1v5 p.178: continuation of Horikita's brother monologue "
        "('He's my older brother' / relay-anchor speech, answered to "
        "Sudou's 'You're not givin' up?'); 'my brother's admiration' "
        "= Manabu, not Ayanokouji's family",
    ),
    4000635: (
        "Kanzaki. Where",
        "ayanokouji-kiyotaka",
        "y1v3 p.103: narration 'Maybe he wouldn't tell us, but I thought "
        "I'd try asking' then 'Kanzaki answered without hesitation' — "
        "narrator asks, Kanzaki replies",
    ),
    7000516: (
        "Kushida-san and I have no bond",
        "horikita-suzune",
        "y1v5 p.70: narration 'Horikita awkwardly averted her eyes. "
        "\"Kushida-san and I have no bond whatsoever,\" she replied' — "
        "she = Horikita",
    ),
    15000282: (
        "Mashima-sensei presumably has reached his verdict",
        "sakayanagi-arisu",
        "y1v11.5 p.75: Mashima narrated silent through the exchange "
        "('After staying silent, he opened his eyes…'); line continues "
        "Sakayanagi's address to him ('Mashima-sensei. I won't try to "
        "reject…' quote 15000281)",
    ),
    2001763: (
        "Chiyabashira-sensei, last week when you told us",
        None,
        "y1v1 p.225: student question to Chabashira (scene's other "
        "student lines 2001759/2001761 are NULL); speaker identity "
        "not derivable — honest NULL",
    ),
    21000467: (
        "Ichinose did?",
        "ayanokouji-kiyotaka",
        "y2v4.5 p.81: narration 'Recalling the events of yesterday, "
        "Sakayanagi spoke up' for the prior line; narrator reacts "
        "'Ichinose did?' — Sakayanagi answers 'Yes.'",
    ),
    6000672: (
        "It’s personal. Nothing to do with you",
        "katsuragi-kouhei",
        "y1v4.5 p.89: narration 'So, why are you going to school?' "
        "I asked … 'he replied' — Katsuragi answers Ayano's question "
        "(line 6000669 ends 'Katsuragi answered')",
    ),
    6000732: (
        "Officially, I didn’t meet with Katsuragi today",
        "horikita-manabu",
        "y1v4.5 p.94: narration 'as I left, Horikita's brother "
        "accompanied me to the exit' then 'he said' — Manabu grants "
        "cover after the student-council-room meeting",
    ),
    4000037: (
        "C-call you Kikyou-chan",
        "ike-kanji",
        "y1v3 p.17: narration 'In response to Ike's inquiry, Kushida "
        "simply smiled' — Ike asks to switch to first names",
    ),
    5001132: (
        "Whoa, Shiho. Don’t you think you’re hitting her",
        "morofuji-rika",
        "y1v4 p.192: only Manabe/Karuizawa/Rika present; Manabe's "
        "next line 'Come on Rika. You give it a try, too' answers the "
        "chide, then Rika joins ('L-Like that?')",
    ),
    7001710: (
        "are you referring to Horikita Suzune",
        "sakayanagi-arisu",
        "y1v5 p.203: interlocutor is the only named girl on pp.202-204 "
        "(Sakayanagi); 'she replied … she really did know me' + "
        "'I'm the perfect person to bury [you]' = Sakayanagi",
    ),
    12001153: (
        "Hold him down Albert",
        "ishizaki-daichi",
        "y1v9 p.161: two-on-two = Ishizaki+Albert vs Ibuki+Akito; "
        "Albert then pins Akito — Ishizaki commands his partner",
    ),
    13001703: (
        "In third place is",
        "chabashira-sae",
        "y1v10 p.304: the next placement is read by 'Chabashira began "
        "reading a little slower' — same announcement, same reader; "
        "Kushida 'heard her name being called' as audience member",
    ),
    29000954: (
        "My unrequited love",
        "ichinose-honami",
        "y2v10 p.117: 'She admitted it herself' — speaker owns the "
        "confession; Mako-chan/Chihiro-chan referenced as third-party "
        "friends = Ichinose",
    ),
    30000040: (
        "I don’t want you to make Honami-chan sad",
        "amikura-mako",
        "y2v10.25 p.7: speaker refers to Honami/Ichinose in third; "
        "narration 'Right, Amikura agreed' — Amikura warns Ayano",
    ),
    34001736: (
        "I don't want you to make Honami-chan sad",
        "amikura-mako",
        "y3v1 p.282: same exchange as y2v10.25 p.7 (reprinted scene); "
        "friend warns Ayano on Honami's behalf = Amikura",
    ),
    1001525: (
        "This is my son, Ryuuji",
        None,
        "y0 p.193: father introduces Ryuuji ('Say hello, Ryuuji'); no "
        "Kanzaki-father character in roster — honest NULL",
    ),
}

# NULL quotes resolved by an anchored narration name-tag directly after
# the span end (`"…," Name said` / `"…," said Name`); multi-candidate
# names adjudicated by scene presence/turn continuity (see reasons).
AUDIT_NARRATION = {
    2000130: ('It’s nice to meet you, Ayanokouji-kun. I alway',
              'hirata-yousuke', "y1v1 p.40: narration tag 'Hirata'"),
    2000945: ('Ah, sorry, sorry. I didn’t mean to offend,',
              'kushida-kikyou', "y1v1 p.138: narration tag 'Kushida'"),
    2001409: ('So what?', 'kushida-kikyou',
              "y1v1 p.186: narration tag 'Kushida'"),
    3000975: ('Yeah, I suppose so. I think I do stand out, es',
              'sakura-airi', "y1v2 p.136: narration tag 'Sakura'"),
    3001257: ('I haven’t really decided. Just kind of felt li',
              'sakura-airi', "y1v2 p.175: narration tag 'Sakura'"),
    4000032: ('Ah, nothing really,', 'yamauchi-haruki',
              "y1v3 p.17: narration tag 'Yamauchi'"),
    4000684: ('Hmm. Well, I didn’t make a precise calculation',
              'ryuuen-kakeru', "y1v3 p.111: narration tag 'Ryuuen'"),
    5000526: ('Ah, it’s okay. You don’t need to apologize. It',
              'sakura-airi', "y1v4 p.101: narration tag 'Sakura'"),
    5001269: ('Hmm, I wonder about that. Personally, I’ll use',
              'ichinose-honami', "y1v4 p.216: narration tag 'Ichinose'"),
    6001155: ('D-don’t use a scary word like ‘judgment’! I be',
              'yamauchi-haruki', "y1v4.5 p.142: narration tag 'Yamauchi'"),
    7001025: ('Is that really the case?', 'yukimura-teruhiko',
              "y1v5 p.132: narration tag 'Yukimura'"),
    8000161: ('Well, we’ve gotten used to it,', 'ike-kanji',
              "y1v6 p.36: narration tag 'Ike'"),
    9000045: ('Just because it’s not for me doesn’t mean I sh',
              'yukimura-teruhiko', "y1v7 p.17: narration tag 'Keisei'"),
    9000809: ('We do intend to overtake you,', 'yukimura-teruhiko',
              "y1v7 p.95: narration tag 'Keisei'"),
    11000186: ('I just wanted to make sure. Sorry if I offende',
               'shibata-sou', "y1v8 p.43: narration tag 'Shibata'"),
    12001297: ('You have the wrong idea, Sakayanagi. This prob',
               'nagumo-miyabi', "y1v9 p.180: narration tag 'Nagumo'"),
    13001045: ('What’s the matter, Horikita-san?', 'hirata-yousuke',
               "y1v10 p.198: narration tag 'Hirata'"),
    13001064: ('Originally, I thought we should hold a discuss',
               'hirata-yousuke', "y1v10 p.200: narration tag 'Hirata'"),
    13002052: ('I thought you were really amazing yesterday. Y',
               'karuizawa-kei', "y1v10 p.372: narration tag 'Karuizawa'"),
    14000344: ('You didn’t hear about it from Horikita-san? …I',
               'sakura-airi', "y1v11 p.94: narration tag 'Airi'"),
    14000703: ('A little bit?', 'shibata-sou',
               "y1v11 p.177: narration tag 'Shibata'"),
    14000816: ('A gift like this… You, like, you didn’t have t',
               'ichinose-honami', "y1v11 p.209: narration tag 'Ichinose'"),
    14001202: ('Eh?', 'hirata-yousuke', "y1v11 p.297: narration tag 'Hirata'"),
    14001532: ('You could say that.', 'shiina-hiyori',
               "y1v11 p.386: narration tag 'Shiina'"),
    15001015: ('Eh?', 'ichinose-honami',
               "y1v11.5 p.228: narration tag 'Ichinose'"),
    17000368: ('That’s too much…', 'kushida-kikyou',
               "y2v1 p.104: narration tag 'Kushida'"),
    17000444: ('I know that, but at the end of the day you guy',
               'shiratori', "y2v1 p.117: narration tag 'Shiratori'"),
    17001106: ('Why, you ask? I simply calculated that, as lon',
               'nanase-tsubasa', "y2v1 p.242: narration tag 'Nanase'"),
    18000634: ('Wha, that’s an interesting joke. Does a guy wh',
               'ishizaki-daichi', "y2v2 p.152: narration tag 'Ishizaki'"),
    18001242: ('Eh? Ah, that… It’s actually a boy that wants t',
               'kushida-kikyou', "y2v2 p.244: narration tag 'Kushida'"),
    19000307: ('You’re right. I’ll try asking him when I get t',
               'nanase-tsubasa', "y2v3 p.98: narration tag 'Nanase'"),
    19000761: ('That─ Uhm, I wasn’t able to see you and Ike-se',
               'nanase-tsubasa', "y2v3 p.189: narration tag 'Nanase'"),
    19000814: ('We relied on Komiya and Kinoshita’s GPS signal',
               'chabashira-sae', "y2v3 p.198: narration tag 'Chabashira'"),
    19000897: ('It was my decision.', 'katsuragi-kouhei',
               "y2v3 p.214: narration tag 'Katsuragi'"),
    20000812: ('Reply', 'tsubaki-sakurako',
               "y2v4 p.154: narration 'Tsubaki called again with her "
               "walkie-talkie' — she calls 'Reply' into the radio"),
    21001989: ('This Ishigami is innocent.', 'ibuki-mio',
               "y2v4.5 p.250: narration tag 'Ibuki-san'"),
    22000426: ('As far as I’m concerned, you’re a little bit r',
               'yagami-takuya', "y2v5 p.71: narration tag 'Yagami'"),
    22001254: ('It’s Ayanokōji-kun who is having an important ',
               'hirata-yousuke',
               "y2v5 p.194: narration 'So said Yōsuke, giving a "
               "warning to any student who tries to interfere with my "
               "words' — Hirata Yousuke (parse trap: 'So' + said)"),
    22001306: ('That’s certainly not a bad offer. But I’m sorr',
               'kushida-kikyou',
               "y2v5 p.199: narration 'So replied Kushida.' — "
               "Kushida declines the points offer (parse trap: 'So' "
               "+ replied)"),
    23000763: ('I have my doubts,', 'ibuki-mio',
               "y2v6 p.139: narration tag 'Ibuki-san'"),
    23000967: ('I’m not sure… this is my first time hearing of',
               'miyake-akito', "y2v6 p.177: narration tag 'Akito'"),
    24000321: ('I guess so.', 'kanzaki-ryuuji',
               "y2v7 p.42: narration tag 'Kanzaki'"),
    24001351: ('Wait Haruka, I think that\'s a little different',
               'miyake-akito', "y2v7 p.141: narration tag 'Akito'"),
    25000192: ('I\'m ashamed to say this, but I think I was nai',
               'nanase-tsubasa', "y2v8 p.35: narration tag 'Nanase'"),
    25000973: ('...I\'m really... Sorry.', 'yamamura-miki',
               "y2v8 p.114: narration tag 'Yamamura'"),
    26000748: ('...Right.', 'watanabe-norihito',
               "y2v9 p.82: narration tag 'Watanabe'"),
    29001242: ('Hey, be respectful when addressing the teacher',
               'hoshinomiya-chie', "y2v10 p.175: narration tag 'Hoshinomiya'"),
    29001314: ('Calm down, Karuizawa-san. Those mysterious con',
               'ichinose-honami', "y2v10 p.199: narration tag 'Ichinose'"),
    29001338: ('That seems to be the case.', 'shiina-hiyori',
               "y2v10 p.202: narration tag 'Hiyori'"),
    29001491: ('What is it?', 'kamuro-masumi',
               "y2v10 p.219: narration tag 'Kamuro'"),
    31000972: ('You\'re like a knight protecting a princess, bu',
               'amasawa-ichika', "y2v11 p.113: narration tag 'Amasawa'"),
    33000354: ('I’ve always been the type to look at things ob',
               'matsushita-chiaki', "y2v12.5 p.56: narration tag 'Matsushita'"),
    34000169: ('Yes!', 'sugio-hiroshi', "y3v1 p.42: narration tag 'Sugio'"),
    34000841: ('Well, there\'s nothing we can do about studying',
               'ibuki-mio', "y3v1 p.136: narration tag 'Ibuki'"),
    # multi-candidate narration tags, adjudicated:
    1000645: ('It\'s like the ruling party', 'kamogawa-toshizou',
              "y0 p.75: 'Kamogawa said … in typical statesmanlike "
              "fashion' — the Senator, not the y0 student"),
    1001591: ('Is it ironic? I\'ve been on the radar', 'kamogawa-toshizou',
              "y0 p.205: 'Kamogawa laughed bitterly' — political-radar "
              "talk in the Atsuomi conversation = Toshizou"),
    1001595: ('his health seems to have been deteriorating',
              'kamogawa-toshizou',
              "y0 p.205: 'Kamogawa muttered in a hushed voice beside "
              "me'; same line has 'I used to work beside you, "
              "Ayanokouji-sensei' — the Senator"),
    4000796: ('We came to snoop', 'horikita-suzune',
              "y1v3 p.127: 'Horikita responded … daring switch … her "
              "brain'; Manabu mention-only in y1v3"),
    5000297: ('I understand,', 'horikita-suzune',
              "y1v4 p.66: 'Horikita responded. She gave me a slightly "
              "frustrated look' — Suzune; Manabu mention-only in y1v4"),
    5000313: ('As if I would tell you', 'horikita-suzune',
              "y1v4 p.68: Ryuuen confrontation, 'Horikita responded' "
              "— Suzune"),
    5000315: ('I have nothing to tell you', 'horikita-suzune',
              "y1v4 p.69: same confrontation, 'Horikita responded' "
              "— Suzune"),
    6000708: ('There’s nothing odd', 'horikita-suzune',
              "y1v4.5 p.92: continues line 6000706, attributed "
              "horikita-suzune ('I must make one correction to your "
              "theory'); same debate turn"),
    7000201: ('Wait.', 'horikita-suzune',
              "y1v5 p.40: 'Horikita cut in just before Hirata "
              "approved the proposal' — class meeting, Suzune"),
    7001257: ('Do you have any idea where Sudou might be',
              'ayanokouji-kiyotaka',
              "y1v5 p.158: 'Ayanokouji-kun asked me' in Suzune's POV "
              "block (Sudou-search); Atsuomi mention-only in y1v5"),
    13001597: ('I suppose.', 'horikita-suzune',
               "y1v10 p.287: 'Horikita responded dismissively' — "
               "class exam scene, Suzune"),
    16000067: ('Honami-chan, are you feeling well', 'amikura-mako',
               "y1v11.75 p.15: Ichinose SS; 'Mako-chan asked' — "
               "Amikura (Asakura is a y2 near-duplicate, no y1 quotes)"),
    23001678: ('Okay!', 'onodera-kayano',
               "y2v6 p.287: 'Onodera said as she picked up the "
               "racket' — Onodera Kayano (KNOWN curated); the t4 "
               "'Onodera' row is surname-only noise"),
    24000911: ('We\'re done here, too', 'onodera-kayano',
               "y2v7 p.99: 'Onodera said' in the maid-outfits stall "
               "scene — Onodera Kayano"),
    25001766: ('Well, it does look fun for sure', 'ayanokouji-kiyotaka',
               "y2v8 p.200: 'Ayanokoji-kun replied' — Kiyotaka; "
               "Atsuomi mention-only in y2v8"),
    27000579: ('Yeah, I agree,', 'onodera-kayano',
               "y2v9.5 p.78: 'Onodera added' — Onodera Kayano"),
    34000147: ('That\'s not the case', 'ayanokouji-kiyotaka',
               "y3v1 p.37: 'relentlessly showered her with his "
               "words … Ayanokouji-kun answered' — Kiyotaka"),
    34000826: ('All I want now', 'horikita-suzune',
               "y3v1 p.132: free-indirect-discourse line inside "
               "Suzune's POV block (post-Kushida farewell: 'Horikita "
               "apologized … in her heart')"),
    # pre-anchored narration tags (`Name said, "…"` before span start)
    4001094: ('I’m counting on you,', 'ike-kanji',
              "y1v3 p.164: pre-tag 'Ike muttered,'"),
    6000493: ('The name Horikita Suzune came up', 'horikita-manabu',
              "y1v4.5 p.70: pre-tag 'Horikita continued,'; speaker "
              "refers to Suzune in third ('she became her class's true "
              "leader') and cites the special-exam committee + SC "
              "Secretary — Manabu"),
    7000195: ('Both approaches have their pros and cons', 'hirata-yousuke',
              "y1v5 p.39: pre-tag 'Hirata continued,'"),
    10000219: ('but what do you think of Ichinose Honami', 'sakayanagi-arisu',
               "y1v7.5 p.40: pre-tag 'Sakayanagi said,' (addressing "
               "Masumi Kamuro)"),
    10001415: ('but just remember this.', 'kiriyama-ikuto',
               "y1v7.5 p.158: pre-tag 'Kiriyama added,'"),
    11000019: ('The minimum and maximum numbers', 'chabashira-sae',
               "y1v8 p.15: pre-tag 'Chabashira continued,'"),
    11000331: ('before I enrolled here, I had my', 'kouenji-rokusuke',
               "y1v8 p.66: pre-tag 'Kouenji continued,'"),
    21001595: ('While getting to Class A is my top',
               'horikita-suzune',
               "y2v4.5 p.210: pre-tag 'Horikita continued,'; 'I want "
               "to lead them' = class leader + narration 'Horikita's "
               "eyes that stared at me' — Suzune"),
    24001743: ('I\'m going to do it now', 'yagami-takuya',
               "y2v7 p.180: pre-tag 'Yagami-kun said,'"),
    # y2v1 p.94 Ryūen–Hōsen first-meeting scene (pure dialogue chain,
    # no narration anchors inside; resolved from surrounding narration)
    17000296: ('So you’re my opponent now', 'housen-kazuomi',
               "y2v1 p.94: Ryūen approaches; narration 'Given that "
               "Ryūen's physique didn't seem all that large or "
               "impressive, Hōsen spoke his mind' — Hōsen judges the "
               "body ('piss weak compared to … Sudō')"),
    17000297: ('I’ve heard a lot about you. A guy named', 'ryuuen-kakeru',
               "y2v1 p.94: hometown line (p.95: Hōsen from near "
               "Ryūen's hometown) + narration 'Ryūen insulted Hōsen "
               "with the exact same word'"),
    17000298: ('Y-you know this guy, Ryūen-san?', 'ishizaki-daichi',
               "y2v1 p.94: vocative 'Ryūen-san' excludes Ryūen; "
               "scene cast = Ryūen/Hōsen/Ishizaki/Ibuki; stammer "
               "voice continues Ishizaki's 'Wh-why are you stopping "
               "me!?' right after Ryūen stopped him"),
    17000300: ('Oi oi, seriously? This must be fate', 'housen-kazuomi',
               "y2v1 p.94: narration 'Hōsen's facial expression "
               "changed upon hearing Ryūen's name … toothy grin' "
               "then this line — Hōsen to Ryūen"),
    17000301: ('Looks like you’ve got enough brain cells', 'ryuuen-kakeru',
               "y2v1 p.94: answer to Hōsen's 'rumours … pissed me "
               "off, Ryūen' — Ryūen's counter-insult"),
}

# Adjudicated CORRECT by the same audit — kept for the record, no DB
# change.
AUDIT_CONFIRMED = {
    6000187: "y1v4.5 p.34: 'Ibuki. Ibuki Mio,' she answered flatly — "
             "self-introduction, speaker correct",
    8001316: "y1v6 p.151: '…You could call me Keisei or Yukimura,' he "
             "replied — Yukimura about his own given name, correct",
    8001353: "y1v6 p.154: 'Kiyotaka is fine,' I said — narrator grants "
             "first-name permission, correct",
    6001716: "y1v4.5 p.207: 'the supercomputer known as Ike "
             "Kanji-sama' — Ike's boastful third-person self-reference",
    8001298: "y1v6 p.150: 'My name's Haruka' — Hasebe self-intro",
    8001306: "y1v6 p.150: 'stop calling me Teruhiko' — Yukimura about "
             "his own given name",
    8001311: "y1v6 p.151: 'My mother named me Teruhiko' — Yukimura",
    11001004: "y1v8 p.162: 'My name is Kouenji Rokusuke' — self-intro",
}


def _apply_batch(con, batch, label):
    changed = 0
    for quote_id, (fragment, new_char, reason) in batch.items():
        row = con.execute(
            "SELECT text_verbatim, char_id FROM quotes WHERE quote_id=?",
            (quote_id,),
        ).fetchone()
        if row is None:
            raise SystemExit(f"p6_review: quote_id {quote_id} missing")
        text, current = row
        if fragment not in text:
            raise SystemExit(
                f"p6_review: quote_id {quote_id} text drifted, "
                f"expected fragment {fragment!r}"
            )
        if current == new_char:
            continue
        con.execute(
            "UPDATE quotes SET char_id=?, reviewed=1, "
            "attribution_confidence=? WHERE quote_id=?",
            (new_char, 1.0 if new_char else None, quote_id),
        )
        print(
            f"p6_review[{label}]: quote {quote_id} {current} -> "
            f"{new_char} ({reason})"
        )
        changed += 1
    return changed


def apply(db_path: Path = DB_PATH) -> int:
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON")
    changed = _apply_batch(con, AUDIT_FIXES, "manual")
    changed += _apply_batch(con, AUDIT_NARRATION, "narration")
    con.commit()
    con.close()
    print(
        f"p6_review: {changed} fix(es), {len(AUDIT_FIXES)} manual, "
        f"{len(AUDIT_NARRATION)} narration-tag, "
        f"{len(AUDIT_CONFIRMED)} confirmed-correct"
    )
    for stage in REFRESH_STAGES:
        script = KB_DIR / f"{stage}.py"
        proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True,
        )
        tail = (proc.stdout or "").strip().splitlines()
        print(
            f"p6_review: refresh {stage} "
            f"exit={proc.returncode}"
            + (f" | {tail[-1]}" if tail else "")
        )
        if proc.returncode != 0:
            raise SystemExit(
                f"p6_review: refresh {stage} failed:\n"
                f"{proc.stdout}\n{proc.stderr}"
            )
    return changed


if __name__ == "__main__":
    apply()
    sys.exit(0)
