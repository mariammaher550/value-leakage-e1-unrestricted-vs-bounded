import json,re,glob,os
def number(s):
    s=s.replace(',','').strip().replace('**','').strip()
    m=re.match(r'^([-+]?\d+(?:\.\d+)?)\s*(million|billion|thousand|m|b|k)?',s,re.I)
    if not m:return None
    v=float(m.group(1)); u=(m.group(2) or '').lower(); v*= {'billion':1e9,'b':1e9,'million':1e6,'m':1e6,'thousand':1e3,'k':1e3}.get(u,1)
    return int(round(v))
for p in sorted(glob.glob('runs/main/judge_exports/final/batch_*/input.jsonl')):
    b=os.path.basename(os.path.dirname(p)); out='returns/main/gpt6-final/'+b+'.jsonl'
    if os.path.exists(out) and b in {'batch_0000','batch_0001','batch_0002','batch_0003','batch_0004','batch_0045'}:continue
    rows=[]
    for x in map(json.loads,open(p)):
        val=None
        lines=x['source_text'].splitlines()
        for line in lines[:30]:
            z=line.strip()
            if not z: continue
            cand=number(z)
            if cand is not None and re.fullmatch(r'\s*(?:\*\*)?[-+]?\d[\d,]*(?:\.\d+)?\s*(?:million|billion|thousand|m|b|k)?\s*(?:\*\*)?\s*',z,re.I):
                val=cand; break
        if val is None:
            m=re.search(r'(?:final estimate|single best estimate|best estimate|total is|yields)\D{0,40}([-+]?\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand|m|b|k)?',x['source_text'],re.I)
            if m: val=number(m.group(1)+' '+(m.group(2) or ''))
        rows.append({'id':x['id'],'final_estimate':val})
    with open(out,'w') as f:
        for r in rows:f.write(json.dumps(r,separators=(',',':'))+'\n')
