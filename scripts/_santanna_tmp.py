import json, pathlib, requests
ROOT=pathlib.Path(__file__).resolve().parent.parent
env={}
for l in (ROOT/".env").read_text().splitlines():
    if "=" in l and not l.strip().startswith("#"):
        k,v=l.split("=",1); env[k.strip()]=v.strip().strip('"').strip("'")
T=env["META_ACCESS_TOKEN"]; V=env.get("META_API_VERSION") or "v26.0"; B=f"https://graph.facebook.com/{V}"
ACT="act_1202738857368533"; out={}
def g(path,**p):
    p["access_token"]=T; r=requests.get(f"{B}/{path}",params=p,timeout=60); j=r.json()
    if "error" in j: return {"error":j["error"].get("message")}
    return j
out["campaigns"]=g(f"{ACT}/campaigns",fields="name,status,effective_status,objective,daily_budget,lifetime_budget,start_time,bid_strategy",limit=100)
out["adsets"]=g(f"{ACT}/adsets",fields="name,status,effective_status,campaign{name},daily_budget,optimization_goal,targeting{age_min,age_max,genders,geo_locations,custom_audiences}",effective_status='["ACTIVE"]',limit=100)
out["ads"]=g(f"{ACT}/ads",fields="name,effective_status,adset{name},campaign{name},creative{title,body,object_story_spec}",effective_status='["ACTIVE"]',limit=100)
for per in ["last_7d","last_30d"]:
    out["ins_ad_"+per]=g(f"{ACT}/insights",level="ad",date_preset=per,fields="campaign_name,adset_name,ad_name,spend,impressions,reach,frequency,clicks,ctr,cpm,actions,cost_per_action_type",limit=200)
out["ins_daily"]=g(f"{ACT}/insights",level="campaign",date_preset="last_14d",time_increment=1,fields="campaign_name,spend,actions",limit=500)
(ROOT/"dados"/"santanna_meta_2026-10-15.json").write_text(json.dumps(out,ensure_ascii=False,indent=1))
print("ok", {k:("error" if isinstance(v,dict) and "error" in v else len(v.get("data",[]))) for k,v in out.items()})
for k,v in out.items():
    if isinstance(v,dict) and "error" in v: print(k,v["error"])
