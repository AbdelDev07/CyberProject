# config/

Copies des fichiers réellement en place sur la machine honeypot (secrets retirés).

| Fichier | Sur la machine | Note |
|---|---|---|
| `nftables.conf` | `/etc/nftables.conf` | pare-feu de base, état fermé, `include /etc/nftables.d/*.nft` |
| `nftables.d/README` | `/etc/nftables.d/README` | répertoire du mode maintenance (TP 2) |
| `nftables-corrige.conf` | — | version issue de la correction du TP 1, avant ajout du DNS IPv6 et de l'include |
| `netplan-50-cloud-init.example.yaml` | `/etc/netplan/50-cloud-init.yaml` | **mot de passe Wi‑Fi remplacé par REDACTED** ; contient encore le `gateway4` fautif (exo 0.1 du TP 2) |
