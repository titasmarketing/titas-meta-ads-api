# Meta Marketing API: TITÃS Marketing

Acesso direto à API oficial da Meta (Graph API v26.0), sem MCP.

## Regras (valem para qualquer gestor que abrir esta pasta)
- `.env` (token): nunca imprimir, commitar, colar em chat ou enviar a terceiros. Para conferir, mostre só o nome da variável.
- Somente leitura por padrão. Alterar conta de cliente (criar, pausar ou editar campanha, orçamento, público) só depois de mostrar exatamente o que vai mudar e o gestor confirmar aquela ação.
- Dados baixados ficam em `dados/` (ignorado pelo git; são dados de clientes). Não enviar para serviços externos.
- Cada gestor usa o próprio token. Nunca reutilizar o de outra pessoa.

## Como rodar
`uv run --python 3.12 --with-requirements requirements.txt python scripts/varredura_conta.py ID_DA_CONTA` (retomável; `--refazer` baixa de novo).

## Detalhes técnicos
- O app está no nível Limited access: limite de chamadas baixo por conta. Evite varreduras repetidas sem necessidade.
- O script só precisa de META_ACCESS_TOKEN e META_API_VERSION. App ID e App Secret não são necessários para uso diário.

## Dados para análise no Claude Desktop
- Os gestores analisam cada cliente no Claude Desktop (um projeto por cliente). Ele lê as pastas anexadas, mas NÃO roda comandos. Quem mantém `dados/` atualizado é você (Claude Code).
- Pedido "atualize os dados" / "baixe os dados da conta X": rode `uv run --python 3.12 --with-requirements requirements.txt python scripts/baixar_todas_contas.py [--conta ID]` (retomável; `--refazer` baixa de novo), confira o `_LEIAME.md` gerado e diga ao gestor qual pasta anexar (`dados/<id_da_conta>`).
- Se o Claude Desktop pediu um dado que não existe: crie um script somente leitura em `scripts/`, rode você mesmo, grave em `dados/` e atualize o `_LEIAME.md`.
- Nunca peça ao gestor para rodar comandos: você tem o terminal. O texto de instruções do projeto no Claude Desktop está em `INSTRUCOES_CLAUDE_DESKTOP.md`.
