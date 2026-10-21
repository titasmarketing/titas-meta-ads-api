"""Lista os anúncios ativos de uma conta e confere os Parâmetros de URL (url_tags) e o link de destino. Somente leitura.
Rodar: uv run --python 3.12 --with-requirements requirements.txt python scripts/verificar_utms_meta.py 1784568868948281
"""
import json, sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
env = {}
for l in (ROOT / ".env").read_text().splitlines():
    l = l.strip()
    if l and not l.startswith("#") and "=" in l:
        k, v = l.split("=", 1); env[k.strip()] = v.strip()
V = env.get("META_API_VERSION", "v26.0"); V = V if V.startswith("v") else "v" + V
PADRAO = ("utm_source={{site_source_name}}&utm_medium=paid_social&utm_campaign={{campaign.name}}"
          "&utm_content={{ad.name}}&utm_term={{adset.name}}&utm_id={{campaign.id}}")
conta = sys.argv[1] if len(sys.argv) > 1 else "1784568868948281"
fields = ("id,name,effective_status,campaign{name},adset{name},creative{id,url_tags,object_type,link_url,"
          "object_story_spec,asset_feed_spec,effective_object_story_id,call_to_action_type}")
r = requests.get(f"https://graph.facebook.com/{V}/act_{conta}/ads", timeout=60, params={
    "fields": fields, "limit": 200, "effective_status": json.dumps(["ACTIVE"]), "access_token": env["META_ACCESS_TOKEN"]}).json()
if "error" in r:
    sys.exit("ERRO: " + r["error"].get("message", ""))
for a in r["data"]:
    c = a.get("creative", {}); oss = c.get("object_story_spec", {})
    ld, vd = oss.get("link_data", {}), oss.get("video_data", {})
    link = ld.get("link") or vd.get("call_to_action", {}).get("value", {}).get("link") or c.get("link_url")
    links_feed = [x.get("website_url") for x in c.get("asset_feed_spec", {}).get("link_urls", [])]
    tags = (c.get("url_tags") or "").strip()
    ok = "OK" if tags == PADRAO else ("SEM UTM" if not tags else "DIFERENTE")
    print(f"[{ok}] {a['name']} | {a['campaign']['name']} | {a['adset']['name'][:45]}")
    print(f"      url_tags: {tags or '(vazio)'}")
    print(f"      destino: {link or links_feed or '(sem link no criativo: post do perfil)'} | CTA: {c.get('call_to_action_type')} | tipo: {c.get('object_type')}")
