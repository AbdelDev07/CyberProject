# Correction du TP 1 — à partir de ma machine et de mes journaux

> Version complète (19 pages, schémas) : [pdf/TP-correction.pdf](../pdf/TP-correction.pdf).
> Ce corrigé a été établi par Claude en lisant `/etc/nftables.conf`, `nft list ruleset` et `dmesg` sur la machine — pas sur un cas théorique.

## Ce que j'avais écrit

```
table inet filter {
        chain input {
                type filter hook input priority 0;          # <- pas de policy
                iif lo accept
                ct state invalid drop
                ct state established,related accept
                tcp dport {22, 23} accept
                tcp dport 53 accept                          # <- ouvre un DNS serveur ?!
                udp dport 53 accept
                tcp dport {443, 80} accept                   # <- ouvre un serveur web ?!
                tcp dport $SSH_PORT ip saddr $ADMIN_IP accept
                ip saddr 192.168.1.0/24 icmp type { echo-request, destination-unreachable, time-exceeded } accept
                ip6 saddr fe80::/10 icmpv6 type { ... } accept
                log prefix "IN-DROP " limit rate 5/minute
        }
        chain forward {
                type filter hook forward priority filter;    # <- vide, policy accept
        }
        chain output {
                type filter hook output priority 0;          # <- pas de policy
                oif lo accept
                ct state invalid drop
                ct state established,related accept
                tcp dport $ELK_PORT ip saddr $ELK_IP accept  # <- saddr au lieu de daddr
                tcp dport {443, 80} accept
                tcp dport 53 accept
                udp dport 53 accept
                udp dport 123 accept
                log prefix "OUT-DROP " limit rate 5/minute
        }
}
```

## Synthèse

**Juste :** structure du fichier, variables `define`, `ct state invalid drop` en tête, restriction SSH par IP source (elle a fonctionné : 16 tentatives depuis `192.168.1.178` bloquées), règles `log` (c'est grâce à elles que la correction existe), et la réponse à l'exo 2.1 — j'avais trouvé le bug (`established` manquant en output).

**À revoir :**

| Bug | Gravité |
|---|---|
| 1. Aucune `policy drop` → `policy accept` implicite : **le pare-feu n'interdit rien** | critique |
| 2. `ip saddr $ELK_IP` en output → la règle ne peut jamais matcher (en sortie, la source est toujours moi) | critique |
| 3. Chaîne `forward` vide et ouverte → tout le trafic Docker/Cowrie passera | majeur |
| 4. `dport 80/443/53` en **input** → ouvre des services, ne répare rien (les réponses sont couvertes par `established`) | majeur |
| 5. Ports Cowrie en input alors qu'un conteneur passe par forward | moyen |
| 6. NDP IPv6 bloqué en sortie ; et la machine a une **IPv6 publique** (pas de NAT) | majeur |
| 7. `nftables.service` disabled → rien ne survit au reboot | majeur |

## Ce que mes journaux racontent (`dmesg | grep -E 'IN-DROP|OUT-DROP'`, 777 lignes)

| Nb | Sens | Protocole | Signification |
|---|---|---|---|
| 588 | sortant | ICMPv6 135/136 | découverte de voisins IPv6 bloquée → IPv6 cassé |
| 111 | sortant | UDP/53 | **DNS bloqué** — la vraie cause de « le web ne marche pas » |
| 54 | sortant | TCP/53 | idem, vers `fd0f:ee:b0::1` (Freebox) |
| 16 | entrant | TCP/2727 | SSH depuis `192.168.1.178` — ma règle a fait son travail |

Les 111 paquets DNS tombent dans une fenêtre de 76 s : exactement le moment où je testais avec `policy drop` sans règle DNS. J'ai « réparé » en ajoutant des `accept 443` en entrée — ce qui n'a rien corrigé (le problème était en sortie, sur le port 53) et a ouvert des services inexistants.

**Leçon :** le symptôme visible (« le web est cassé ») ne désigne pas la règle fautive. Le journal donne `PROTO=` et `DPT=` : il faut le lire **avant** de modifier une règle.

## Mes annotations, corrigées

- *« table inet — je sais pas à quoi ça correspond »* → famille d'adresses : `inet` voit IPv4 **et** IPv6. Piège : `ip saddr` ne matche que v4, `ip6 saddr` que v6, `tcp dport` les deux.
- *« iif lo accept — fais repartir la règle depuis le début »* → **non.** `iif` = *input interface*, `lo` = loopback. « Si le paquet est entré par le bouclage, accepte. » Vital : `systemd-resolved` écoute sur `127.0.0.53`.
- *« ct state established — les réponses passent sans passer par le pare-feu ? »* → non, **chaque paquet est évalué** ; cette règle les reconnaît tous d'un coup grâce au suivi de connexion.
- *« Il manque ct state established,related accept dans output »* → **bonne réponse.** Sans elle, le SYN-ACK de sshd est droppé en sortie : la session gèle.
- *« pourquoi bash -c ? »* → `sudo sleep 120 && nft flush` : le `&&` est interprété par mon shell, donc `nft flush` tourne sans sudo. `sudo bash -c '…'` exécute toute la chaîne en root. Mieux : `systemd-run --on-active=120 --unit=fw-rollback nft flush ruleset` (survit à la perte de la session).
- Exo 1.1 (1) *« je ne comprends pas »* → deux chemins : **A.** Cowrie → fichier JSON → Filebeat (hôte) → Logstash **5044** → règle en **output** ; **B.** Cowrie → Elasticsearch **9200** directement depuis le conteneur → règle en **forward**. J'ai choisi 5044, donc A.
- Exo 1.2 *« les fichiers sont enregistrés dans dl/ »* → vrai, mais pour les enregistrer **Cowrie les télécharge vraiment** : mon IP apparaît chez l'hébergeur du malware. Pour un lab : sortie fermée, Cowrie journalise l'URL sans récupérer le fichier.

## Le ruleset corrigé

Voir [config/nftables-corrige.conf](../config/nftables-corrige.conf) (version validée `nft -c`) et [config/nftables.conf](../config/nftables.conf) (version réellement en place, avec le DNS IPv6 de la Freebox et l'`include` du mode maintenance).

Changements : `policy drop` ×3 · `ip daddr $ELK_IP` · forward fermé et journalisé · suppression des 80/443/53 en input · DNS restreint aux résolveurs déclarés · ICMPv6 complet dans **les deux** chaînes · `ct state new` sur les ouvertures · pas de 80/443 en sortie (mon choix : maintenance à la demande) · `level info` sur les logs.

## Procédure de déploiement sûre

1. Deux terminaux ; `sudo systemd-run --on-active=180 --unit=fw-rollback nft flush ruleset`.
2. `sudo nft -c -f /etc/nftables.conf`.
3. `sudo nft -f /etc/nftables.conf` ; taper une commande dans le terminal A ; **ouvrir une troisième connexion SSH** (seule une *nouvelle* connexion prouve la règle d'entrée).
4. Tests (`getent`, `curl` doit échouer si sortie fermée, `nc` vers ELK doit passer, `nc` vers autre VM doit échouer + OUT-DROP).
5. `systemctl stop fw-rollback.timer`, `systemctl enable --now nftables`, reboot.
