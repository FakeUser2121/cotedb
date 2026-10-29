"""P5 stage: curated mid-tier type assignment (dossier folder routing).

python3 kb/assign_mid_type.py

mid_type ∈ authority|rivals|allies|peers|family|outside for every tier-2
character (decision table below — reviewable, persisted, idempotent);
tier-1 (main) chars stay NULL. Dossier builder routes on this column.
"""
import sqlite3

from roster_mine import DB_PATH

MID_TYPES = {
    "chabashira-sae": "authority",        # homeroom teacher 1-D
    "hoshinomiya-chie": "authority",      # teacher
    "mashima-tomonari": "authority",      # teacher
    "tsubaki-sakurako": "authority",      # teacher
    "ayanokouji-atsuomi": "family",       # father
    "horikita-manabu": "family",          # brother
    "hashimoto-masayoshi": "rivals",      # class-A schemer
    "housen-kazuomi": "rivals",           # class-D hostile leader arc
    "ishizaki-daichi": "rivals",          # Ryuuen camp enforcer
    "katsuragi-kouhei": "rivals",         # class-A rival leadership
    "nagumo-miyabi": "rivals",            # student-council rival
    "nanase-tsubasa": "rivals",           # tracks Ayanokouji (tsukishiro side)
    "yagami-takuya": "rivals",            # White Room rival
    "hirata-yousuke": "allies",           # class-D stabilizer
    "sakura-airi": "allies",              # helped/protected arc
    "sudou-ken": "allies",                # friend/ally from class D
    "kouenji-rokusuke": "peers",          # class-D individualist
    "sakagami": "peers",                  # class rep peer
    "shiina-hiyori": "peers",             # rival-class reader/writer circle
    "tsukishiro": "outside",              # Ayanokouji Sr enforcer
}


def main():
    db = sqlite3.connect(DB_PATH)
    known = {r[0] for r in db.execute(
        "SELECT char_id FROM characters WHERE tier=2")}
    missing = known - set(MID_TYPES)
    extra = set(MID_TYPES) - known
    if missing or extra:
        raise SystemExit(f"routing table out of sync — missing: {sorted(missing)} "
                         f"extra: {sorted(extra)}")
    changed = 0
    for cid, mt in MID_TYPES.items():
        cur = db.execute(
            "UPDATE characters SET mid_type=? WHERE char_id=? AND "
            "COALESCE(mid_type,'')<>?", (mt, cid, mt))
        changed += cur.rowcount
    db.execute("UPDATE characters SET mid_type=NULL WHERE tier=1 AND "
               "mid_type IS NOT NULL")
    db.commit()
    after = dict(db.execute(
        "SELECT char_id, COALESCE(mid_type,'') FROM characters"))
    print(f"changed: {changed}")
    by = {}
    for cid, mt in after.items():
        if mt:
            by.setdefault(mt, []).append(cid)
    for mt in sorted(by):
        print(f"  {mt}: {len(by[mt])} {sorted(by[mt])}")
    null_t2 = [c for c in after if after[c] == "" and
               db.execute("SELECT tier FROM characters WHERE char_id=?",
                          (c,)).fetchone()[0] == 2]
    print(f"tier-2 without type: {null_t2}")
    again = 0
    for cid, mt in MID_TYPES.items():
        again += db.execute(
            "UPDATE characters SET mid_type=? WHERE char_id=? AND "
            "COALESCE(mid_type,'')<>?", (mt, cid, mt)).rowcount
    db.commit()
    print(f"idempotent (2nd pass changes): {again}")
    db.close()


if __name__ == "__main__":
    main()
