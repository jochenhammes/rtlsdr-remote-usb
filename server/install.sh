#!/usr/bin/env bash
# Installiert und aktiviert die USB/IP-Server-Seite für den RTL-SDR-Export.
#
# Muss auf der Maschine laufen, an der der RTL-SDR-Dongle physisch steckt.
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Bitte als root ausführen (sudo $0)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

if command -v usbip &>/dev/null && command -v usbipd &>/dev/null; then
  echo "==> usbip/usbipd bereits vorhanden ($(command -v usbip)), Installation übersprungen"
else
  echo "==> Installiere usbip-Tools"
  if command -v apt-get &>/dev/null; then
    apt-get update
    apt-get install -y usbip
  elif command -v dnf &>/dev/null; then
    dnf install -y usbip-utils
  elif command -v pacman &>/dev/null; then
    pacman -Sy --noconfirm usbutils
  else
    echo "Unbekannter Paketmanager – bitte 'usbip' (bzw. 'usbip-utils') manuell installieren." >&2
    exit 1
  fi
fi

if ! command -v usbip &>/dev/null || ! command -v usbipd &>/dev/null; then
  echo "usbip/usbipd nach der Installation nicht im PATH gefunden." >&2
  exit 1
fi

USBIP_BIN="$(command -v usbip)"
USBIPD_BIN="$(command -v usbipd)"

echo "==> Lade Kernelmodul usbip_host"
modprobe usbip_host
echo "usbip_host" > /etc/modules-load.d/usbip-host.conf

echo "==> Blackliste den nativen DVB-Treiber (kollidiert sonst mit librtlsdr/usbip)"
cat > /etc/modprobe.d/blacklist-rtl-sdr.conf <<'EOF'
# Verhindert, dass der Kernel den RTL-SDR-Dongle als DVB-Empfänger einbindet.
# librtlsdr (und damit auch USB/IP-Clients) brauchen direkten USB-Zugriff.
blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2830
EOF

echo "==> Installiere udev-Regel (automatisches usbip bind beim Einstecken)"
sed "s#/usr/sbin/usbip#${USBIP_BIN}#" "${SCRIPT_DIR}/99-rtlsdr-usbip.rules" \
  > /etc/udev/rules.d/99-rtlsdr-usbip.rules
chmod 644 /etc/udev/rules.d/99-rtlsdr-usbip.rules
udevadm control --reload-rules

echo "==> Installiere systemd-Unit für usbipd"
sed "s#/usr/sbin/usbipd#${USBIPD_BIN}#" "${SCRIPT_DIR}/rtlsdr-usbipd.service" \
  > /etc/systemd/system/rtlsdr-usbipd.service
chmod 644 /etc/systemd/system/rtlsdr-usbipd.service
systemctl daemon-reload
systemctl enable --now rtlsdr-usbipd.service

cat <<'EOF'

Fertig.

Falls der Dongle schon eingesteckt war, bevor die udev-Regel installiert
wurde, einmal aus- und wieder einstecken, oder manuell binden:

    usbip list -l          # busid herausfinden, z.B. 1-1.4
    usbip bind -b <busid>

Mit 'usbip list -l' prüfen, ob das Gerät als "usbip-host" exportiert wird.
EOF
