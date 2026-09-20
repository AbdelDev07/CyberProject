# TP 2 — Le mode maintenance, et préparer l'arrivée de Docker

> Version complète : [pdf/TP2-mode-maintenance.pdf](../pdf/TP2-mode-maintenance.pdf). État : 🔄 en cours.

## 0. État des lieux

Fait par Claude le 20/09 ([journal](../journal/2026-09-20-nftables.md)) : `/etc/nftables.conf` corrigé et en place, `policy drop` ×3, `nftables.service` enabled, `/etc/nftables.d/` créé vide, `include "/etc/nftables.d/*.nft"` en fin de fichier. La sortie 80/443 est ouverte par des règles **en mémoire** (`TEMP-claude-session`) qui disparaîtront au prochain reload.

**Principe fondateur du TP** (appris par l'incident du `systemctl start` qui a effacé la règle TEMP) : *tout ce qui doit survivre vit dans un fichier lu par le service.*

**Exo 0.1 — Prérequis bloquant : la passerelle IPv4.** `ip route` n'a pas de `default via`. Toute la sortie passe en IPv6 ; les attaquants de Cowrie arriveront en IPv4 via la box et ne recevront jamais de réponse. Remplacer `gateway4: 10.0.0.1` par `routes: [{to: default, via: 192.168.1.254}]`, `chmod 600` le fichier (clé Wi‑Fi dedans), `sudo netplan try`, vérifier `curl -4 -sI https://archive.ubuntu.com`.

## 1. Cahier des charges

**Exo 1.1** — Flux nécessaires : dépôts Ubuntu, `download.docker.com`, `registry-1.docker.io`, `github.com`, `api.anthropic.com` — tous tcp/443 (+80). Questions : peut-on filtrer par nom de domaine ? (non : résolu au chargement, CDN) ; pourquoi « 80/443 vers tout sauf le LAN » est acceptable en *temporaire* et pas en permanent ; IPv4 **et** IPv6 ?

**Exo 1.2** — Le LAN en IPv6 : expliquer `2a01:e0a:abe:f8e0::/64` (global routable), `fd0f:ee:b0::/48` (ULA, « privé »), `fe80::/10` (lien local).

## 2. Le fichier `/etc/nftables.d/maintenance.nft`

**Exo 2.1** — Contraintes : pas de `flush ruleset` ; déclare `table inet filter { chain output { … } }` (fusion, pas écrasement) ; rien vers `$LAN`/`$LAN6` (les `define` sont-ils visibles depuis un include ? tester) ; `counter` + `comment "maintenance"`.

```
table inet filter {
    chain output {
        ip  daddr != ____ tcp dport { 80, 443 } ct state new counter accept comment "maintenance"
        ip6 daddr != { ____ } tcp dport { 80, 443 } ct state new counter accept comment "maintenance"
    }
}
```

**Piège de l'ordre :** inclus en fin de fichier → règles ajoutées **après** `log prefix "OUT-DROP "`. Trois options : include avant le `log` (possible dans un bloc `chain` ?), déplacer le `log` dans `zz-log.nft` (ordre alphabétique), ou accepter le bruit (non — pourquoi ?).

**Exo 2.2** — `nft -c -f /etc/nftables.conf` (vérifie aussi les includes) ; `systemctl reload nftables` (= `nft -f /etc/nftables.conf`, cf. `systemctl cat nftables`) ; les TEMP ont disparu, les `maintenance` sont là ; `curl` répond 200. Armer le filet avant.

## 3. L'interrupteur `fw-maint`

**Exo 3.1** — `/usr/local/sbin/fw-maint on|off|status`. Squelette : `on` = renommer `.nft.off` → `.nft`, `nft -c`, `systemctl reload nftables` ; `off` = à écrire ; `status` = `nft list chain inet filter output | grep -q '"maintenance"'`.

Questions : pourquoi `nft -c` avant le reload (que se passe-t-il entre le `flush` et l'erreur de syntaxe ?) ; pourquoi pas `rm` ; que dit `status` après un reboot, est-ce voulu ?

**Exo 3.2** — Cycle : `off` → `curl` échoue + OUT-DROP DPT=443 ; `getent` résout quand même (DNS hors maintenance) ; `on` → 200 ; `off && reboot` → `status` = NORMAL ; `on`. *Pendant « off », Claude est injoignable — c'est normal.*

## 4. Installer Docker et voir ce qu'il fait au pare-feu

Dépôt officiel (`download.docker.com`, paquets `docker-ce docker-ce-cli containerd.io docker-compose-plugin`).

**Exo 4.1** — `nft list tables` avant/après `systemctl start docker` ; `nft list table ip nat` ; `nft list chain ip filter DOCKER-USER` ; `sysctl net.ipv4.ip_forward`. Noter : famille `ip`, pas `inet` (conséquence pour l'IPv6 ?).

**Exo 4.2 — Le piège du `flush ruleset`.** `systemctl reload nftables` puis `nft list tables` puis `docker run --rm alpine ping -c1 1.1.1.1`. Les tables Docker ont disparu, le conteneur n'a plus de réseau. Correctif dans `/etc/nftables.conf` :

```
table inet filter          # crée la table si absente
flush table inet filter    # ne vide QUE la mienne
```

**Exo 4.3 — Deux pare-feux, une priorité.** Ma chaîne `forward` (`policy drop`) et `ip filter FORWARD` de Docker sont sur le même hook, même priorité. Un paquet doit être accepté par **les deux**. Écrire dans ma chaîne `forward` : (a) established ; (b) entrée vers les ports Cowrie ; (c) sortie conteneur → ELK ; (d) sortie conteneur → Internet seulement en maintenance. Indice : `iifname "docker0"` / `oifname "docker0"`. `DOCKER-USER` est-il encore nécessaire ?

## 5. Livrables

`ip route` avec la route par défaut · tableau 1.2 · `maintenance.nft` + réponse au piège de l'ordre · `fw-maint` complet + réponses 3.1 · résultat du cycle 3.2 reboot compris · réponses 4.1–4.3 + nouvelle en-tête de `nftables.conf` + chaîne `forward` finale · `nft list ruleset` avec Docker installé et maintenance **off** (état de repos du honeypot).

**Étape suivante :** Cowrie — conteneur, redirection 22→2222, sortie vers Filebeat/Logstash, durcissement du conteneur.
