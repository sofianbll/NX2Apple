#!/usr/bin/env python3
"""Recette du cycle de vie de l'app construite, sans toucher aux autres processus."""

import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.request

PORT = 8767
BUNDLE_ID = "local.nxnative.dashboard"
WITNESS_SESSION = "nxnative-app-test-witness"
APP_BINARY_SUFFIX = "/NXNative Dashboard.app/Contents/MacOS/NXNativeDashboard"
CONFLICT_TEXT = "Le port 8767 est déjà utilisé"


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def command(*args, timeout=10):
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)


def ps_rows():
    result = command("/bin/ps", "-axo", "pid=,ppid=,args=")
    check(result.returncode == 0, result.stderr)
    rows = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) == 3:
            rows.append((int(fields[0]), int(fields[1]), fields[2]))
    return rows


def pid_alive(pid):
    result = command("/bin/ps", "-p", str(pid), "-o", "stat=")
    return result.returncode == 0 and bool(result.stdout.strip()) and not result.stdout.strip().startswith("Z")


def parent_pid(pid):
    for row_pid, parent, _ in ps_rows():
        if row_pid == pid:
            return parent
    return None


def app_pids(binary):
    matches = []
    for pid, _, args in ps_rows():
        if args == str(binary) or args.startswith(str(binary) + " "):
            matches.append(pid)
    return matches


def listener_pids():
    result = command(
        "/usr/sbin/lsof", "-nP", f"-iTCP:{PORT}", "-sTCP:LISTEN", "-t"
    )
    if result.returncode == 1 and not result.stdout.strip():
        return []
    check(result.returncode == 0, result.stderr)
    return sorted({int(line) for line in result.stdout.split()})


def port_accepts_connections():
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", PORT)) == 0


def wait_until(description, predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    raise RuntimeError(f"Délai dépassé : {description}")


def wait_for_new_app(binary, before):
    new_pid = None

    def find_new():
        nonlocal new_pid
        new = set(app_pids(binary)) - before
        if len(new) == 1:
            new_pid = new.pop()
            return True
        return False

    wait_until("nouvelle instance de l'app", find_new, 10)
    return new_pid


def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=2) as response:
        body = response.read()
        check(response.status == 200, f"GET {path} → {response.status}")
        return body


def assert_server(app_pid, server_pid):
    check(pid_alive(app_pid), "L'app n'est plus vivante")
    check(pid_alive(server_pid), "Le serveur n'est plus vivant")
    check(listener_pids() == [server_pid], "Le listener 8767 n'est pas le serveur attendu")
    check(parent_pid(server_pid) == app_pid, "Le listener n'est pas un enfant direct de l'app")


def wait_for_server(app_pid):
    server_pid = None

    def ready():
        nonlocal server_pid
        listeners = listener_pids()
        if len(listeners) == 1 and parent_pid(listeners[0]) == app_pid:
            server_pid = listeners[0]
            return True
        return False

    wait_until("listener enfant de l'app", ready, 20)
    wait_until("GET /status", lambda: get("/status") is not None, 5)
    return server_pid


def window_text(pid):
    script = r'''
on textFromElement(uiElement)
    set textResult to ""
    tell application "System Events"
        try
            set elementValue to value of uiElement
            if class of elementValue is not list then set textResult to elementValue as text
        end try
        try
            set children to UI elements of uiElement
            repeat with childElement in children
                set textResult to textResult & linefeed & my textFromElement(childElement)
            end repeat
        end try
    end tell
    return textResult
end textFromElement

tell application "System Events"
    set targetProcess to missing value
    set candidateProcesses to every process whose bundle identifier is "BUNDLE_ID_PLACEHOLDER"
    repeat with candidateProcess in candidateProcesses
        try
            if (unix id of candidateProcess) is PID_PLACEHOLDER then
                set targetProcess to candidateProcess
                exit repeat
            end if
        end try
    end repeat
    if targetProcess is missing value then return ""
    if (count windows of targetProcess) is 0 then return ""
    return ("PID=" & (unix id of targetProcess) & linefeed & my textFromElement(window 1 of targetProcess))
end tell
'''.replace("PID_PLACEHOLDER", str(pid)).replace("BUNDLE_ID_PLACEHOLDER", BUNDLE_ID)
    return command("/usr/bin/osascript", "-e", script, timeout=5)


