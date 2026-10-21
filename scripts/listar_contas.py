"""Lista as contas de anúncios que o seu token da Meta enxerga (somente leitura).

Uso:
    uv run --python 3.12 --with-requirements requirements.txt python scripts/listar_contas.py

Lê META_ACCESS_TOKEN e META_API_VERSION do .env na raiz. O token nunca é impresso.
"""
import pathlib
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATUS = {1: "ativa", 2: "desativada", 3: "pendência de pagamento", 7: "em análise",
          9: "período de carência", 100: "pendente de encerramento", 101: "encerrada"}


def load_env():
    env = {}
    arquivo = ROOT / ".env"
    if not arquivo.exists():
        sys.exit("Arquivo .env não encontrado na raiz do projeto. Copie o seu arquivo de token para .env.")
    for line in arquivo.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def main():
    env = load_env()
    token = env.get("META_ACCESS_TOKEN", "")
    if not token:
        sys.exit("META_ACCESS_TOKEN está vazio no .env.")
    versao = env.get("META_API_VERSION") or "v26.0"
    r = requests.get(
        f"https://graph.facebook.com/{versao}/me/adaccounts",
        params={"fields": "name,account_id,account_status,currency,business{name}", "limit": 200, "access_token": token},
        timeout=30,
    ).json()
    if "error" in r:
        sys.exit(f"Erro da Meta: {r['error'].get('message')}")
    contas = r.get("data", [])
    print(f"{len(contas)} conta(s) de anúncios")
    for a in contas:
        bm = (a.get("business") or {}).get("name", "—")
        print(f"- {a['name']} | {a['account_id']} | {STATUS.get(a['account_status'], a['account_status'])} | {a['currency']} | BM: {bm}")


if __name__ == "__main__":
    main()
