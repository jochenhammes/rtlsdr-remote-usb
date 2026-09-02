#!/usr/bin/env python3
"""Hält eine USB/IP-Verbindung zu einem entfernten RTL-SDR-Dongle aufrecht.

Findet den Dongle auf dem konfigurierten Server automatisch (per
Vendor:Product-ID), attached ihn lokal via `usbip attach`, überwacht die
Verbindung und attached bei einem Abbruch automatisch neu (exponentielles
Backoff).

Konfiguration über Umgebungsvariablen (siehe config.example.env):
  RTLSDR_SERVER_HOST   Hostname/IP des USB/IP-Servers (Pflicht)
  RTLSDR_BUSID         Feste busid statt Auto-Discovery (optional)
  RTLSDR_POLL_INTERVAL Sekunden zwischen Verbindungsprüfungen (Default: 5)
  RTLSDR_MAX_BACKOFF   Maximales Backoff in Sekunden (Default: 60)
"""
from __future__ import annotations

import logging
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass

LOG = logging.getLogger("rtlsdr-usbip-watchdog")

# Bekannte Vendor:Product-IDs für RTL2832U-basierte RTL-SDR-Dongles.
KNOWN_RTLSDR_IDS = {"0bda:2832", "0bda:2838"}

USBIP_BIN = os.environ.get("RTLSDR_USBIP_BIN", "usbip")


class UsbipError(RuntimeError):
    pass


@dataclass
class Config:
    server_host: str
    busid: str | None
    poll_interval: float
    max_backoff: float

    @classmethod
    def from_env(cls) -> "Config":
        server_host = os.environ.get("RTLSDR_SERVER_HOST")
        if not server_host:
            raise SystemExit("RTLSDR_SERVER_HOST muss gesetzt sein.")
        return cls(
            server_host=server_host,
            busid=os.environ.get("RTLSDR_BUSID") or None,
            poll_interval=float(os.environ.get("RTLSDR_POLL_INTERVAL", "5")),
            max_backoff=float(os.environ.get("RTLSDR_MAX_BACKOFF", "60")),
        )


def run_usbip(*args: str) -> subprocess.CompletedProcess:
    cmd = [USBIP_BIN, *args]
    LOG.debug("Ausführen: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True)


# 'usbip list -r <host>' Ausgabeformat (Auszug):
#
#  - busid 1-1.4 (0bda:2838)
#     Realtek Semiconductor Corp. : RTL2838 DVB-T
#
_LIST_ENTRY_RE = re.compile(
    r"^\s*-\s*busid\s+(?P<busid>\S+)\s+\((?P<vidpid>[0-9a-fA-F]{4}:[0-9a-fA-F]{4})\)",
    re.MULTILINE,
)


def discover_busid(server_host: str) -> str:
    """Findet die busid des ersten RTL-SDR-Dongles auf dem Server."""
    result = run_usbip("list", "-r", server_host)
    if result.returncode != 0:
        raise UsbipError(
            f"'usbip list -r {server_host}' fehlgeschlagen: {result.stderr.strip()}"
        )
    return find_rtlsdr_busid(result.stdout)


def find_rtlsdr_busid(usbip_list_output: str) -> str:
    """Parst 'usbip list -r'-Output und gibt die erste passende busid zurück."""
    candidates = [
        (m.group("busid"), m.group("vidpid").lower())
        for m in _LIST_ENTRY_RE.finditer(usbip_list_output)
    ]
    for busid, vidpid in candidates:
        if vidpid in KNOWN_RTLSDR_IDS:
            return busid
    raise UsbipError(
        "Kein RTL-SDR-Dongle auf dem Server gefunden "
        f"(bekannte IDs: {', '.join(sorted(KNOWN_RTLSDR_IDS))}; "
        f"gefundene Geräte: {candidates!r})"
    )


def is_attached(server_host: str, busid: str) -> bool:
    result = run_usbip("port")
    if result.returncode != 0:
        return False
    # 'usbip port' listet u.a. Zeilen wie:
    #   Port 00: <Port in Use> at ...
    #          -> usbip://<host>:3240/<busid>
    needle = f"{server_host}:3240/{busid}"
    return needle in result.stdout


def attach(server_host: str, busid: str) -> None:
    LOG.info("Attaching %s von %s ...", busid, server_host)
    result = run_usbip("attach", "-r", server_host, "-b", busid)
    if result.returncode != 0:
        raise UsbipError(f"'usbip attach' fehlgeschlagen: {result.stderr.strip()}")
    LOG.info("Erfolgreich attached: %s (%s)", busid, server_host)


def detach_all() -> None:
    result = run_usbip("port")
    if result.returncode != 0:
        return
    for match in re.finditer(r"^Port\s+(\d+):", result.stdout, re.MULTILINE):
        port = match.group(1)
        LOG.info("Detaching Port %s", port)
        run_usbip("detach", "-p", port)


class GracefulExit(Exception):
    pass


def _handle_signal(signum, _frame):
    raise GracefulExit()


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("RTLSDR_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = Config.from_env()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    backoff = 1.0
    try:
        while True:
            busid = config.busid
            try:
                if busid is None:
                    busid = discover_busid(config.server_host)
                if not is_attached(config.server_host, busid):
                    attach(config.server_host, busid)
                backoff = 1.0
            except UsbipError as exc:
                LOG.warning("%s - erneuter Versuch in %.0fs", exc, backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, config.max_backoff)
                continue

            time.sleep(config.poll_interval)
    except GracefulExit:
        LOG.info("Beende, löse Verbindung(en)...")
        detach_all()
        return 0


if __name__ == "__main__":
    sys.exit(main())
