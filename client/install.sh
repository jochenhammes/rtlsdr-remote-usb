#!/usr/bin/env bash
# Installiert und aktiviert die USB/IP-Client-Seite plus den Watchdog-Service.
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Bitte als root ausführen (sudo $0)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

echo "==> Installiere usbip-Tools und Python 3"
if command -v apt-get &>/dev/null; then
  apt-get update
  apt-get install -y usbip python3
elif command -v dnf &>/dev/null; then
  dnf install -y usbip-utils python3
elif command -v pacman &>/dev/null; then
  pacman -Sy --noconfirm usbutils python
else
  echo "Unbekannter Paketmanager – bitte 'usbip' und 'python3' manuell installieren." >&2
  exit 1
fi

echo "==> Lade Kernelmodul vhci-hcd"
modprobe vhci-hcd
echo "vhci-hcd" > /etc/modules-load.d/vhci-hcd.conf

echo "==> Installiere Watchdog-Skript"
install -m 755 "${SCRIPT_DIR}/rtlsdr_usbip_watchdog.py" /usr/local/bin/rtlsdr-usbip-watchdog

echo "==> Konfigurationsdatei"
if [[ ! -f /etc/default/rtlsdr-usbip-client ]]; then
  install -m 644 "${SCRIPT_DIR}/config.example.env" /etc/default/rtlsdr-usbip-client
  echo "    -> /etc/default/rtlsdr-usbip-client angelegt. Bitte RTLSDR_SERVER_HOST anpassen!"
else
  echo "    -> /etc/default/rtlsdr-usbip-client existiert bereits, wird nicht überschrieben."
fi

echo "==> Installiere systemd-Unit"
install -m 644 "${SCRIPT_DIR}/rtlsdr-usbip-client.service" /etc/systemd/system/rtlsdr-usbip-client.service
systemctl daemon-reload

cat <<'EOF'

Fertig. Vor dem Start unbedingt RTLSDR_SERVER_HOST in
/etc/default/rtlsdr-usbip-client setzen, dann:

    sudo systemctl enable --now rtlsdr-usbip-client
    journalctl -u rtlsdr-usbip-client -f

Nach erfolgreichem Attach erscheint der Dongle unter
/dev/bus/usb/... und ist z.B. mit 'rtl_test' oder 'lsusb' prüfbar.
EOF
