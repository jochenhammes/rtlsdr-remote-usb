#!/usr/bin/env bash
# Prüft von einer BELIEBIGEN Maschine aus (auch macOS/Windows, kein
# usbip-Client oder Kernelmodul nötig), ob ein rtlsdr-remote-usb-Server
# erreichbar ist und ein Gerät exportiert.
#
# Testet NUR Erreichbarkeit + Export-Liste, nicht den echten Attach (der
# braucht das vhci-hcd-Kernelmodul und geht nur von einem echten
# Linux-Client aus, siehe client/README.md).
#
# Nutzung: ./check-export.sh <server-host-oder-ip>
set -euo pipefail

HOST="${1:-}"
if [[ -z "${HOST}" ]]; then
  echo "Nutzung: $0 <server-host-oder-ip>" >&2
  exit 1
fi

echo "==> Teste TCP-Erreichbarkeit von ${HOST}:3240"
if command -v nc &>/dev/null; then
  if nc -z -w 5 "${HOST}" 3240; then
    echo "    OK: Port 3240 ist offen."
  else
    echo "    FEHLER: Port 3240 nicht erreichbar." >&2
    echo "    -> Läuft 'rtlsdr-usbipd' auf dem Server? (systemctl status rtlsdr-usbipd)" >&2
    echo "    -> Firewall auf dem Server blockiert Port 3240?" >&2
    exit 1
  fi
else
  echo "    'nc' nicht gefunden, überspringe (weiter mit usbip list -r)."
fi

echo
echo "==> Frage exportierte Geräte ab (usbip list -r ${HOST})"
if command -v usbip &>/dev/null; then
  usbip list -r "${HOST}"
elif command -v docker &>/dev/null; then
  echo "    'usbip' lokal nicht installiert, nutze einen Docker-Container..."
  docker run --rm debian:bookworm-slim bash -c \
    "apt-get update -qq && apt-get install -y -qq usbip >/dev/null 2>&1 && usbip list -r ${HOST}"
else
  cat >&2 <<EOF
    Weder 'usbip' noch 'docker' gefunden.

    Auf macOS z.B. Docker Desktop installieren und diesen Befehl erneut
    ausführen, oder auf einer Linux-Maschine 'usbip' installieren
    (siehe client/README.md).
EOF
  exit 1
fi

cat <<'EOF'

Erwartetes Ergebnis: ein Eintrag mit "(0bda:2832)" oder "(0bda:2838)" —
das ist der RTL-SDR-Dongle. Taucht er nicht auf, siehe
docs/TROUBLESHOOTING.md ("usbip list -l zeigt den Dongle nicht").

Für den echten Funktionstest (Dongle nutzen, z.B. mit rtl_test) wird ein
echter Linux-Client mit dem vhci-hcd-Kernelmodul benötigt, siehe
client/README.md.
EOF
