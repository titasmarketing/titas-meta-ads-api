#!/usr/bin/env python3
"""Diagnostico de um periodo da conta (somente leitura, Graph API).

Uso (na raiz da pasta "Meta Ads API"):
  python3 scripts/diagnostico_periodo.py 1249071343893960 2026-09-20 2026-10-22

Retomavel: pula arquivos ja baixados (use --refazer para baixar de novo).
Le META_ACCESS_TOKEN e META_API_VERSION do .env. O token nunca e impresso.
Saida: dados/<conta>/diag_<inicio>_<fim>/
"""
import json, pathlib, sys, time, urllib.parse, urllib.request, urllib.error

ROOT = pathlib.Path.cwd()
ENV = {}
for line in (ROOT / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip().strip('"').strip("'")
TOKEN = ENV["META_ACCESS_TOKEN"]
VER = ENV.get("META_API_VERSION") or "v26.0"
BASE = f"https://graph.facebook.com/{VER}"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
REFAZER = "--refazer" in sys.argv
acct, since, until = args[0], args[1], args[2]
OUT = ROOT / "dados" / acct / f"diag_{since}_{until}"
OUT.mkdir(parents=True, exist_ok=True)
TR = json.dumps({"since": since, "until": until})


def scrub(s):
    return str(s).replace(TOKEN, "***")


class ApiErro(Exception):
    pass


def call(path, params=None):
    if path.startswith("http"):
        url = path
    else:
        p = dict(params or {})
        p["access_token"] = TOKEN
        url = f"{BASE}/{path}?{urllib.parse.urlencode(p)}"
    last = None
    for tent in range(4):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")
            last = f"{e.code} {scrub(body)[:500]}"
            if e.code >= 500 or '"code":17' in body or '"code":4,' in body or '"code":80004' in body:
                time.sleep(6 * (tent + 1)); continue
            raise ApiErro(last)
        except Exception as e:
            last = scrub(e); time.sleep(4 * (tent + 1))
    raise ApiErro(f"falhou apos tentativas: {last}")


def get_all(path, params):
    data, res = [], call(path, params)
    while True:
        data += res.get("data", [])
        nxt = res.get("paging", {}).get("next")
        if not nxt:
            return data
        res = call(nxt)


def etapa(nome, fn):
    f = OUT / f"{nome}.json"
    if f.exists() and not REFAZER:
        print(f"pulado {nome}")
        return
    try:
        obj = fn()
    except ApiErro as e:
        obj = {"erro": str(e)}
        print(f"ERRO {nome}: {e}")
    f.write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    if not (isinstance(obj, dict) and "erro" in obj):
        print(f"ok {nome}: {len(obj) if isinstance(obj, list) else 1}")


A = f"act_{acct}"
INS_F = ("campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,spend,impressions,reach,frequency,cpm,ctr,clicks,"
         "inline_link_clicks,inline_link_click_ctr,cost_per_inline_link_click,actions,cost_per_action_type,"
         "video_play_actions,video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,"
         "video_p100_watched_actions,video_thruplay_watched_actions,video_avg_time_watched_actions")
BD_F = "campaign_id,campaign_name,spend,impressions,reach,cpm,ctr,inline_link_clicks,actions"

etapa("conta", lambda: call(A, {"fields": "name,account_status,disable_reason,balance,amount_spent,spend_cap,currency,timezone_name,is_prepay_account,funding_source_details,min_daily_budget"}))
etapa("campanhas", lambda: get_all(f"{A}/campaigns", {"limit": 200, "fields": "id,name,objective,status,effective_status,configured_status,daily_budget,lifetime_budget,bid_strategy,start_time,created_time,updated_time,issues_info"}))
etapa("conjuntos", lambda: get_all(f"{A}/adsets", {"limit": 200, "fields": "id,name,campaign_id,status,effective_status,daily_budget,lifetime_budget,optimization_goal,billing_event,destination_type,promoted_object,targeting,start_time,end_time,created_time,updated_time,learning_stage_info,issues_info"}))
etapa("anuncios", lambda: get_all(f"{A}/ads", {"limit": 200, "fields": "id,name,campaign_id,adset_id,status,effective_status,created_time,updated_time,issues_info,ad_review_feedback,creative{id,name,title,body,call_to_action_type,effective_object_story_id,object_story_spec,asset_feed_spec,video_id,instagram_permalink_url}"}))
etapa("atividades", lambda: get_all(f"{A}/activities", {"limit": 200, "since": since, "until": until, "fields": "event_time,event_type,translated_event_type,object_id,object_name,object_type,extra_data,actor_name"}))

base = {"time_range": TR, "limit": 500}
etapa("ins_conta_diario", lambda: get_all(f"{A}/insights", {**base, "level": "account", "time_increment": 1, "fields": "spend,impressions,reach,frequency,cpm,ctr,inline_link_clicks,actions,cost_per_action_type,video_play_actions,video_thruplay_watched_actions"}))
etapa("ins_anuncio_diario", lambda: get_all(f"{A}/insights", {**base, "level": "ad", "time_increment": 1, "fields": INS_F}))
etapa("ins_anuncio_total", lambda: get_all(f"{A}/insights", {**base, "level": "ad", "fields": INS_F}))
etapa("ins_conjunto_semanal", lambda: get_all(f"{A}/insights", {**base, "level": "adset", "time_increment": 7, "fields": INS_F.replace("ad_id,ad_name,", "")}))
for nome, bd in [("regiao", "region"), ("posicionamento", "publisher_platform,platform_position"),
                 ("idade_genero", "age,gender"), ("dispositivo", "device_platform"),
                 ("horario", "hourly_stats_aggregated_by_advertiser_time_zone")]:
    etapa(f"bd_campanha_{nome}", lambda bd=bd: get_all(f"{A}/insights", {**base, "level": "campaign", "fields": BD_F, "breakdowns": bd}))
etapa("bd_conta_regiao_semanal", lambda: get_all(f"{A}/insights", {**base, "level": "account", "time_increment": 7, "fields": "spend,impressions,actions", "breakdowns": "region"}))
print("FIM", OUT)
