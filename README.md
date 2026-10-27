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

Para listar as contas que o seu token enxerga (e conferir se está tudo certo):

```
uv run --python 3.12 --with-requirements requirements.txt python scripts/listar_contas.py
```

## Cuidados

- `.env` e `dados/` nunca vão para o git (token dá acesso às contas dos clientes; `dados/` guarda dados de clientes).
- Não envie o token por WhatsApp, e-mail ou chat. Use o cofre de senhas ou um link de uso único com expiração.
- Saiu alguém da equipe, ou o token vazou? Avise o Pedro: o token daquela pessoa é revogado sem afetar os outros.

## Dados para analisar no Claude Desktop

O Claude Desktop lê pastas anexadas, mas não roda comandos. Por isso os dados são baixados antes, aqui, e cada pasta traz um `_LEIAME.md`.
Peça ao Claude Code: "atualize os dados do Meta" (ou rode o script de download). Depois anexe a pasta do cliente ao projeto dele no Claude Desktop e cole o conteúdo de `INSTRUCOES_CLAUDE_DESKTOP.md` nas instruções do projeto.
