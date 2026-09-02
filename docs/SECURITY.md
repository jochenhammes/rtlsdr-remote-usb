# Sicherheitshinweise

**USB/IP hat standardmäßig keine Verschlüsselung und keine
Authentifizierung.** Jeder, der den Server-Port (3240/tcp) erreichen kann,
kann exportierte USB-Geräte attachen und den kompletten USB-Traffic
mitlesen. Für einen RTL-SDR-Dongle heißt das konkret: Zugriff auf alles, was
der Dongle empfängt, plus die Möglichkeit, ihn zu belegen/zu stören.

## Empfehlungen

1. **Nie direkt ins Internet exponieren.** Port 3240/tcp niemals über
   Portweiterleitung/Firewall öffentlich erreichbar machen.
2. **Nur über ein VPN oder einen Tunnel nutzen**, z.B.:
   - [Tailscale](https://tailscale.com/) oder [WireGuard](https://www.wireguard.com/)
     zwischen Server und Client, USB/IP nur über das VPN-Interface,
   - oder ein SSH-Tunnel/Port-Forward (`ssh -L 3240:localhost:3240 <server>`),
     dann `RTLSDR_SERVER_HOST=localhost` auf dem Client.
3. **Firewall auf dem Server**: Port 3240/tcp nur für die IP(s) des/der
   Clients freigeben (z.B. via `ufw allow from <client-ip> to any port 3240`).
4. Läuft der Server ohnehin schon in einem privaten/vertrauenswürdigen LAN
   (z.B. beide Maschinen im selben Heimnetz hinter NAT), ist das
   Restrisiko überschaubar — trotzdem empfiehlt sich mindestens Punkt 3.

## Rechte

Sowohl `usbipd` (Server) als auch das Binden/Attachen von Geräten erfordern
Root-Rechte bzw. entsprechende Kernelmodul-Berechtigungen. Die mitgelieferten
systemd-Units laufen daher als root. Wer das einschränken möchte, kann
`CAP_NET_ADMIN`/`CAP_SYS_ADMIN` gezielt vergeben (nicht Teil dieses
Projekts, da distributionsabhängig).
