# HANDOVER.md

Överlämning mellan agenter och sessioner. Läs innan du börjar, uppdatera innan du slutar.

## Aktuellt läge

*Senast inventerat 2026-11-04 av Claude (Cowork).*

Projekt: An SSH emulator that simulates OpenGear console servers with connected Cisco and Garderos devices for testing and development.

- Huvudbranch: `main`
- Senaste commit på `main`: 2026-11-01 `ff70b2d` Add privacy-guard scanning and mask private addresses (#2)
- Öppna PR:er: 0
- Andra brancher på remote: 2

## Pågående arbete

| Agent/vem | Branch | Status | Beskrivning |
|-----------|--------|--------|-------------|
| Cursor | `cursor/privacy-guard-7f51` | branch utan PR, senaste commit 2026-11-01 | Add privacy-guard scanning and mask private addresses |
| Cursor | `cursor/emulator-module-entry-be83` | branch utan PR, senaste commit 2026-10-16 | Add the emulator module entry point |

## Nästa steg

- Gå igenom brancher utan PR: öppna PR, merga eller radera (fråga användaren innan radering).
- Fyll på "Bygga och testa" i AGENTS.md om något saknas eller är fel.

## Kända problem

- Inga dokumenterade ännu.

## Senaste commits

- 2026-11-01 `ff70b2d` Add privacy-guard scanning and mask private addresses (#2)
- 2026-10-26 `39252cd` feat: mark busy ports in the pmshell listing
- 2026-10-26 `6c395cf` feat: add --check-config dry run
- 2026-10-26 `8d5ad9d` docs: add AGENTS.md contributor guide
- 2026-10-26 `99c6188` docs: correct the README against the current code
- 2026-10-26 `e024a1e` docs(examples): rename the asyncssh example and fix its run command
- 2026-10-26 `2a01ab3` chore: remove dead build files and stale ignore rules
- 2026-10-26 `efda721` ci: install dev requirements and always run the test suite
- 2026-10-26 `c1df066` test: run emulator tests against a real ephemeral server
- 2026-10-26 `5310ab1` fix: make ruff check pass

## Logg

| Datum | Agent | Vad som gjordes |
|-------|-------|-----------------|
| 2026-11-04 | Claude (Cowork) | Lade till AGENTS.md, HANDOVER.md och CLAUDE.md; inventerade PR:er, brancher och commits. |
