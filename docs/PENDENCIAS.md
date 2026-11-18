# Pendências do repositório

Itens que a organização do repositório (Breno) deixou em aberto por depender de
informação ou de arquivos de outros membros. Remover cada item quando resolvido.

## Arquivos que ainda faltam

- [ ] **`.python-version`**: versão do Python usada pela equipe ainda não confirmada
      (perguntar ao Nataniel, que mantém o `pyproject.toml` e o `uv.lock`). Deve
      ser compatível com o `requires-python` do `pyproject.toml`.
- [ ] **`pyproject.toml` e `uv.lock`**: responsabilidade do Nataniel (ou de quem
      ele indicar). O README assume `uv sync` e `uv run python main.py`.
- [ ] **`.vscode/settings.json`**: vem do Nataniel; o `.gitignore` já o preserva.
- [ ] **`docs/fluxograma.svg`**: o Nataniel vai subir. O README já aponta para ele.
- [ ] **`docs/fluxograma.png`**: exportar do `.svg` oficial depois que ele subir.
- [ ] Demais arquivos de `scripts/src/` (abas, `componentes.py`, `pipeline.py`,
      `registro.py`) e `scripts/analise_dataset.py`: cada dono sobe o seu. A janela
      principal só roda depois que todos entrarem.

## Decisões a confirmar com a equipe

- [ ] **Local do dataset:** o `dados/README.md` e o `.gitignore` assumem
      `dados/PCB_DATASET/`. Conferir se o `analise_dataset.py` (Bruno) usa esse caminho.
- [ ] **`dados/referencias/`:** o `.gitignore` ignora as imagens cadastradas e
      mantém só o `.gitkeep`. Se a equipe preferir versionar as 10 referências de
      `PCB_USED`, remover as duas últimas linhas da regra no `.gitignore`.
- [ ] **`resultados/`:** não está ignorada, para versionar as saídas da análise do
      dataset. Ignorar se preferirem manter só o código.

## Conteúdo do README a validar

- [ ] **GPU/CUDA:** o README descreve o estado atual (protótipo em Python/OpenCV)
      e trata a aceleração CUDA como próximo passo. Confirmar se isso reflete o código.
- [ ] **Status das funcionalidades (F1 a F7):** tabela baseada no vídeo de
      demonstração e no email de divisão de tarefas; cada dono deve conferir a sua.
- [ ] **Resultados/métricas:** a seção está preparada, mas as métricas contra as
      anotações (precisão, revocação, F1) só entram quando a avaliação for implementada.
