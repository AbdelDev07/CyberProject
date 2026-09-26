# Cours — Honeypots : concepts, isolation et chaîne de collecte

> Version complète avec schémas : [pdf/Cours-honeypots.pdf](../pdf/Cours-honeypots.pdf).

## 1. À quoi sert un honeypot

Un système **sans utilité légitime**, placé là pour être attaqué. C'est cette absence d'usage normal qui fait sa valeur :

> Sur un serveur normal, distinguer une attaque du trafic légitime est difficile (faux positifs). Sur un honeypot, il n'y a pas de trafic légitime : **tout ce qui arrive est suspect par définition**.

Ce que ça apporte : comprendre la pression réelle sur une IP exposée, connaître les identifiants attaqués, observer les modes opératoires, récupérer les URL de distribution.

Ce que ça n'apporte pas : aucune protection (c'est un capteur, pas un bouclier) ; peu de ciblage (surtout des robots) ; un coût de surveillance — un honeypot dont personne ne lit les journaux est un risque net.

## 2. Les niveaux d'interaction

| Niveau | Principe | Exemples | Risque | Ce qu'on apprend |
|---|---|---|---|---|
| Faible | ouvre des ports, répond des bannières | portspoof, honeyd | nul | qui scanne |
| **Moyen** | **émule** un service complet, n'exécute rien | **Cowrie**, Dionaea | faible | identifiants, commandes, charges |
| Fort | vraie machine réellement compromise | VM sacrificielle | **élevé** | tout, y compris 0-day |

Cowrie donne l'essentiel de l'information pour une fraction du risque. Quand l'attaquant tape `rm -rf /`, Cowrie consulte une arborescence factice en mémoire et renvoie une réponse plausible — rien n'atteint le vrai système de fichiers.

**Limite :** un décor se détecte. Cowrie arrête les robots et les opérateurs pressés, pas quelqu'un qui cherche activement un honeypot.

## 3. La règle d'or : le confinement sortant

> Un honeypot est fait pour être compromis. La seule question qui compte est : **et après ?**

Mal confiné, il devient un point d'appui pour attaquer ton réseau, un relais pour attaquer des tiers (depuis ton IP), ou un nœud de botnet.

**Sortant : tout interdit, sauf ce qui est explicitement nécessaire.** Ici : une destination, un port.

### Où l'écrire

| Si le honeypot tourne… | Son trafic passe par | Où écrire la règle |
|---|---|---|
| directement sur l'hôte | `input`/`output` | chaîne `output` |
| **dans un conteneur** | `forward` | chaîne `forward` (et/ou `DOCKER-USER`) |
| dans une VM pontée | `forward` de l'hyperviseur | sur l'hyperviseur |

### La vérification n'est pas facultative

```bash
docker run --rm --network <reseau_honeypot> alpine sh -c '
  nc -z 192.168.1.254 80 ; nc -z 192.168.1.33 22 ; nc -z 1.1.1.1 443'
dmesg | grep FWD-CONTAINER-DROP
```

> Un pare-feu qu'on n'a pas testé depuis l'intérieur de la zone qu'il confine n'est pas un pare-feu : c'est une intention.

## 4. La crédibilité du leurre

| Élément | À éviter | Préférer |
|---|---|---|
| Nom d'hôte | `honeypot`, `cowrie`, `test` | `srv-prod-01`, `nas01` |
| Bannière | version exotique ou incohérente | version courante, légèrement ancienne |
| Identifiants | tout accepter | liste de mots de passe faibles réalistes |
| Système de fichiers | arborescence par défaut | quelques fichiers personnalisés, historique plausible |

**Incohérence présente sur notre machine :** port 22 annonce `OpenSSH_8.9p1`, port 2727 annonce `9.6p1`. Un scan des deux révèle deux systèmes. Aligner règle le problème, au prix d'un leurre moins attirant.

## 5. De la capture au renseignement

Le parseur `ndjson` dans Filebeat fait toute la différence :

| Sans parseur | Avec parseur |
|---|---|
| un champ `message` avec tout le JSON | `src_ip`, `username`, `password`, `input`… interrogeables |
| « cherche les lignes contenant 192.168.1.5 » | « top 10 des mots de passe par heure, groupés par pays » |

Quatre questions pour le tableau de bord : **qui** (sources, volume), **quoi** (identifiants, taux de réussite), **comment** (commandes après connexion), **vers où** (URL de téléchargement — la donnée la plus précieuse).

> Un tableau vide ressemble à « rien ne se passe ». Prévois une alerte sur l'absence d'événements.

## 6. Avant d'exposer sur Internet

| Délai après ouverture du port 22 | Ce qui arrive |
|---|---|
| quelques minutes | premiers scans automatisés |
| première heure | premières attaques par dictionnaire |
| premier jour | ~1000 tentatives ; premières connexions réussies |
| première semaine | charges téléchargées, persistance, recrutement botnet |

Liste de contrôle : sortant confiné **et testé depuis l'intérieur** · aucun accès au reste du réseau · vrai SSH ailleurs, filtré, avec fail2ban · fail2ban ne surveille **pas** les ports du honeypot · rotation des journaux · durée de conservation décidée · conditions de l'opérateur vérifiées · supervision du honeypot lui-même.

### Juridique et éthique

- **Tu es responsable du trafic sortant de ton IP** — d'où le confinement strict.
- **Collecter n'est pas attaquer** : observer ce qui vient chez toi est légitime ; sonder en retour ne l'est pas.
- **Les adresses IP sont des données personnelles** (RGPD) : durée de conservation limitée et décidée à l'avance.
- **Les échantillons sont du code malveillant réel.** Ici la question ne se pose pas : sortie fermée, seule l'URL est enregistrée.

## 7. Pour aller plus loin

Tarpit SSH (`endlessh`) · autres protocoles (Dionaea, Conpot) · corrélation avec des listes de réputation · partage communautaire · honeypot à forte interaction sur réseau isolé.

---

> **La leçon transversale du projet.** La partie difficile n'a jamais été d'installer Cowrie — c'est une commande. Elle a été de garantir ce que le honeypot **ne peut pas** faire : les cinq bugs du TP 1, le piège du `flush ruleset`, le décalage des ports par le DNAT, l'exposition IPv6 involontaire. Ce sont toujours les interdictions qui sont difficiles à écrire, et il faut les prouver plutôt que les supposer.
