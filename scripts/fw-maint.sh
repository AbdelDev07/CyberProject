#!/bin/bash
# fw-maint on|off|status — bascule le mode maintenance du pare-feu (TP 2, exo 3.1)
# SQUELETTE À COMPLÉTER : la sous-commande "off" est volontairement vide.
set -euo pipefail
LIVE=/etc/nftables.d/maintenance.nft
OFF=/etc/nftables.d/maintenance.nft.off      # même fichier, extension qui échappe au glob *.nft

case "${1:-}" in
  on)
    [ -f "$OFF" ] && mv "$OFF" "$LIVE"
    nft -c -f /etc/nftables.conf
    systemctl reload nftables
    ;;
  off)
    # à écrire
    ;;
  status)
    if nft list chain inet filter output | grep -q '"maintenance"'; then
      echo "MAINTENANCE : sortie web OUVERTE"
    else
      echo "NORMAL : sortie web fermée"
    fi
    ;;
  *) echo "usage: $0 on|off|status" >&2; exit 2 ;;
esac
