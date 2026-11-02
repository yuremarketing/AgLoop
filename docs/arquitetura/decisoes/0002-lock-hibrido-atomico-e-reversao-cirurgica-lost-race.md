# ADR 0002: Lock Híbrido Atômico (`.agloop.lock`) e Reversão Cirúrgica em `lost_race`

- **Status:** Aceita
- **Data:** 2026-10-22 (Commit `2e5cc85` / [Issue #1](https://github.com/yuremarketing/AgLoop/issues/1))
- **Decisores:** Yure Mark (PO), Claude, Gemini

---

## Contexto e Problema

Na versão inicial do `GitLock` (`core/git_lock.py`), existiam três fragilidades críticas para uso em ambientes reais onde múltiplos agentes ou desenvolvedores humanos compartilham o mesmo repositório:
1. O commit utilizava `git add -A`, arriscando incluir arquivos de código inacabados ou sensíveis no commit de IPC da Sala de Guerra.
2. Quando um agente perdia a corrida de `git push` para outro agente remoto, o código executava `git reset --hard HEAD~1`, **destruindo alterações não commitadas** em outros arquivos da working tree.
3. Agentes rodando na mesma máquina não possuíam exclusão mútua local antes de invocar operações Git, e um crash de processo poderia deixar um lock órfão eternamente.

## Decisão

Implementar em `core/git_lock.py` o **Lock Híbrido em Duas Camadas com Segurança de Working Tree**:
1. **Lock Local Atômico via Diretório (`.agloop.lock/`):**
   - Usa `os.mkdir(".agloop.lock")` (operação atômica em sistemas POSIX/NTFS) e grava `owner.json` contendo `{"pid": ..., "host": ..., "ts": ...}`.
   - **Recuperação de Stale Lock (`_lock_is_stale`):** Se o `host` registrado for a máquina local (`socket.gethostname()`), verifica imediatamente se o processo ainda existe via `os.kill(pid, 0)`. Se o PID morreu, quebra o lock na hora sem esperar timeout. Para processos remotos ou travados, aplica o teto configurável `AGLOOP_LOCK_TIMEOUT` (default `300s`).
2. **Commits Estritamente Escopados (`git commit -- <paths>`):**
   - `GitLock.commit()` adiciona e commita exclusivamente os caminhos explícitos da Sala de Guerra (`war_room.md`), ignorando qualquer outro arquivo modificado ou *staged* no índice compartilhado.
3. **Abolição de `reset --hard` e Resolução Cirúrgica de `lost_race` (`_resolve_lost_race`):**
   - Se o `git push` é rejeitado (`non-fast-forward`) e o rebase conflita na Sala de Guerra (outro agente respondeu primeiro), o `GitLock` aborta o rebase, desfaz apenas o commit local com `git reset --soft HEAD~1`, restaura cirurgicamente somente os arquivos da Sala de Guerra (`git checkout HEAD -- <paths>`) e avança para `origin/main` mantendo 100% dos demais arquivos da working tree intactos.

## Consequências

### Positivas
- Elimina 100% do risco de perda de código em andamento na working tree compartilhada (Risco `R02` mitigado).
- Recuperação instantânea de crashes locais via checagem de PID e proteção contra deadlocks via timeout de 300s (Risco `R03` mitigado).
- Cobertura integral por testes automatizados em `tests/test_git_lock.py`.

### Negativas
- Quando um agente perde a corrida de push (`lost_race`), a resposta que ele havia acabado de formular para o estado antigo da Sala de Guerra é descartada para que ele reavalie o contexto atualizado pelo vencedor no próximo ciclo (comportamento desejado para manter coerência conversacional).
