# Client-Setup

Läuft auf der Maschine, auf der der entfernte RTL-SDR-Dongle "erscheinen"
soll.

## Installation

```bash
sudo ./install.sh
```

Das Skript:

1. installiert `usbip` und `python3`,
2. lädt das Kernelmodul `vhci-hcd` und aktiviert es dauerhaft,
3. installiert den Watchdog nach `/usr/local/bin/rtlsdr-usbip-watchdog`,
4. legt `/etc/default/rtlsdr-usbip-client` aus `config.example.env` an
   (falls noch nicht vorhanden),
5. installiert die systemd-Unit `rtlsdr-usbip-client`.

## Konfiguration

In `/etc/default/rtlsdr-usbip-client` mindestens setzen:

```
RTLSDR_SERVER_HOST=192.168.1.50
```

Alle Optionen sind in [`config.example.env`](config.example.env)
dokumentiert (Server-Host, optional feste `busid`, Poll-Intervall, maximales
Backoff, Log-Level).

## Starten

```bash
sudo systemctl enable --now rtlsdr-usbip-client
journalctl -u rtlsdr-usbip-client -f
```

Der Watchdog:

- sucht den RTL-SDR-Dongle auf dem konfigurierten Server automatisch (per
  Vendor:Product-ID `0bda:2832`/`0bda:2838`), sofern keine feste `busid`
  konfiguriert ist,
- attached ihn per `usbip attach`,
- prüft periodisch (`RTLSDR_POLL_INTERVAL`, Default 5s), ob die Verbindung
  noch steht,
- attached bei Verbindungsverlust automatisch neu, mit exponentiellem
  Backoff bis `RTLSDR_MAX_BACKOFF` (Default 60s),
- löst beim Beenden (`systemctl stop`) alle Verbindungen sauber.

## Prüfen, ob es funktioniert

```bash
lsusb                 # Dongle sollte als Realtek-Gerät auftauchen
usbip port             # zeigt attached Ports
rtl_test -t            # aus rtl-sdr-Tools, testet den Dongle direkt
```

Danach kann jede normale RTL-SDR-Anwendung (GQRX, SDR#, GNU Radio, `rtl_fm`,
...) den Dongle wie gewohnt benutzen — er verhält sich exakt wie ein lokal
angeschlossener.
