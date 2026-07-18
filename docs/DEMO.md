# Five-minute demo

This walkthrough demonstrates how `og-emulator` can provide a disposable OpenGear-style console lab for development, CI, and integration testing.

## 1. Start the lab

```bash
docker compose up --build -d
```

Confirm that the service is healthy:

```bash
docker compose ps
```

## 2. Connect over SSH

```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  admin@localhost -p 2222
```

The default password is `admin`.

## 3. Explore the console server

At the OpenGear-style prompt, list available console ports:

```text
pmshell
```

Select a device, or connect directly:

```text
pmshell -l port02
```

Run device commands such as:

```text
show version
show running-config
```

Return to the console server with:

```text
exit
```

## 4. Use it in automation tests

Point SSH-based test clients at:

```text
host: localhost
port: 2222
username: admin
password: admin
```

The emulator is useful for validating prompt handling, pmshell navigation, command parsing, timeout behavior, and multi-device workflows without access to physical console servers.

## 5. Stop and remove the lab

```bash
docker compose down
```

## Portfolio talking points

- Implements a real SSH service rather than mocking a client library.
- Models a stateful console-server workflow and downstream device sessions.
- Uses an extensible device factory for multiple network-device personalities.
- Runs reproducibly in containers and is validated through GitHub Actions.
- Enables hardware-independent development of network automation software.
