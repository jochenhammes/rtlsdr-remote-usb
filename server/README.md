# Server-Setup

Läuft auf der Maschine, an der der RTL-SDR-Dongle physisch per USB steckt.

## Installation

```bash
sudo ./install.sh
```

Das Skript:

1. installiert `usbip` (Debian/Ubuntu: Paket `usbip`, Fedora: `usbip-utils`),
2. lädt das Kernelmodul `usbip_host` und aktiviert es dauerhaft,
3. blacklisted den DVB-Kernel-Treiber `dvb_usb_rtl28xxu` (der würde den
   Dongle sonst als DVB-Empfänger einbinden statt ihn für `librtlsdr`/USB/IP
   freizugeben),
4. installiert eine udev-Regel, die den Dongle beim Einstecken automatisch
   für den Export bindet (`usbip bind`),
5. installiert und startet den `rtlsdr-usbipd`-systemd-Service.

## Manuelle Schritte / Kontrolle

Exportierte Geräte anzeigen:

```bash
usbip list -l
```

Ein Gerät manuell binden/lösen (falls die udev-Regel nicht greift, z.B. weil
der Dongle schon vor der Installation eingesteckt war):

```bash
usbip bind -b 1-1.4      # busid aus 'usbip list -l'
usbip unbind -b 1-1.4
```

Service-Status/Logs:

```bash
systemctl status rtlsdr-usbipd
journalctl -u rtlsdr-usbipd -f
```

## Firewall

Der `usbipd`-Daemon lauscht standardmäßig auf Port **3240/tcp**. Diesen Port
nur für vertrauenswürdige Client-IPs bzw. nur innerhalb eines VPNs öffnen —
siehe [`../docs/SECURITY.md`](../docs/SECURITY.md).
