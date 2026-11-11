# ADR 0006: Distribuição Segura: Repositório Público, Branch `stable` e PyPI como Canal Oficial

- **Status:** Proposta (aguardando decisão do PO, [Issue #56](https://github.com/yuremarketing/AgLoop/issues/56), Turno 34)
- **Data:** 2026-11-11 (Turno 34)
- **Decisores:** Yure Mark (PO); recomendação de Claude (Dev Especialista) e Gemini (Tech Lead); redação de Claude-Cloud (Documentação)

---

## Contexto e Problema

O AgLoop é obtido hoje por três canais, e só um é controlado:

1. **PyPI** (`pip install agloop`): versões fechadas, publicadas só por Release via Trusted Publishing (`publish.yml`). É a fonte usada pelo aviso de versão e pelo `agloop update` (Issue #54).
2. **Git direto** (`pip install git+https://github.com/yuremarketing/AgLoop`): instala a `main` daquele momento, possivelmente no meio de um turno e sem versão rastreável. Recomendado no README e no Manual por falta de Release recente.
3. **Plugin do Claude Code e extensão do Gemini**: instalados a partir da branch padrão do repositório (`main`).

O PO considerou a instalação via Git insegura e levantou a hipótese de tornar o repositório privado.

## Opções Consideradas

| Opção | Resolve o risco? | Custo / efeito colateral |
| :--- | :--- | :--- |
| **A. Repositório privado** | Sim, para terceiros | Quebra o plugin (`/plugin marketplace add`) e a extensão (`gemini extensions install`) para terceiros; documentação e issues deixam de ser públicas; incoerente com a licença MIT; CI passa a consumir minutos pagos (9 jobs por PR, incluindo macOS e Windows). |
| **B. Híbrido** (público para distribuição + privado para desenvolvimento) | Sim | Dois repositórios, CI duplicado, sincronização de releases e Sala de Guerra fragmentada. |
| **C. Público + canais apontando para versões fechadas** (recomendada) | Sim | Uma etapa nova no workflow de release; documentação atualizada após o Release 0.8.0. |

## Decisão Proposta (Opção C)

1. **Repositório permanece público**, coerente com a licença MIT e com CI gratuito.
2. **PyPI como canal oficial do pacote:** após o Release 0.8.0, README e Manual deixam de recomendar `pip install git+...`; fica só `pip install agloop`. `pip install -e .` permanece apenas em uma seção "Para contribuidores".
3. **Branch `stable`** avançada **somente pela automação de release** (`publish.yml`, após a publicação no PyPI), sempre por fast-forward até o commit da tag. Plugin e extensão passam a instalar dela:
   - Claude Code: `/plugin marketplace add yuremarketing/AgLoop#stable`
   - Gemini CLI: `gemini extensions install https://github.com/yuremarketing/AgLoop --ref=stable`
4. **Sequência:** (a) Release 0.8.0 com autorização específica do PO; (b) PR com a etapa `stable` no `publish.yml`, com autorização do PO por tocar automação de release; (c) atualização de README e Manual.

## Consequências

### Positivas
- Ninguém instala código no meio de um turno: só versões publicadas pelo PO.
- O plugin, a extensão e a documentação pública continuam funcionando para a comunidade.
- A documentação não precisa ser editada a cada versão (`stable` avança sozinha).
- Sem custo adicional de CI.

### Negativas / Riscos
- Não é possível **impedir** instalações via Git num repositório público, apenas deixar de recomendá-las.
- A branch `stable` depende do workflow de release: falha nessa etapa deixa a `stable` atrás da última versão (mitigação: o Checklist Pós-Release, Seção 9 do `SKILL.md`, confere a `stable`).

## Decisão do PO

> _Pendente._ Registrar aqui a resposta literal do PO (opção escolhida, data e hora) e mudar o Status para "Aceita" ou "Rejeitada".
