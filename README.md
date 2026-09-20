# CyberProject — Honeypot Cowrie durci, appris pas à pas

> Journal d'un apprentissage assisté par IA : je demande à Claude des **TP et des cours**, je fais **toutes les manipulations moi-même** sur une vraie machine, et Claude **corrige à partir de l'état réel** de cette machine (fichiers, journaux du noyau) — pas à partir d'un cas théorique.

## L'objectif

Faire tourner un honeypot SSH/Telnet ([Cowrie](https://github.com/cowrie/cowrie)) dans Docker sur une machine Ubuntu Server 24.04 de mon réseau domestique, avec :

- un pare-feu **nftables** en liste blanche (`policy drop` partout) ;
- **un seul flux sortant autorisé vers le LAN** : l'envoi des logs à une VM ELK ;
- une sortie Internet **fermée par défaut**, ouverte à la demande (mode maintenance) ;
- un accès d'administration SSH restreint à mon poste.

## La méthode

```
   moi                                      Claude
    │  « fais-moi un TP sur X »               │
    │ ───────────────────────────────────────▶│
    │                       TP (PDF) : objectifs, indices, tests de vérification
    │ ◀───────────────────────────────────────│
    │  je fais les manips, j'annote le PDF    │
    │  « j'ai bloqué ici, regarde la machine »│
    │ ───────────────────────────────────────▶│
    │            Claude lit /etc/…, dmesg, nft list ruleset
    │                       correction (PDF) + cours (PDF) ciblés sur MES erreurs
    │ ◀───────────────────────────────────────│
```

Claude ne fait les actions à ma place que quand je le demande explicitement (reset de la machine, pose du pare-feu final). Tout le reste, c'est moi — y compris les erreurs, qui sont documentées telles quelles parce que ce sont elles qui apprennent le plus.

## Où en est-on

| Étape | État | Documents |
|---|---|---|
| 0. Remise à neuf de la machine (retrait de k3s, Docker, Keycloak…) | ✅ fait | [journal/2026-09-18-reset.md](journal/2026-09-18-reset.md) |
| 1. TP 1 — pare-feu nftables du honeypot | ✅ fait, corrigé | [TP](docs/02-tp1-parefeu.md) · [Correction](docs/03-correction-tp1.md) · [PDF](pdf/) |
| 2. Cours nftables (écrit à partir de mes points bloquants) | ✅ | [docs/04-cours-nftables.md](docs/04-cours-nftables.md) · [PDF](pdf/Cours-nftables.pdf) |
| 3. Pare-feu de base posé et activé sur la machine | ✅ fait | [journal/2026-09-20-nftables.md](journal/2026-09-20-nftables.md) · [config/nftables.conf](config/nftables.conf) |
| 4. TP 2 — mode maintenance + installation Docker | 🔄 en cours | [docs/05-tp2-mode-maintenance.md](docs/05-tp2-mode-maintenance.md) · [PDF](pdf/TP2-mode-maintenance.pdf) |
| 5. Cowrie dans Docker, redirection 22→2222, envoi vers ELK | ⏳ à venir | |
| 6. Durcissement (fail2ban, sysctl, lynis) | ⏳ à venir | |

## Le laboratoire

```
 Internet ──── Freebox (192.168.1.254, NAT v4 / routage v6) ──┬── PC admin      192.168.1.33   (SSH → 2727)
                                                             ├── HONEYPOT      192.168.1.63   (Cowrie + nftables)
                                                             ├── VM ELK        192.168.1.35   (Logstash 5044)
                                                             └── ?             192.168.1.178  (vu dans les logs IN-DROP)
```

Machine honeypot : Ubuntu Server 24.04.3, noyau 6.8, Wi‑Fi en IP statique, SSH sur le port 2727 avec clés uniquement.

## Ce que j'ai appris (résumé honnête)

Les erreurs que j'ai faites au TP 1, toutes retrouvées dans `dmesg` par Claude :

1. **Aucune `policy drop`** → mon pare-feu ne bloquait rien, tout en écrivant « DROP » dans le journal.
2. **`ip saddr` au lieu de `ip daddr`** sur la règle la plus importante (logs vers ELK) → elle ne pouvait jamais matcher.
3. **« Le web ne marche pas »** → c'était le DNS (111 paquets UDP/53 refusés). J'ai ajouté des règles 443 en entrée, ce qui ouvrait des services au lieu de corriger la sortie.
4. **IPv6 oublié** → 588 paquets NDP bloqués, et la machine a une adresse IPv6 publique (pas de NAT en v6 : le pare-feu est le seul rempart).
5. **Service non activé** → rien n'aurait survécu au redémarrage.

Le détail, avec les preuves, est dans la [correction](docs/03-correction-tp1.md).

## Organisation du dépôt

```
docs/        les TP, corrections et cours en Markdown
pdf/         les mêmes, en PDF (versions complètes avec schémas)
config/      fichiers de configuration réellement en place sur la machine (secrets retirés)
scripts/     scripts d'exploitation
journal/     ce qui a été fait, quand, et ce qui a été constaté
```
