import re, unicodedata, glob, os, sys
os.chdir("/home/user3/Documents/unsafe/cote")
def norm(s):
    s = unicodedata.normalize("NFKC", s)
    for k,v in {"\u2018":"'","\u2019":"'","\u201c":'"',"\u201d":'"',"\u2014":"-","\u2013":"-","\u2026":"..."}.items(): s=s.replace(k,v)
    return re.sub(r"[^0-9a-z\u3040-\u30ff\u4e00-\u9fff]+","",s.lower())
raw=open("text/COTE Y1 V1.txt",encoding="utf-8").read()
pages={};cur=0;buf=[]
for l in raw.splitlines():
    m=re.match(r"^--- page (\d+) ---$",l.strip())
    if m:
        if cur: pages[cur]="\n".join(buf)
        cur=int(m.group(1));buf=[];continue
    if re.match(r"^Page\|\d+$",l.strip()) or re.match(r"^Goldenagato",l.strip()): continue
    buf.append(l)
if cur: pages[cur]="\n".join(buf)
full=norm("\n".join(pages[p] for p in sorted(pages)))
fails=[];total=0
for lf in sorted(glob.glob("drafts/*/*.article.md")):
    for i,line in enumerate(open(lf,encoding="utf-8"),1):
        if line.lstrip().startswith("#"): continue
        pm=re.search(r"\((?:p|pp)\.\s*(\d+)",line)
        local=norm("".join(pages.get(p,"") for p in range(max(1,first),first+6))) if False else None
        first=int(pm.group(1)) if pm else None
        local=norm("".join(pages.get(p,"") for p in range(max(1,first-5),(first or 0)+6))) if first else full
        for m in re.finditer(r'["\u201c]([^"\u201c\u201d]{10,})["\u201d]',line):
            if m.start()>0 and line[m.start()-1].isalnum(): continue
            frags=[f for f in re.split(r"\s*\.\.\.\s*|\s*\u2026\s*",m.group(1)) if len(f.strip())>=10]
            if not frags: continue
            total+=1
            for f in frags:
                nf=norm(f)
                if not nf: continue
                if nf in local or nf in full: continue
                fails.append((lf,i,first,f[:90]));break
print(f"checked {total} quoted spans in articles")
for f in fails: print("  FAIL",f[0],"L"+str(f[1]),"p."+str(f[2]),repr(f[3]))
if not fails: print("ALL PASS")
sys.exit(1 if fails else 0)
