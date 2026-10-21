#!/usr/bin/env python3
"""
Varredura completa de uma conta de anúncios da Meta via Graph API (somente leitura).

Uso:
    python3 scripts/varredura_conta.py 1249071343893960

- Lê META_ACCESS_TOKEN e META_API_VERSION do arquivo .env na raiz desta pasta.
- Salva tudo em dados/<id_da_conta>/ (um JSON por relatório).
- É retomável: relatórios já salvos são pulados. Use --refazer para baixar de novo.
- O token nunca é impresso nem salvo nos arquivos.
"""
import json, pathlib, sys, time
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_env():
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()
TOKEN = ENV["META_ACCESS_TOKEN"]
VER = ENV.get("META_API_VERSION", "v23.0") or "v23.0"
BASE = f"https://graph.facebook.com/{VER}"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
ACC = ARGS[0] if ARGS else "1249071343893960"
ACT = f"act_{ACC}"
REFAZER = "--refazer" in sys.argv
OUT = ROOT / "dados" / ACC
OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session()

ALL_STATUS = ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED", "IN_PROCESS", "WITH_ISSUES",
              "CAMPAIGN_PAUSED", "ADSET_PAUSED", "PENDING_REVIEW", "DISAPPROVED",
              "PREAPPROVED", "PENDING_BILLING_INFO"]


def scrub(s):
    return str(s).replace(TOKEN, "***")


def log(*a):
    print(time.strftime("%H:%M:%S"), *[scrub(x) for x in a], flush=True)


def call(method, url, params=None, tries=6):
    params = dict(params or {})
    if "access_token=" not in url:
        params["access_token"] = TOKEN
    for i in range(tries):
        try:
            if method == "GET":
                r = S.get(url, params=params, timeout=180)
            else:
                r = S.post(url, data=params, timeout=180)
        except requests.RequestException as e:
            log("  erro de rede:", e)
            time.sleep(5 * (i + 1))
            continue
        try:
            j = r.json()
        except ValueError:
            j = {}
        if r.status_code == 200:
            return j
        err = j.get("error", {}) if isinstance(j, dict) else {}
        code = err.get("code")
        msg = err.get("error_user_msg") or err.get("message") or r.text[:300]
        if code in (4, 17, 32, 613, 80000, 80003, 80004) or r.status_code >= 500 or err.get("is_transient"):
            wait = 30 * (i + 1)
            log(f"  limite/transitório (code {code}): {msg[:160]} — aguardando {wait}s")
            time.sleep(wait)
            continue
        raise RuntimeError(scrub(f"HTTP {r.status_code} code={code} sub={err.get('error_subcode')}: {msg}"))
    raise RuntimeError("muitas tentativas sem sucesso")


def get_all(path_or_url, params):
    url = path_or_url if path_or_url.startswith("http") else f"{BASE}/{path_or_url}"
    data, p = [], dict(params)
    while True:
        j = call("GET", url, p)
        if isinstance(j.get("data"), list):
            data.extend(j["data"])
        else:
            return j
        nxt = j.get("paging", {}).get("next")
        if not nxt:
            break
        url, p = nxt, {}
    return data


def enc(p):
    return {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in p.items()}


