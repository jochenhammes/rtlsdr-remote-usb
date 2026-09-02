# Troubleshooting

## `usbip list -l` zeigt den Dongle nicht (Server)

Der native DVB-Kerneltreiber hat das Gerät wahrscheinlich schon belegt.
Prüfen:

```bash
lsmod | grep dvb_usb_rtl28xxu
```

Falls geladen: `install.sh` blacklisted den Treiber, aber das greift erst
nach einem Reboot bzw. Neu-Einstecken des Dongles. Sofort-Fix:

```bash
sudo rmmod dvb_usb_rtl28xxu
sudo modprobe usbip_host
sudo usbip bind -b <busid>
```

## `usbip list -r <host>` vom Client aus liefert nichts / Timeout

- Ist `rtlsdr-usbipd` auf dem Server aktiv? `systemctl status rtlsdr-usbipd`
- Ist Port 3240/tcp vom Client aus erreichbar? `nc -zv <server> 3240`
- Firewall auf dem Server prüfen (`ufw status`, `iptables -L`, ...).
- Ist der Dongle überhaupt gebunden? `usbip list -l` auf dem Server muss ihn
  als `usbip-host`-Treiber zeigen.

## `usbip attach` schlägt mit "already attached" fehl

Der Client hat den Dongle schon an einem anderen Port attached (z.B. nach
einem vorherigen Absturz ohne sauberes Detach). Alle Ports prüfen und lösen:

```bash
usbip port
sudo usbip detach -p <port>
```

Der Watchdog macht das beim Beenden automatisch (`SIGTERM`/`SIGINT`), aber
nicht nach einem harten Absturz oder Stromausfall.

## Kernelmodul `vhci-hcd` / `usbip_host` fehlt

```bash
modinfo vhci-hcd     # bzw. usbip_host auf dem Server
```

Falls "not found": Der Kernel wurde ohne USB/IP-Unterstützung gebaut
(selten bei Standard-Distributions-Kerneln) oder die `linux-modules-extra`-
bzw. entsprechenden Pakete fehlen (Debian/Ubuntu: meist in `linux-image-*`
enthalten, sonst `linux-modules-extra-$(uname -r)` installieren).

## Watchdog findet den Dongle nicht automatisch

Der Watchdog erkennt nur die Vendor:Product-IDs `0bda:2832` und `0bda:2838`
(Standard-RTL2832U-Dongles). Bei einem abweichenden Dongle oder mehreren
exportierten Geräten: `busid` manuell herausfinden (`usbip list -r <host>`)
und in `/etc/default/rtlsdr-usbip-client` als `RTLSDR_BUSID` fest eintragen.

## Verbindung bricht ständig ab

- Netzwerkqualität prüfen (USB/IP reagiert empfindlich auf Paketverlust und
  hohe Latenz – WLAN ist meist ungeeignet, LAN/VPN mit stabiler Verbindung
  bevorzugen).
- `journalctl -u rtlsdr-usbip-client -f` und `journalctl -u rtlsdr-usbipd -f`
  auf beiden Seiten parallel beobachten, um zu sehen, welche Seite den
  Abbruch meldet.
