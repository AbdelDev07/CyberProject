# Cours — nftables : filtrer le trafic d'une machine Linux

> Écrit par Claude à partir de mes points bloquants du TP 1. Version complète avec 12 schémas : [pdf/Cours-nftables.pdf](../pdf/Cours-nftables.pdf). Ceci est le résumé.

## 1. Pourquoi c'est difficile

Trois pièges : (1) une conversation a deux sens — autoriser la sortie ne suffit pas ; (2) tout le trafic ne passe pas au même endroit — pour moi, de moi, à travers moi ; (3) la machine émet du trafic auquel personne ne pense (DNS, NTP, NDP, bouclage) et le symptôme visible ne désigne jamais la bonne règle.

**Fil directeur :** on n'écrit pas un pare-feu en listant des ports, mais des **flux** — qui parle à qui, dans quel sens, qui ouvre la conversation.

## 2. Le voyage d'un paquet (netfilter)

Cinq points de contrôle (*hooks*) : `prerouting` → décision de routage → `input` (pour moi) ou `forward` (traverse) → `output` (émis par moi) → `postrouting`.

| Chemin | Chaînes | Exemple |
|---|---|---|
| entrant | prerouting → **input** | SSH vers ma machine |
| sortant | **output** → postrouting | curl, envoi des logs à ELK |
| traversant | prerouting → **forward** → postrouting | tout le trafic d'un conteneur Docker |

C'est la **destination du paquet** qui décide, pas moi. Première question avant toute règle : « pour moi, de moi, ou à travers moi ? »

## 3. Anatomie d'un ruleset

`table` → `chain` → `rule`.

- **Famille** de la table : `ip` (v4), `ip6` (v6), `inet` (les deux — le choix par défaut). Piège : dans une table `inet`, `ip saddr` ne matche que v4, `ip6 saddr` que v6, `tcp dport` les deux.
- **Déclaration de chaîne :** `type filter hook input priority filter; policy drop;` — type (filter/nat), hook, priorité (plus basse = évaluée avant ; permet de passer avant Docker), policy (défaut = `accept` si omis).
- **Règle :** conditions (ET logique) puis verdict. `accept`/`drop`/`reject` terminent l'évaluation ; **`log` et `counter` ne sont pas des verdicts** — l'évaluation continue.

> `log prefix "DROP "` sans `policy drop` écrit « DROP » dans le journal… et laisse passer le paquet.

## 4. Évaluation d'une chaîne

De haut en bas, **première règle qui matche gagne**, les suivantes ne sont jamais vues. Ordre canonique :

