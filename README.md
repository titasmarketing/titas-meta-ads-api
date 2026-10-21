# Meta Marketing API: TITÃS Marketing

Acesso direto à API oficial da Meta (Graph/Marketing API v26.0) para as contas de anúncios dos clientes, sem MCP.
O script de varredura é somente leitura.

## Configurar no seu computador (uma vez)

1. Instale o `uv`:
   - macOS: `brew install uv`  (ou `curl -LsSf https://astral.sh/uv/install.sh | sh`)
   - Windows (PowerShell): `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Copie `.env.example` para `.env` e cole o seu token em `META_ACCESS_TOKEN=` (sem aspas nem espaços).
   O token vem do cofre de senhas da TITÃS. Cada gestor tem o seu; não peça nem use o de outra pessoa.
3. Teste (baixa tudo de uma conta para `dados/<id_da_conta>/`):

```
uv run --python 3.12 --with-requirements requirements.txt python scripts/varredura_conta.py ID_DA_CONTA
```

Para listar as contas que o token enxerga:
`https://graph.facebook.com/v26.0/me/adaccounts?fields=name,account_id&access_token=SEU_TOKEN` (não compartilhe essa URL).

## Cuidados

- `.env` e `dados/` nunca vão para o git (token dá acesso às contas dos clientes; `dados/` guarda dados de clientes).
- Não envie o token por WhatsApp, e-mail ou chat. Use o cofre de senhas ou um link de uso único com expiração.
- Saiu alguém da equipe, ou o token vazou? Avise o Pedro: o token daquela pessoa é revogado sem afetar os outros.