def assert_conflict_visible(pid):
    deadline = time.monotonic() + 12
    last_result = None
    while time.monotonic() < deadline:
        check(pid_alive(pid), "L'app s'est terminée au lieu d'afficher le conflit")
        last_result = window_text(pid)
        if (last_result.returncode == 0
                and last_result.stdout.startswith(f"PID={pid}\n")
                and CONFLICT_TEXT in last_result.stdout):
            return
        time.sleep(0.2)
    detail = ""
    if last_result is not None:
        detail = f" ; dernière lecture UI : {last_result.stdout} {last_result.stderr}"
    raise RuntimeError("Le conflit de port n'est pas visible" + detail)


def quit_app(pid):
    result = command(
        "/usr/bin/osascript", "-e", f'quit app id "{BUNDLE_ID}"', timeout=10
    )
    check(result.returncode == 0, f"Quitter par AppleScript : {result.stderr}")
    wait_until("arrêt de l'app après Quitter", lambda: not pid_alive(pid), 8)


def terminate_pid(pid, sig=signal.SIGTERM):
    if pid_alive(pid):
        os.kill(pid, sig)


def stop_owned_process(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def run(app_bundle):
    binary = app_bundle / "Contents/MacOS/NXNativeDashboard"
    check(binary.is_file(), f"App absente : {app_bundle}")

    # Cette vérification précède toute création de processus ou de session.
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", PORT))
        except OSError as error:
            raise RuntimeError(f"Le port {PORT} est déjà utilisé ; abandon sans action : {error}")
    check(not listener_pids() and not port_accepts_connections(), f"Le port {PORT} est déjà utilisé")
    other_apps = [pid for pid, _, args in ps_rows() if APP_BINARY_SUFFIX in args]
    check(not other_apps, f"Une instance NXNative Dashboard tourne déjà : {other_apps}")
    check(command("tmux", "has-session", "-t", WITNESS_SESSION).returncode != 0,
          f"La session témoin {WITNESS_SESSION} existe déjà")

    tracked_apps = set()
    owned_servers = set()
    fake = None
    detached = None
    tmux_created = False

    def launch(new=False):
        before = set(app_pids(binary))
        args = ["/usr/bin/open"]
        if new:
            args.append("-n")
        args.append(str(app_bundle))
        result = command(*args)
        check(result.returncode == 0, f"open : {result.stderr}")
        pid = wait_for_new_app(binary, before)
        tracked_apps.add(pid)
        return pid

    def launch_ready():
        pid = launch()
        server_pid = wait_for_server(pid)
        owned_servers.add(server_pid)
        assert_server(pid, server_pid)
        return pid, server_pid

    def assert_witnesses(label):
        check(command("tmux", "has-session", "-t", WITNESS_SESSION).returncode == 0,
              f"Session tmux témoin absente après {label}")
        check(detached is not None and detached.poll() is None,
              f"Processus détaché témoin absent après {label}")

    try:
        result = command("tmux", "new", "-d", "-s", WITNESS_SESSION, "sleep", "600")
        check(result.returncode == 0, f"Création du témoin tmux : {result.stderr}")
        tmux_created = True
        detached = subprocess.Popen(
            ["/usr/bin/nohup", "/bin/sleep", "600"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        assert_witnesses("leur création")

        app_pid, server_pid = launch_ready()
        check(b"<html" in get("/").lower(), "La page du dashboard ne répond pas en HTML")
        get("/status")
        assert_server(app_pid, server_pid)
        print("PASS ouverture : listener enfant, page et GET /status 200")
        quit_app(app_pid)
        wait_until("serveur arrêté après Quitter", lambda: not pid_alive(server_pid), 5)
        wait_until("port libre après Quitter", lambda: not listener_pids() and not port_accepts_connections(), 5)
        assert_witnesses("Quitter")
        print("PASS Quitter : serveur arrêté et port libre")

        app_pid, server_pid = launch_ready()
        terminate_pid(app_pid, signal.SIGKILL)
        killed_at = time.monotonic()
        wait_until("arrêt de l'app après SIGKILL", lambda: not pid_alive(app_pid), 2)
        wait_until("serveur arrêté après SIGKILL", lambda: not pid_alive(server_pid), 5)
        check(time.monotonic() - killed_at <= 5, "Le serveur a survécu plus de 5 s au SIGKILL")
        wait_until("port libre après SIGKILL", lambda: not listener_pids() and not port_accepts_connections(), 1)
        assert_witnesses("SIGKILL")
        print("PASS SIGKILL : serveur arrêté en moins de 5 s")

        fake_code = (
            "import socket\n"
            "s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n"
            f"s.bind(('127.0.0.1',{PORT})); s.listen()\n"
            "while True:\n"
            " c,_=s.accept(); c.close()\n"
        )
        fake = subprocess.Popen(
            [sys.executable, "-c", fake_code],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        wait_until("faux listener", lambda: listener_pids() == [fake.pid], 3)
        app_pid = launch()
        assert_conflict_visible(app_pid)
        check(fake.poll() is None and listener_pids() == [fake.pid], "Le faux serveur a été perturbé")
        assert_witnesses("le conflit de port")
        quit_app(app_pid)
        check(fake.poll() is None and listener_pids() == [fake.pid], "Quitter a arrêté le faux serveur")
        stop_owned_process(fake)
        wait_until("port libre après arrêt du faux listener", lambda: not listener_pids(), 3)
        print("PASS conflit : message visible et faux listener intact")

        first_pid, first_server = launch_ready()
        second_pid = launch(new=True)
        assert_server(first_pid, first_server)
        assert_conflict_visible(second_pid)
        assert_server(first_pid, first_server)
        get("/status")
        assert_witnesses("la seconde instance")
        terminate_pid(second_pid, signal.SIGTERM)
        wait_until("arrêt de la seconde instance", lambda: not pid_alive(second_pid), 3)
        assert_server(first_pid, first_server)
        quit_app(first_pid)
        wait_until("serveur de la première instance arrêté", lambda: not pid_alive(first_server), 5)
        wait_until("port libre final", lambda: not listener_pids() and not port_accepts_connections(), 5)
        assert_witnesses("le nettoyage de la seconde instance")
        print("PASS seconde instance : conflit visible, premier serveur intact")
        print("PASS témoins : session tmux et processus détaché vivants après chaque cas")
    finally:
        for pid in sorted(tracked_apps):
            terminate_pid(pid)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and any(pid_alive(pid) for pid in tracked_apps):
            time.sleep(0.1)
        for pid in sorted(tracked_apps):
            terminate_pid(pid, signal.SIGKILL)

        # Seuls les serveurs dont ce test a vérifié la filiation sont concernés.
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and any(pid_alive(pid) for pid in owned_servers):
            time.sleep(0.1)
        for pid in sorted(owned_servers):
            terminate_pid(pid)
        stop_owned_process(fake)
        stop_owned_process(detached)
        if tmux_created:
            command("tmux", "kill-session", "-t", WITNESS_SESSION)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage : {sys.argv[0]} '/chemin/NXNative Dashboard.app'")
    try:
        run(Path(sys.argv[1]).resolve())
    except Exception as error:
        print(f"ÉCHEC app-test : {error}", file=sys.stderr)
        raise SystemExit(1)
