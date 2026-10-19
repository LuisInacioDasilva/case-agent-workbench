# Case Agent Workbench

Eu queria um exemplo de agente que tivesse trabalho de verdade, e não só dois prompts encadeados com uma resposta bonita. Aqui o caso passa por recuperação de conhecimento local, análise estruturada e revisão independente. A saída é um rascunho para uma pessoa decidir; a aplicação não envia mensagem, não altera pedido e não executa ferramenta com efeito externo.

## Ver funcionando sem pagar nada

Requisito: Python 3.10+. O modo inicial é uma **demonstração determinística**, não um LLM. Ela existe para visualizar o fluxo, rodar testes e avaliar os controles sem baixar modelo ou usar API paga.

```bash
python -m unittest discover -s tests -v
python -m app.evaluate
python -m app.server
```

Abra `http://127.0.0.1:8086`. Use os casos prontos ou escreva um caso **sintético**. A interface mostra categoria, resposta, fontes, trilha e a etapa de revisão humana. O servidor aceita conexões apenas em `127.0.0.1` e não persiste os casos.

## LLM local de verdade

Com [Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md) instalado e um modelo baixado, por exemplo `ollama pull qwen3:4b-instruct`:

```bash
# Linux/macOS
WORKBENCH_MODE=ollama OLLAMA_MODEL=qwen3:4b-instruct python -m app.server

# PowerShell
$env:WORKBENCH_MODE='ollama'; $env:OLLAMA_MODEL='qwen3:4b-instruct'; python -m app.server
```

O adaptador usa `POST http://127.0.0.1:11434/api/chat`, `stream: false` e schema JSON no campo `format`. O endpoint é fixo no loopback: texto do caso não escolhe URL, ferramenta ou destino. Não testei a qualidade desse modelo nesta máquina; a suíte automatizada cobre o fluxo com respostas controladas, não a precisão real de inferência. A qualidade precisa ser avaliada com o modelo e hardware escolhidos.

## Fluxo

1. `KnowledgeBase` recupera até dois documentos do corpus local por palavras normalizadas. É propositalmente simples e auditável; não se apresenta como busca semântica.
2. O agente analista recebe caso e evidências e responde no schema de categoria, rascunho, citações e revisão humana obrigatória.
3. O programa rejeita schema inválido, fonte inexistente, resposta vazia e tentativa de tirar a revisão humana.
4. O agente revisor avalia o rascunho. Um veto bloqueia a saída. Aprovação libera **apenas exibição**, nunca execução.

O corpus e os casos de avaliação são sintéticos. `data/evals.json` torna o comportamento esperado verificável; `tests/` cobre os casos, injeção de instruções, citações falsas, veto, indisponibilidade do modelo, limites de entrada e API HTTP. Há limites claros: um modelo pode citar um documento verdadeiro e ainda interpretar mal o texto. Para uso real, eu acrescentaria um conjunto maior de avaliações humanas, métricas de falso positivo e um processo de revisão antes de integrar qualquer ação.

`python -m app.evaluate` executa o corpus com o fluxo completo e gera `dist/evaluation.json`: taxa de aprovação e checks individuais de status, categoria, fonte e revisão humana. O relatório guarda somente o número do caso, sem copiar seu texto. `--mode ollama` permite rodar o mesmo conjunto contra um modelo local; não trato a taxa nesses poucos casos sintéticos como precisão de produção.

## Deploy, segurança e rollback

O projeto foi desenhado para execução local, não para expor a internet. Se for integrado a um sistema real, primeiro introduza autenticação, isolamento por usuário, política de retenção e observabilidade sem conteúdo sensível; só depois ferramentas externas com permissões mínimas e aprovação por ação. Não há schema nem migração. Rollback é parar o servidor e voltar ao commit anterior; nenhum dado é modificado fora da memória do processo.

---

<p align="center"><a href="https://github.com/LuisInacioDasilva"><img src="https://avatars.githubusercontent.com/u/88007376?v=4" width="82" height="82" alt="Foto de Luis da Silva" style="border-radius:50%"></a></p>
<p align="center"><strong>Desenvolvido por Luis da Silva</strong><br>Back-end, dados, integrações e automação em produção.</p>
