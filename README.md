# rtlsdr-remote-usb

Bindet einen RTL-SDR-Dongle, der an einer entfernten Linux-Maschine steckt, per
[USB/IP](https://docs.kernel.org/usb/usbip_protocol.html) lokal ein — als wäre
er direkt per USB angeschlossen. Jede Anwendung, die normalerweise
`librtlsdr` nutzt (SDR#, GQRX, CubicSDR, GNU Radio/osmosdr, `rtl_fm`,
`rtl_tcp`, ...), funktioniert dadurch unverändert, ganz ohne
Netzwerkprotokoll-Unterstützung in der Anwendung selbst.

## Wie funktioniert das?

USB/IP ist ein Linux-Kernel-Subsystem, das den kompletten USB-Verkehr eines
Geräts über TCP tunnelt:

```
[RTL-SDR Dongle] --USB--> [Server: usbipd + usbip_host Kernelmodul]
                                    |
                         (Netzwerk, Port 3240/tcp)
                                    |
                  [Client: vhci-hcd Kernelmodul + usbip attach]
                                    |
                        /dev/bus/usb/... (virtuelles USB-Gerät)
                                    |
                    librtlsdr / SDR#, GQRX, GNU Radio, rtl_fm, ...
```

Der Server exportiert den Dongle, der Client "attached" ihn — danach legt der
Kernel auf dem Client ein ganz normales USB-Gerät an. Für `librtlsdr` und
alle Anwendungen darüber ist das nicht von einem physisch angeschlossenen
Dongle zu unterscheiden.

## Quick Start

1. **Server** (an dem der RTL-SDR-Dongle physisch steckt): siehe
   [`server/README.md`](server/README.md).
2. **Client** (auf dem der Dongle "erscheinen" soll): siehe
   [`client/README.md`](client/README.md).
3. Bei Problemen: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).
4. **Vor dem Einsatz über ein nicht vertrauenswürdiges Netzwerk unbedingt
   lesen:** [`docs/SECURITY.md`](docs/SECURITY.md) — USB/IP ist
   standardmäßig unverschlüsselt und ohne Authentifizierung.

## Server testen ohne Linux-Client

Um nach der Server-Installation zu prüfen, ob der Dongle erreichbar und
exportiert ist — auch von einer Maschine ohne `usbip`/Kernelmodul-Support
(z.B. macOS) — siehe [`tools/check-export.sh`](tools/check-export.sh):

```bash
./tools/check-export.sh <server-host-oder-ip>
```

Das testet nur Netzwerk-Erreichbarkeit und die Export-Liste, nicht den
echten Attach (dafür wird ein Linux-Client mit `vhci-hcd` benötigt, siehe
[`client/README.md`](client/README.md)).

## Voraussetzungen

- Beide Maschinen: Linux mit einem Kernel, der USB/IP unterstützt
  (`CONFIG_USBIP_CORE`, bei den meisten Distributions-Kerneln vorhanden).
- Server: Paket `usbip` bzw. `usbip-utils` (Debian/Ubuntu: `usbip`, das
  `usbip_host`-Kernelmodul heißt dort `usbip-host`).
- Client: dasselbe Paket, zusätzlich das `vhci-hcd`-Kernelmodul.
- Root-/`sudo`-Rechte auf beiden Seiten (Kernelmodule laden, USB-Geräte
  binden).

## Projektstruktur

```
rtlsdr-remote-usb/
├── server/     Setup & systemd-Unit für die Maschine mit dem Dongle
├── client/     Setup, Watchdog & systemd-Unit für die Maschine, die den
│               Dongle nutzen soll
├── docs/       Troubleshooting & Sicherheitshinweise
├── tests/      Tests für die Watchdog-Parsing-/Retry-Logik
└── tools/      check-export.sh: Server-Reachability-Check ohne Linux-Client
```

## Lizenz

MIT, siehe [`LICENSE`](LICENSE).
