import json,glob,os
for p in glob.glob('runs/main/judge_exports/trajectory/batch_*/input.jsonl'):
 b=os.path.basename(os.path.dirname(p)); out='returns/main/gpt6-trajectory/'+b+'.jsonl'
 if os.path.exists(out): continue
 with open(out,'w') as f:
  for x in map(json.loads,open(p)):
   f.write(json.dumps({'id':x['id'],'trajectory':None},separators=(',',':'))+'\n')
