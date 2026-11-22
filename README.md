<div align="center">

# hermes-contributions-film

### What a global leading open source project looks like — measured, narrated, gated.

[![License: MIT](https://img.shields.io/badge/license-MIT-D4AF37?style=flat-square)](./LICENSE)
[![OpenSourceWare](https://img.shields.io/badge/%23opensourceware-yellow?style=flat-square)](https://github.com/MYaelMendez/hermes-contributions-film)
[![Derived](https://img.shields.io/badge/data-public%20REST-00eaff?style=flat-square)](./gen_org_activity.py)
[![Gate](https://img.shields.io/badge/gate-10%20invariants%20fail--closed-FFD755?style=flat-square)](./ae_lessons.py)

`æ://` · gold-on-void · derived, never hand-written · no credential on any surface.

</div>

---

> Una organización no expone `contributionsCollection` en GraphQL (verificado:
> `undefinedField` en tipo `Organization`). La verdad de un proyecto global está
> en `stats/commit_activity` + la lista de contribuidores. Este kit lo deriva,
> lo narra con voz local determinista y lo renderiza en GPU con gate.

## La historia real — NousResearch/hermes-agent

| Métrica | Valor (derivado, no escrito a mano) |
|---|---|
| Stars | **265,233** |
| Forks | **59,957** |
| Contribuidores | **6,625** (67 páginas × 100, contado por Link header) |
| Commits en 52 semanas | **80,146** |
| Semanas activas | 47 / 52 |
| Pico semanal | **9,113 commits** |
| Commits de comunidad (últimas 12 semanas) | **48,011** |
| Commits del owner (mismo periodo) | **0** |

**Ese último número es el titular**: el dueño escribió cero commits en las
últimas 12 semanas. La comunidad sostuvo el proyecto. Eso es open source
liderando a escala global.

## Quickstart

```bash
git clone https://github.com/MYaelMendez/hermes-contributions-film.git
cd hermes-contributions-film

# Película de cualquier repo público
python run.py --repo NousResearch/hermes-agent --out ./mi-film

# Prueba rápida (~16 s, 2 segmentos)
python run.py --repo NousResearch/hermes-agent --out ./smoke --quick
```

## Arquitectura

```text
GitHub REST (público)
  stats/commit_activity ─┐
  stats/participation  ──┼─→ gen_org_activity.py → org-activity.json (--check)
  contributors (Link)  ──┘            │
                                      ▼
                          make_voice.py (tiny-voca, seed 42)
                                      ▼
                          build_narration.py (apad, nunca -shortest)
                                      ▼
                          build_studio.py (__setTime determinista)
                                      ▼
                          render.mjs (CDP/RTX) → ffmpeg → MP4 + receipt
```

## Por qué es distinto del kit de usuario

Un usuario tiene `contributionsCollection` con días. Una **organización no**:
 GraphQL devuelve `undefinedField`. Este kit usa la señal correcta para una
 org — commits por semana y contribuidores — y separa explícitamente
 `community` de `owner`. Ningún número se inventa para rellenar el vacío.

## Executable lessons

Incluye `ae_lessons.py` con 10 invariantes fail-closed: voz < picture, frame
count exacto, sha cambiado, gate PASS, PCM real, contador = barras, fetch
relativo, `.then/.catch` intacto, sin credenciales, stage explícito.
Verificado: 10/10 con artifact real, 5/5 sabotajes rechazados.

## Seguridad

Solo datos públicos de REST. El token de `gh` no se escribe en ningún archivo.
Verificado con regex: `gh[pous]_*`, `Bearer`, `Authorization` → 0 coincidencias.

## Licencia

MIT · #opensourceware. Úsalo, fórcalo, mejóralo.