def save(name, obj):
    (OUT / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    n = len(obj) if isinstance(obj, list) else 1
    log(f"  ✓ {name}: {n} registros")


def done(name):
    return (OUT / f"{name}.json").exists() and not REFAZER


# ---------------------------------------------------------------- entidades
def entidades():
    if not done("conta"):
        save("conta", call("GET", f"{BASE}/{ACT}", {"fields": ",".join([
            "id", "name", "account_status", "amount_spent", "created_time", "currency",
            "timezone_name", "disable_reason", "spend_cap", "business", "balance"])}))

    def listar(name, edge, fields, limit=200):
        if done(name):
            return
        for status in (ALL_STATUS, ["ACTIVE", "PAUSED", "ARCHIVED", "DELETED"], None):
            p = {"fields": fields, "limit": limit}
            if status:
                p["effective_status"] = json.dumps(status)
            try:
                save(name, get_all(f"{ACT}/{edge}", p))
                return
            except RuntimeError as e:
                log(f"  {name}: tentativa falhou ({e}); tentando alternativa")
        log(f"  ✗ {name}: não foi possível listar")

    listar("campanhas", "campaigns", ",".join([
        "id", "name", "objective", "status", "effective_status", "created_time", "start_time",
        "stop_time", "updated_time", "daily_budget", "lifetime_budget", "budget_remaining",
        "buying_type", "bid_strategy", "special_ad_categories", "smart_promotion_type"]))
    listar("conjuntos", "adsets", ",".join([
        "id", "name", "campaign_id", "status", "effective_status", "created_time", "start_time",
        "end_time", "updated_time", "daily_budget", "lifetime_budget", "optimization_goal",
        "billing_event", "bid_strategy", "bid_amount", "destination_type", "promoted_object",
        "targeting", "attribution_spec", "is_dynamic_creative"]))
    listar("anuncios", "ads", ",".join([
        "id", "name", "adset_id", "campaign_id", "status", "effective_status", "created_time",
        "updated_time", "preview_shareable_link",
        "creative{id,name,title,body,object_type,call_to_action_type,thumbnail_url,image_url,"
        "video_id,object_story_spec,asset_feed_spec,effective_object_story_id,"
        "effective_instagram_media_id,instagram_permalink_url,link_url,url_tags}"]), limit=50)

    extras = {
        "publicos_personalizados": ("customaudiences", "id,name,subtype,description,"
            "approximate_count_lower_bound,approximate_count_upper_bound,time_created,time_updated,"
            "rule,lookalike_spec,retention_days,delivery_status,operation_status"),
        "publicos_salvos": ("saved_audiences", "id,name,targeting,time_created,time_updated,description"),
        "pixels": ("adspixels", "id,name,creation_time,last_fired_time,is_unavailable"),
        "videos": ("advideos", "id,title,length,created_time,permalink_url"),
    }
    for name, (edge, fields) in extras.items():
        if done(name):
            continue
        try:
            save(name, get_all(f"{ACT}/{edge}", {"fields": fields, "limit": 200}))
        except RuntimeError as e:
            log(f"  ✗ {name}: {e}")

    if not done("historico_atividades"):
        try:
            save("historico_atividades", get_all(f"{ACT}/activities", {
                "fields": "actor_name,event_time,event_type,translated_event_type,object_id,"
                          "object_name,object_type,extra_data,date_time_in_timezone",
                "since": "2023-01-01", "limit": 500}))
        except RuntimeError as e:
            log(f"  ✗ historico_atividades: {e}")


# ---------------------------------------------------------------- insights
BASE_F = ["spend", "impressions", "reach", "frequency", "clicks", "inline_link_clicks", "ctr",
          "inline_link_click_ctr", "cpc", "cpm", "cost_per_inline_link_click", "actions",
          "cost_per_action_type", "date_start", "date_stop"]
LEVEL_F = {
    "account": [],
    "campaign": ["campaign_id", "campaign_name", "objective"],
    "adset": ["campaign_id", "campaign_name", "adset_id", "adset_name", "optimization_goal"],
    "ad": ["campaign_id", "campaign_name", "adset_id", "adset_name", "ad_id", "ad_name"],
}
VIDEO_F = ["video_play_actions", "video_p25_watched_actions", "video_p50_watched_actions",
           "video_p75_watched_actions", "video_p100_watched_actions",
           "video_thruplay_watched_actions", "video_avg_time_watched_actions"]
RANK_F = ["quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking"]


def run_insights(name, level, time_increment="all_days", breakdowns=None, extra=None, drop=None):
    if done(name):
        return
    fields = [f for f in BASE_F + LEVEL_F[level] + (extra or []) if f not in (drop or [])]
    p = {"level": level, "fields": ",".join(fields), "date_preset": "maximum",
         "time_increment": time_increment, "limit": 500}
    if breakdowns:
        p["breakdowns"] = ",".join(breakdowns)
    variants = []
    if level != "account":
        variants.append({**p, "filtering": [{"field": f"{level}.effective_status", "operator": "IN",
                                             "value": ALL_STATUS}]})
    variants.append(p)
    for v in variants:
        try:
            log(f"→ {name}")
            j = call("POST", f"{BASE}/{ACT}/insights", enc(v))
            rid = j["report_run_id"]
            t0 = time.time()
            while True:
                st = call("GET", f"{BASE}/{rid}", {"fields": "async_status,async_percent_completion"})
                s = st.get("async_status")
                if s == "Job Completed":
                    break
                if s in ("Job Failed", "Job Skipped") or time.time() - t0 > 600:
                    raise RuntimeError(f"job assíncrono: {s}")
                time.sleep(3)
            save(name, get_all(f"{rid}/insights", {"limit": 500}))
            return
        except RuntimeError as e:
            log(f"  {name}: variante falhou ({e})")
            try:  # tentativa síncrona
                save(name, get_all(f"{ACT}/insights", enc(v)))
                return
            except RuntimeError as e2:
                log(f"  {name}: síncrono falhou ({e2})")
    log(f"  ✗ {name}: sem dados")


def insights():
    run_insights("ins_conta_diario", "account", "1")
    run_insights("ins_conta_mensal", "account", "monthly")
    run_insights("ins_campanha_total", "campaign")
    run_insights("ins_campanha_mensal", "campaign", "monthly")
    run_insights("ins_campanha_semanal", "campaign", "7")
    run_insights("ins_conjunto_total", "adset")
    run_insights("ins_conjunto_mensal", "adset", "monthly")
    run_insights("ins_anuncio_total", "ad", extra=VIDEO_F + RANK_F)
    if not done("ins_anuncio_total"):
        run_insights("ins_anuncio_total", "ad", extra=VIDEO_F)
    run_insights("ins_anuncio_mensal", "ad", "monthly")
    # recortes (breakdowns)
    run_insights("bd_campanha_idade_genero", "campaign", breakdowns=["age", "gender"])
    run_insights("bd_conjunto_idade_genero", "adset", breakdowns=["age", "gender"])
    run_insights("bd_conta_idade_genero_mensal", "account", "monthly", breakdowns=["age", "gender"])
    run_insights("bd_campanha_regiao", "campaign", breakdowns=["region"])
    run_insights("bd_conta_regiao_mensal", "account", "monthly", breakdowns=["region"])
    run_insights("bd_campanha_posicionamento", "campaign",
                 breakdowns=["publisher_platform", "platform_position"])
    run_insights("bd_conta_posicionamento_mensal", "account", "monthly",
                 breakdowns=["publisher_platform", "platform_position"])
    run_insights("bd_anuncio_posicionamento", "ad", breakdowns=["publisher_platform"])
    run_insights("bd_campanha_dispositivo", "campaign", breakdowns=["device_platform"])
    run_insights("bd_campanha_horario", "campaign",
                 breakdowns=["hourly_stats_aggregated_by_advertiser_time_zone"],
                 drop=["reach", "frequency"])
    run_insights("bd_anuncio_idade_genero", "ad", breakdowns=["age", "gender"])


if __name__ == "__main__":
    etapa = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--etapa=")), "tudo")
    log(f"Conta {ACT} | API {VER} | saída: dados/{ACC}/")
    if etapa in ("tudo", "entidades"):
        entidades()
    if etapa in ("tudo", "insights"):
        insights()
    log("Fim.")
