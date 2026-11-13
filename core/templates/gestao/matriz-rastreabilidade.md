# Matriz de Rastreabilidade

Artefato único de rastreabilidade do projeto, registrando entregas, issues, turnos, PRs e arquivos tocados.

## Como manter esta matriz

- **Quem atualiza:** o Dev Especialista do turno, a cada abertura e fechamento de tarefa (`T<turno>.<n>` ou turno de tarefa única).
- **Coluna "Arquivos tocados":** é a base para o Tech Lead conferir independência entre tarefas do mesmo turno.
- **Linhas novas:** uma por entrega relevante (issue fechada, PR mergeado ou documentação entregue por Autoridade Delegada).

## Template para nova linha

```markdown
| `<Épico>` | [#<issue>](https://github.com/usuario/repo/issues/<issue>) | Turno `<N>`<br>`T<N>.<n>` | PR #<n> / Commits diretos | `<arquivo1>`, `<arquivo2>` | `pytest` `<x>/<x>` | ✅ Concluído / 🔄 Em andamento / ⏸️ Adiado |
```

## Histórico de Entregas

| Épico | Issue | Turno / Tarefa | PR | Arquivos tocados | Testes | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
