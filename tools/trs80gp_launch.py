"""Launch trs80gp with a valid macOS application context and writable cwd."""
from __future__ import annotations

import os
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Sequence


def run(command: Sequence[str], *, cwd: Path, timeout: int,
        check: bool = True) -> subprocess.CompletedProcess:
    """Run one batch command, using LaunchServices for a macOS app bundle."""
    invocation = [str(item) for item in command]
    executable = Path(invocation[0]).resolve()
    if (sys.platform != "darwin" or
            os.environ.get("BETTERCPM_TRS80GP_DIRECT") == "1" or
            executable.parent.name != "MacOS" or
            executable.parent.parent.parent.suffix != ".app"):
        return subprocess.run(invocation, cwd=cwd, check=check, timeout=timeout)

    cwd = Path(cwd).resolve()
    with tempfile.TemporaryDirectory(prefix="bettercpm-trs80gp-launch-") as temp:
        temporary = Path(temp)
        contents = temporary / "BetterCPM-trs80gp.app/Contents"
        (contents / "MacOS").mkdir(parents=True)
        (contents / "Info.plist").write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>run</string>
<key>CFBundleIdentifier</key><string>org.bettercpm.trs80gp-launcher</string>
<key>CFBundleName</key><string>BetterCPM trs80gp launcher</string>
<key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
""", encoding="utf-8")
        launcher = contents / "MacOS/run"
        launcher.write_text(
            "#!/bin/zsh\nset -e\n"
            "cd \"${BETTERCPM_TRS80_WORKDIR:?missing test work directory}\"\n"
            "args=(\"${(@f)$(<\"${BETTERCPM_TRS80_ARGS:?missing argument file}\")}\")\n"
            "print -r -- $$ > \"${BETTERCPM_TRS80_PIDFILE:?missing PID file}\"\n"
            f"exec {shlex.quote(str(executable))} \"${{args[@]}}\"\n",
            encoding="utf-8")
        launcher.chmod(0o755)
        argument_file = temporary / "arguments.txt"
        if any("\n" in argument for argument in invocation[1:]):
            raise ValueError("trs80gp argument contains a newline")
        argument_file.write_text("\n".join(invocation[1:]) + "\n", encoding="utf-8")
        pid_file = temporary / "pid"
        launched = ["/usr/bin/open", "-n",
                    "--env", f"BETTERCPM_TRS80_WORKDIR={cwd}",
                    "--env", f"BETTERCPM_TRS80_ARGS={argument_file}",
                    "--env", f"BETTERCPM_TRS80_PIDFILE={pid_file}",
                    str(contents.parent)]
        subprocess.run(launched, check=True, timeout=10)
        deadline = time.monotonic() + timeout
        while not pid_file.is_file():
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(invocation, timeout)
            time.sleep(0.02)
        pid = int(pid_file.read_text(encoding="ascii"))
        while True:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return subprocess.CompletedProcess(invocation, 0)
            if time.monotonic() >= deadline:
                os.kill(pid, signal.SIGTERM)
                for _ in range(50):
                    time.sleep(0.02)
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        break
                else:
                    os.kill(pid, signal.SIGKILL)
                raise subprocess.TimeoutExpired(invocation, timeout)
            time.sleep(0.05)
