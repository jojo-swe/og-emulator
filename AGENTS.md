# AGENTS.md

## What it is

An asyncssh-based SSH server that emulates an OpenGear console server with
pmshell and three downstream device personalities (OpenGear, Cisco, Garderos).

## Run

```bash
pip install -r requirements-dev.txt
python -m emulator [--port N] [--config FILE] [--debug]
docker compose up --build
```

## Test and lint

- `pytest` (config in `pytest.ini`, `asyncio_mode = auto`)
- `ruff check .` (rules pinned in `pyproject.toml`)
- Both must pass before a PR; CI runs them on Python 3.11 and 3.12.

## Layout

- `__main__.py` (repo root): the real CLI, config loading and merging.
- `emulator/__main__.py`: thin shim so `python -m emulator` runs the root CLI.
- `core/ssh_server.py`: `DeviceManager`, the `SSHSession` state machine
  (`opengear` → `pmshell` → `device`), `SSHServer`, `create_ssh_server`.
- `devices/`: `BaseDevice`, `DeviceFactory`, one module per device type
  registered with `@register_device("name")`.
- `config/default_config.json`: shipped default configuration.
- `tests/`: pytest suite; `tests/test_emulator.py` runs a real server on port 0.

## Adding a device

1. Subclass `BaseDevice` and decorate it with `@register_device("name")`.
2. Implement `connect`, `disconnect` and `execute_command`.
3. Import the module in `devices/factory.py` next to the existing ones.
4. Add a device entry to the config and a test.

## Conventions

- Output lines written to the channel end with `\r\n`.
- Never print secrets; passwords are masked in logs.
- Keep `ssh_host_key` (and any generated key) out of git.
- The CLI path reads JSON config only.

## Known dead code, do not build on it

- `core/config.py` and `core/manager.py`: INI-based, broken relative import,
  unawaited coroutine.
- Root `__init__.py` lazy loader.
- `utils/logging.py`.

## Privacy / Integritet

Inga privata uppgifter får committas, och de får inte stå i PR-text (titel, beskrivning eller kommentar). Det gäller:

- personlig e-post — använd GitHubs noreply-adress i stället
- telefonnummer
- postadresser och hemadresser
- namn på privatpersoner
- interna IP-adresser
- Tailscale-värdnamn
- användarnamn i sökvägar
- nycklar och tokens
- innehåll i `.env`

Kör `pre-commit install` lokalt så att gitleaks granskar staged ändringar mot `.gitleaks.toml` före varje commit.

Agenter som hittar privata uppgifter maskerar dem med platshållare och skriver aldrig ut själva värdet i en commit, en pull request eller en logg. Använd till exempel `<email>`, `<user>`, `192.168.x.y`, `10.x.y.z`, `100.64.0.x` och `<host>.ts.net`.

---

<!-- agents-handover:rules -->
## Gemensamma agentregler (multi-agent)
Gemensamma regler för alla AI-agenter (Claude Code, Codex, molnagenter m.fl.) som arbetar i det här repot.
Flera agenter kan jobba här parallellt – utgå alltid från att någon annan kan ha pågående arbete.

### Innan du börjar

1. **Läs `HANDOVER.md`** – aktuellt läge, pågående arbete, nästa steg och kända problem.
2. **Kolla läget i git:**
   ```sh
   git status
   git fetch --all --prune
   git branch -a
   gh pr list --state open
   ```
3. **Gör inte om något som redan pågår.** Finns det en öppen PR, en aktiv branch eller en rad under
   "Pågående arbete" i `HANDOVER.md` som rör samma sak – bygg vidare på den eller fråga användaren.
4. Har arbetskatalogen ocommittade ändringar som inte är dina: rör dem inte. Använd en egen
   `git worktree` eller fråga användaren.

### Under arbetet

- **En branch per uppgift**, namnformat: `agent/<verktyg>/<kort-beskrivning>`
  (t.ex. `agent/claude/fix-login-timeout`, `agent/codex/add-csv-export`).
- Registrera ditt arbete under "Pågående arbete" i `HANDOVER.md` tidigt (agent, branch, status).
- **Committa ofta** med tydliga meddelanden.
- **Fråga alltid användaren innan destruktiva git-kommandon:** `push --force`, `reset --hard`,
  `clean -fd`, radera brancher (lokalt eller remote), `rebase` av delade brancher, `checkout -- .`.

### Innan sessionen avslutas

- **Inget arbete får lämnas ocommittat.** Committa (vid behov som WIP) och **pusha alltid** din branch.
- **Uppdatera `HANDOVER.md`:** aktuellt läge, pågående arbete, nästa steg, kända problem och en ny rad
  i loggen (datum, agent, vad som gjordes).
- Om repot saknar `AGENTS.md` eller `HANDOVER.md`: skapa dem från mallen
  (https://github.com/jojo-swe/repo-template) innan du börjar.

### Repo-specifikt (autodetekterat 2026-11-04)

#### Bygga och testa

- Installera: `python -m venv .venv` och `pip install -r requirements.txt`
- Test: `pytest`
- Docker: `docker compose up`
- CI: GitHub Actions (`ci.yml`, `privacy-guard.yml`)

#### Struktur

- `.github/` (2 filer)
- `config/` (2 filer)
- `core/` (4 filer)
- `devices/` (6 filer)
- `docs/` (2 filer)
- `emulator/` (2 filer)
- `examples/` (2 filer)
- `scripts/` (1 filer)
- `tests/` (5 filer)
- `utils/` (3 filer)
- Filer i roten: `.dockerignore`, `.gitignore`, `.gitleaks.toml`, `.pre-commit-config.yaml`, `__init__.py`, `__main__.py`, `AGENTS.md`, `compose.yaml`, `Dockerfile`, `LICENSE`, `pyproject.toml`, `pytest.ini`, `README.md`, `requirements-dev.txt`, `requirements.txt` …

#### Övrigt

<!-- Konventioner, miljövariabler, deploy, saker agenter ska undvika. -->
