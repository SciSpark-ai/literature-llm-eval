import json, re, unicodedata, collections, sys
import pathlib
base=str(pathlib.Path(__file__).resolve().parents[1])
man=json.load(open(f"{base}/data_manifest/clinical-reference-audit.json"))
labels={}
for t in man["topics"]:
    for l in t["labels"]:
        labels[(t["topic_id"],l["pmid"])]=(l["abstract_label"],l["content_label"])

def norm(s):
    s=unicodedata.normalize("NFKC",s).lower()
    s=re.sub(r"[^\w\s]"," ",s); s=re.sub(r"\s+"," ",s).strip(); return s

def classify(quote, src):
    """return failure category for a quote not exactly found"""
    if quote is None or not quote.strip(): return "empty"
    if quote in src: return "exact"
    has_ell = ("..." in quote) or ("…" in quote)
    frags=[f.strip() for f in re.split(r"\.\.\.|…", quote) if f.strip()]
    nsrc=norm(src)
    if not has_ell:
        if norm(quote) in nsrc: return "normalized_match"
        # partial: longest fragment share
        words=norm(quote).split()
        # check if >=80% of 5-grams of quote in source
        grams=[" ".join(words[i:i+5]) for i in range(max(1,len(words)-4))]
        hit=sum(g in nsrc for g in grams)/len(grams)
        if hit>=0.8: return "near_verbatim_minor_edit"
        if hit>=0.3: return "partial_paraphrase"
        return "paraphrase_or_unsupported"
    # elided
    ok=all(norm(f) in nsrc for f in frags if len(f)>=8)
    if ok:
        # ordered?
        pos=[nsrc.find(norm(f)) for f in frags if len(f)>=8]
        return "elided_fragments_in_order" if pos==sorted(pos) else "elided_fragments_unordered"
    return "elided_with_paraphrase"

def load(run):
    req=json.load(open(f"{base}/runs/{run}/stage-a-requests.json"))
    res=json.load(open(f"{base}/runs/{run}/stage-a-results.json"))
    # map topic -> list of candidates with text, from requests (batches)
    text={}
    for r in req:
        u=json.loads(r["req"]["messages"][1]["content"])
        for c in u["candidates"]:
            text.setdefault(r["topic"],[]).append((c["title"] or "")+"\n"+(c["abstract"] or ""))
    out=[]
    for t in res:
        topic=t["topic"]
        for i,rec in enumerate(t["records"]):
            g=rec["grade"]
            src=None
            # locate by pmid: requests don't carry pmid; rely on order
            out.append(dict(run=run,topic=topic,idx=i,pmid=rec["pmid"],modelGrade=g.get("modelGrade"),grade=g.get("grade"),
                            topicGrade=g.get("topicGrade"),quote=g.get("quote"),qv=g.get("quoteVerified"),ungraded=g.get("ungraded"),
                            design=rec.get("design"),mdd=rec.get("modelDesignDropped"),layer=rec.get("layer")))
    # attach text by order within topic
    for topic,lst in text.items():
        recs=[o for o in out if o["topic"]==topic]
        assert len(recs)==len(lst),(topic,len(recs),len(lst))
        for o,s in zip(recs,lst): o["src"]=s
    for o in out:
        o["abs"],o["cont"]=labels.get((o["topic"],o["pmid"]),(None,None))
        o["cat"]="exact" if o["qv"] else classify(o["quote"],o["src"])
    return out

runs={r:load(r) for r in ["clinical-v1","clinical-quote-v2"]}
json.dump(runs,open(f"{base}/runs/replay_records.json","w"),indent=1)

print("== sanity: label coverage"); 
for r,recs in runs.items():
    print(r, "n",len(recs),"abs labels missing",sum(o["abs"] is None for o in recs))

print("\n== quote failure categories among candidates with modelGrade>0 (any label), per run")
for r,recs in runs.items():
    c=collections.Counter(o["cat"] for o in recs if (o["modelGrade"] or 0)>0)
    print(r, dict(c))
print("\n== among abstract-positive with modelGrade>0")
for r,recs in runs.items():
    c=collections.Counter(o["cat"] for o in recs if (o["modelGrade"] or 0)>0 and o["abs"]==1)
    print(r, dict(c))

print("\n== fixed-output policy replay per topic (abstract-positive recall; negatives admitted)")
print("policy A=modelGrade>0 (ignore quote); B=grade>0 after gate; C=B + route quote-fail with modelGrade>0 to review")
for r,recs in runs.items():
    print("--",r)
    for topic in sorted(set(o["topic"] for o in recs)):
        T=[o for o in recs if o["topic"]==topic]
        P=[o for o in T if o["abs"]==1]; N=[o for o in T if o["abs"]==0]
        A=lambda o:(o["modelGrade"] or 0)>0
        B=lambda o:(o["grade"] or 0)>0
        C=lambda o:A(o) and not B(o)
        print(f"{topic} pos={len(P)} neg={len(N)} | A pos {sum(map(A,P))} neg {sum(map(A,N))} | B pos {sum(map(B,P))} neg {sum(map(B,N))} | review-queue pos {sum(map(C,P))} neg {sum(map(C,N))} | contentPos among reviewqueue {sum(1 for o in P if C(o) and o['cont']==1)}")
    # modelGrade==0 positives: silent semantic miss
    for topic in sorted(set(o["topic"] for o in recs)):
        T=[o for o in recs if o["topic"]==topic and o["abs"]==1 and (o["modelGrade"] or 0)==0]
        print(f"   {topic} abstract-positives with modelGrade 0: {len(T)} (cat: {dict(collections.Counter(o['cat'] for o in T))})")

print("\n== paired comparison v1 vs v2 by pmid")
v1={(o["topic"],o["pmid"]):o for o in runs["clinical-v1"]}; v2={(o["topic"],o["pmid"]):o for o in runs["clinical-quote-v2"]}
flip=collections.Counter()
for k in v1:
    a,b=v1[k],v2[k]
    ga,gb=(a["modelGrade"] or 0),(b["modelGrade"] or 0)
    flip[("pos" if a["abs"]==1 else "neg", "same" if ga==gb else ("up" if gb>ga else "down"))]+=1
print(dict(flip))
print("positives where v1 modelGrade>0 but v2 modelGrade==0:", [(k,v1[k]["modelGrade"],v1[k]["cat"]) for k in v1 if v1[k]["abs"]==1 and (v1[k]["modelGrade"] or 0)>0 and (v2[k]["modelGrade"] or 0)==0])
print("design label changes:", sum(1 for k in v1 if v1[k]["design"]!=v2[k]["design"]), "of", len(v1))
print("\n== grade distribution modelGrade (pos/neg) per run")
for r,recs in runs.items():
    print(r, "pos",dict(collections.Counter(o["modelGrade"] for o in recs if o["abs"]==1)), "neg",dict(collections.Counter(o["modelGrade"] for o in recs if o["abs"]==0)))
print("\n== quote length stats for failures (v1)")
L=[len(o["quote"] or "") for o in runs["clinical-v1"] if o["cat"]!="exact"]; print("n",len(L),"median",sorted(L)[len(L)//2] if L else None,"max",max(L) if L else None)
L=[len(o["quote"] or "") for o in runs["clinical-v1"] if o["cat"]=="exact"]; print("exact n",len(L),"median",sorted(L)[len(L)//2] if L else None)
