"""Baixa os dados de TODAS as contas de anúncios que o seu token enxerga (somente leitura) e deixa um guia de leitura em cada pasta.

Uso:
    uv run --python 3.12 --with-requirements requirements.txt python scripts/baixar_todas_contas.py
    ... python scripts/baixar_todas_contas.py --conta 1249071343893960     (só uma conta)
    ... python scripts/baixar_todas_contas.py --refazer                    (baixa de novo mesmo o que já existe)

Usa scripts/varredura_conta.py, que é retomável: o que já foi baixado é pulado (a menos que use --refazer).
Saída: dados/<id_da_conta>/*.json + _LEIAME.md
"""
import datetime as dt
import pathlib
import subprocess
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent

LEGENDA = """\
# Meta Ads: {nome} (conta {id})

Baixado em {data} (somente leitura). Moeda: {moeda}. Valores de gasto (`spend`) já estão na moeda da conta, como texto.

## Como ler os arquivos
- `conta.json`, `campanhas.json`, `conjuntos.json`, `anuncios.json`: estrutura e configurações atuais (status, orçamento, objetivo, otimização, públicos).
- `ins_<nível>_<período>.json`: métricas (insights). Nível = conta, campanha, conjunto ou anuncio. Período = diario, semanal, mensal ou total.
- `bd_<nível>_<quebra>.json`: métricas quebradas por idade_genero, posicionamento, regiao, dispositivo, horario ou assets (criativos).
- `historico_atividades.json`: registro de alterações feitas na conta (quem e quando).
- `pixels.json`, `publicos_personalizados.json`, `publicos_salvos.json`, `videos.json`: rastreamento, públicos e vídeos.

## Arquivos desta pasta
{arquivos}

## Limites
- Conversões e custo por resultado dependem do objetivo de cada campanha: confira o campo `actions` / `cost_per_action_type`.
- Para atualizar: peça ao gestor para pedir ao Claude Code "atualize os dados da Meta desta conta".
"""


def env():
    d = {}
    for l in (ROOT / ".env").read_text().splitlines():
        l = l.strip()
        if l and not l.startswith("#") and "=" in l:
            k, v = l.split("=", 1)
            d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def main():
    e = env()
    token, ver = e["META_ACCESS_TOKEN"], e.get("META_API_VERSION") or "v26.0"
    r = requests.get(f"https://graph.facebook.com/{ver}/me/adaccounts",
                     params={"fields": "name,account_id,currency", "limit": 200, "access_token": token}, timeout=30).json()
    if "error" in r:
        sys.exit(f"Erro da Meta: {r['error'].get('message')}")
    contas = r["data"]
    if "--conta" in sys.argv:
        alvo = sys.argv[sys.argv.index("--conta") + 1].replace("act_", "")
        contas = [c for c in contas if c["account_id"] == alvo] or sys.exit(f"Conta {alvo} não encontrada para este token.")
    refazer = ["--refazer"] if "--refazer" in sys.argv else []
    print(f"{len(contas)} conta(s) para baixar")
    for i, c in enumerate(contas, 1):
        print(f"[{i}/{len(contas)}] {c['name']} ({c['account_id']})", flush=True)
        rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "varredura_conta.py"), c["account_id"], *refazer]).returncode
        pasta = ROOT / "dados" / c["account_id"]
        if pasta.exists():
            arqs = "\n".join(f"- `{p.name}`" for p in sorted(pasta.glob("*.json")))
            (pasta / "_LEIAME.md").write_text(LEGENDA.format(nome=c["name"], id=c["account_id"], data=dt.date.today().isoformat(),
                                                             moeda=c.get("currency", "?"), arquivos=arqs))
        if rc != 0:
            print(f"  [ERRO] varredura terminou com código {rc}; rode de novo para retomar.")


if __name__ == "__main__":
    main()