1. `ct state invalid drop`
2. `ct state established,related accept` (99 % du volume : l'évacuer tout de suite)
3. `iif lo accept`
4. les ouvertures autorisées, du plus précis au plus général
5. `log …` puis policy

Un `drop` large placé avant l'`accept` ELK bloque aussi les logs.

## 5. La policy

Verdict appliqué si aucune règle n'a reconnu le paquet. Omise → `accept`.

| | `policy accept` | `policy drop` |
|---|---|---|
| principe | tout passe sauf interdit | tout bloqué sauf autorisé |
| quand j'oublie quelque chose | **une faille**, invisible | **une panne**, visible et journalisée |

Dans les deux cas on oublie quelque chose ; seule la conséquence diffère. `nft list ruleset` affiche **toujours** la policy effective — c'est la vérification fiable.

## 6. Le suivi de connexion (conntrack)

Mémoire des conversations en cours. Quatre états : `new` (c'est ici qu'on décide), `established` (accepter), `related` (erreur ICMP, FTP-data — accepter), `invalid` (jeter en premier).

Les paquets de retour **ne contournent pas** le pare-feu : chacun est évalué, et `established,related accept` les reconnaît tous d'un coup. Sans lui il faudrait `tcp sport 443 accept` en entrée — une porte ouverte.

Squelette de chaîne à connaître par cœur :

```
type filter hook input priority filter; policy drop;
ct state invalid drop
ct state established,related accept
iif lo accept
# ... ouvertures ...
log prefix "IN-DROP " level info limit rate 5/minute
```

## 7. Source et destination

| Chaîne | `saddr` | `daddr` | `dport` |
|---|---|---|---|
| input | la machine distante | moi | un port **chez moi** |
| output | moi | la machine distante | un port **chez le correspondant** |

Question qui résout tout : **qui ouvre la connexion ?** Moi → output, correspondant en `daddr`. Lui → input, il est en `saddr`.

Erreurs symétriques : `ip saddr $ELK` en output ne matche jamais ; `tcp dport 443` en input **ouvre un serveur web** au lieu de réparer les requêtes sortantes.

## 8. Les flux qu'on oublie

1. **Bouclage** : `iif lo` / `oif lo` — *input/output interface*, aucune boucle. `systemd-resolved` écoute sur `127.0.0.53` : sans cette règle, plus de DNS.
2. **DNS** : neuf pannes « le web ne marche plus » sur dix. Séparer : `getent hosts …` (résolution seule) vs `curl -sI https://<IP>` (connexion seule). Nommer les résolveurs : `ip daddr { 8.8.8.8, 1.1.1.1 } udp dport 53 accept` (+ tcp, + le résolveur IPv6 de la box).
3. **NTP** `udp dport 123` — des logs mal horodatés sont inexploitables.
4. **ICMP** : `destination-unreachable`, `time-exceeded`, `packet-too-big` sont vitaux (PMTU). La plupart sont `related`, donc déjà couverts ; `echo-request` et tout le voisinage IPv6 doivent être explicites.

## 9. IPv6

- **Pas de NAT** : la machine a une adresse publique `2a01:…` directement routable. Le pare-feu est le seul rempart.
- **ICMPv6 est indispensable** : types 135/136 (voisinage = ARP), 133/134 (routeur), 2 (packet-too-big). Non liés à une connexion → **pas couverts par `related`** → à autoriser explicitement **dans les deux chaînes**.

```
icmpv6 type { nd-neighbor-solicit, nd-neighbor-advert, nd-router-solicit, nd-router-advert,
              packet-too-big, time-exceeded, parameter-problem, destination-unreachable } accept
```

## 10. Docker

Au démarrage Docker active `ip_forward`, crée ses chaînes (`DOCKER`, `DOCKER-USER`…), ajoute une DNAT en `prerouting` pour chaque `-p`, et une MASQUERADE en `postrouting`.

1. Un `-p 22:2222` rend le port joignable **quelle que soit ma chaîne input** (le paquet est réécrit puis routé → forward).
2. Le trafic **émis** par un conteneur passe par **forward**, pas par output.

Point d'accroche : `DOCKER-USER`, évaluée avant les règles Docker, jamais modifiée par lui :

```bash
sudo iptables -I DOCKER-USER 1 -d 192.168.1.35 -p tcp --dport 5044 -j ACCEPT
sudo iptables -I DOCKER-USER 2 -d 192.168.1.0/24 -j DROP
```

Persistance : Docker recrée ses chaînes à chaque redémarrage → `iptables-persistent`, `ExecStartPost` sur `docker.service`, ou une chaîne nft `forward` à `priority -10`. Et **`flush ruleset` détruit les tables Docker** → préférer `flush table inet filter`.

## 11. Écrire, tester, déboguer

Décrire le flux → écrire la règle (`nft -c -f`) → tester (`curl`/`nc`/`ping`) → **lire le log**.

```
OUT-DROP IN= OUT=wlp3s0 SRC=192.168.1.63 DST=8.8.8.8 PROTO=UDP SPT=51923 DPT=53
```
`PROTO=` et `DPT=` disent exactement quel flux manque. `counter` sur une règle : un compteur à zéro = la règle ne matche pas (aurait révélé le `saddr`/`daddr` en dix secondes).

Seule une **nouvelle** connexion SSH prouve la règle d'entrée. Filet : `sudo systemd-run --on-active=180 --unit=fw-rollback nft flush ruleset`.

## 12. Les sept erreurs qui coûtent une machine

| # | Erreur | Symptôme |
|---|---|---|
| 1 | oublier `policy drop` | aucun — rien n'est filtré |
| 2 | oublier `established` en output | la session SSH gèle |
| 3 | confondre `saddr`/`daddr` | la règle ne matche jamais |
| 4 | oublier le DNS | « Internet ne marche plus » |
| 5 | oublier `iif lo` | le DNS local casse |
| 6 | oublier l'ICMPv6 en sortie | IPv6 intermittent, journal saturé |
| 7 | oublier `systemctl enable nftables` | tout marche… jusqu'au reboot |
