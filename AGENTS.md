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
