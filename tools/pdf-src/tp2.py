import sys
sys.path.insert(0, "/tmp/claude-1000/-home-ubuserv-CyberProject/376a1b90-229f-487c-98c9-68ff58902afb/scratchpad")
from common import *
from figures import D, WD
from reportlab.graphics.shapes import Rect, Line


def fig_maint():
    d = D(190)
    box(d, 90, 150, 150, 34, "/etc/nftables.conf\n(fermé, permanent)", LBLUE, BLUE, NAVY, 7.6)
    box(d, 90, 60, 150, 44, "include\n\"/etc/nftables.d/*.nft\"", CODEBG, BORDER, NAVY, 7.4, font="DVM")
    arrow(d, 90, 133, 90, 83, DGREY, 1.2)
    txt(d, 90, 108, "dernière ligne", 6.4, DGREY)

    box(d, 300, 150, 190, 34, "/etc/nftables.d/maintenance.nft\nprésent  →  sortie web OUVERTE", LGREEN, GREEN, NAVY, 7.2)
    box(d, 300, 60, 190, 34, "/etc/nftables.d/ vide\n→  sortie web FERMÉE", LRED, RED, colors.HexColor("#5b160e"), 7.2)
    arrow(d, 166, 70, 205, 60, DGREY, 1.1, 4)
    arrow(d, 166, 62, 205, 140, DGREY, 1.1, 4)

    band(d, 418, 105, 88, 30, "systemctl\nreload nftables", NAVY, size=7.2)
    arrow(d, 396, 150, 418, 121, GREEN, 1.1, 4)
    arrow(d, 396, 60, 418, 89, RED, 1.1, 4)
    txt(d, 235, 14, "Un seul fichier permanent. Le mode dépend de la présence d'un second fichier, et d'un reload.",
        7.4, NAVY, "DV-B")
    return d


b = Builder()

# ============================================================ COUVERTURE
b.SP(3.2 * cm)
b.P("TP 2 — Le mode maintenance", "title")
b.P("Ouvrir la sortie Internet à la demande, préparer l'arrivée de Docker", "sub")
b.SP(1 * cm)
b.FIG(fig_maint(), "Le mécanisme à construire dans ce TP.")
b.SP(6)
b.BOX("<b>Format :</b> comme le TP 1, tu fais toutes les manipulations. Chaque exercice donne l'objectif, des "
      "indices, et le test qui prouve que c'est fait. Les livrables sont listés à la fin.", "i")
b.PB()

# ============================================================ 0. ÉTAT DES LIEUX
b.H1("0. État des lieux — ce qui a été fait pour toi")
b.P("Le pare-feu de base est désormais en place sur la machine. Voici précisément ce qui a été fait le "
    "20 septembre, pour que tu saches d'où tu pars.")
b.TABLE(["Élément", "État", "Détail"], [
    ["<font face='DVM'>/etc/nftables.conf</font>", "<font color='#1e7e34'><b>en place</b></font>",
     "Ruleset corrigé du TP 1 + DNS IPv6 de la Freebox (<font face='DVM'>fd0f:ee:b0::1</font>) + une ligne "
     "<font face='DVM'>include \"/etc/nftables.d/*.nft\"</font> en fin de fichier"],
    ["Politique des trois chaînes", "<font color='#1e7e34'><b>drop</b></font>", "input, forward, output"],
    ["<font face='DVM'>nftables.service</font>", "<font color='#1e7e34'><b>enabled + active</b></font>",
     "Le fichier est rechargé à chaque démarrage"],
    ["<font face='DVM'>/etc/nftables.d/</font>", "créé, vide", "Contient seulement un README. C'est là que tu vas travailler"],
    ["Sortie web (80/443)", "<font color='#b26a00'><b>TEMPORAIRE</b></font>",
     "Deux règles ajoutées <b>en mémoire</b>, commentées <font face='DVM'>TEMP-claude-session</font>. "
     "Elles disparaîtront au prochain reload ou reboot"],
    ["Tests effectués", "<font color='#1e7e34'><b>OK</b></font>",
     "DNS résout ; HTTPS sort ; connexion vers une autre VM du LAN bloquée et journalisée ; ping local OK"],
], [4.3 * cm, 2.9 * cm, W - 7.2 * cm])

b.H2("Ce qui reste à faire, et pourquoi ce n'est pas fait")
b.TABLE(["#", "Tâche", "Pourquoi c'est à toi"], [
    ["1", "Ouvrir une <b>nouvelle</b> connexion SSH depuis ton PC pour prouver que la règle d'entrée fonctionne",
     "Je ne peux pas le faire depuis la machine elle-même"],
    ["2", "Redémarrer et vérifier que le pare-feu revient (<font face='DVM'>nft list ruleset</font>)",
     "Un reboot coupe ma session"],
    ["3", "Remplacer les règles TEMP par un vrai mode maintenance", "C'est ce TP"],
    ["4", "Corriger <font face='DVM'>gateway4: 10.0.0.1</font> dans netplan", "Modification réseau : voir exo 0.1, c'est bloquant pour Cowrie"],
    ["5", "Allumer / vérifier la VM ELK (192.168.1.35 ne répond pas)", "Hors de cette machine"],
    ["6", "Identifier 192.168.1.178", "Hors de cette machine"],
], [0.8 * cm, 8.6 * cm, W - 9.4 * cm])

b.H2("Ce que l'incident du jour t'apprend")
b.BOX("Pendant la mise en place, j'ai ajouté la règle 443 en mémoire, puis lancé "
      "<font face='DVM'>systemctl start nftables</font>. Le service exécute <font face='DVM'>nft -f "
      "/etc/nftables.conf</font>, dont la première ligne est <font face='DVM'>flush ruleset</font>. "
      "<b>La règle a été effacée instantanément.</b> Ma session n'a survécu que grâce à "
      "<font face='DVM'>ct state established</font> — les connexions déjà ouvertes — le temps de la remettre.", "w")
b.P("Tu tiens là le principe fondateur de ce TP : <b>tout ce qui doit survivre vit dans un fichier lu par le "
    "service</b>. Une règle ajoutée à la main avec <font face='DVM'>nft add rule</font> est un test, jamais une "
    "configuration.")

b.EXO("Exo 0.1 — Prérequis : la passerelle IPv4 (bloquant pour Cowrie)")
b.P("Regarde la table de routage :")
b.CODE("""
ip route            # IPv4 : il n'y a PAS de "default via ..."
ip -6 route         # IPv6 : "default via fe80::... proto ra"
""")
b.P("Conséquence : <b>toute la sortie Internet de la machine passe en IPv6</b>. Le NTP, apt, ma propre session. "
    "Ça fonctionne par chance, parce que la Freebox distribue de l'IPv6. Mais les attaquants de Cowrie arriveront "
    "par une redirection de port <b>IPv4</b> sur la box — et sans route IPv4 par défaut, la machine ne pourra "
    "pas leur répondre. Cowrie serait injoignable.")
b.P("Cause : <font face='DVM'>gateway4: 10.0.0.1</font> dans <font face='DVM'>/etc/netplan/50-cloud-init.yaml</font>, "
    "une adresse hors de ton sous-réseau. La Freebox répond au ping sur <font face='DVM'>192.168.1.254</font>.")
b.P("Corrige le fichier (syntaxe moderne, <font face='DVM'>gateway4</font> est déprécié), puis applique avec "
    "<font face='DVM'>netplan try</font> — qui annule tout seul au bout de 120 s si tu ne confirmes pas :")
b.CODE("""
# dans le bloc wlp3s0, remplacer la ligne gateway4 par :
      routes:
        - to: default
          via: 192.168.1.254

sudo chown root:root /etc/netplan/50-cloud-init.yaml   # au passage : la clé Wi-Fi est dedans
sudo chmod 600 /etc/netplan/50-cloud-init.yaml
sudo netplan try                                       # puis Entrée pour confirmer
ip route | grep default                                # -> default via 192.168.1.254
curl -4 -sI https://archive.ubuntu.com | head -1       # forcer l'IPv4 : doit répondre 200
""")
b.P("<i>Question :</i> pourquoi <font face='DVM'>netplan try</font> plutôt que <font face='DVM'>netplan apply</font> ? "
    "Même logique que le filet de sécurité du TP 1.")
b.PB()

# ============================================================ 1. CAHIER DES CHARGES
b.H1("1. Cahier des charges du mode maintenance")
b.EXO("Exo 1.1 — Que doit ouvrir le mode maintenance ?")
b.P("Liste les flux nécessaires pour installer Docker puis Cowrie. Complète le tableau <b>avant</b> d'écrire une règle.")
b.TABLE(["Besoin", "Destination", "Port / proto", "IPv4 ? IPv6 ?"], [
    ["Dépôts Ubuntu (apt)", "archive.ubuntu.com, security.ubuntu.com", "tcp/80, tcp/443", "les deux"],
    ["Dépôt Docker", "download.docker.com", "tcp/443", "?"],
    ["Registre d'images", "registry-1.docker.io, *.cloudflare.docker.com", "tcp/443", "?"],
    ["Code de Cowrie", "github.com", "tcp/443", "?"],
    ["Ma session Claude", "api.anthropic.com", "tcp/443", "IPv6 aujourd'hui"],
    ["Le reste du LAN", "192.168.1.0/24", "—", "<b>toujours fermé</b>"],
], [3.6 * cm, 5.4 * cm, 2.8 * cm, W - 11.8 * cm])
b.P("<i>Questions :</i>")
b.NUM([
    "Peut-on écrire une règle par destination (par nom) ? Que fait nftables d'un nom de domaine dans une règle ? "
    "(Indice : <font face='DVM'>nft -c</font> te le dira ; pense à la résolution au moment du chargement et aux "
    "CDN dont l'adresse change.)",
    "Conclusion pratique : on ouvre « 80/443 vers tout sauf le LAN ». En quoi est-ce acceptable pour un mode "
    "<i>temporaire</i>, et pourquoi ce serait inacceptable en permanence sur un honeypot ?",
    "Faut-il ouvrir en IPv4 <b>et</b> en IPv6 ? Regarde <font face='DVM'>getent ahosts download.docker.com</font>.",
])

b.EXO("Exo 1.2 — Le LAN en IPv6")
b.P("Bloquer le LAN en IPv4 c'est <font face='DVM'>ip daddr != 192.168.1.0/24</font>. Mais tes autres machines ont "
    "aussi des adresses IPv6. Lesquelles ?")
b.CODE("""
ip -6 addr show wlp3s0        # ton préfixe global : 2a01:e0a:abe:f8e0::/64
ip -6 route                   # les réseaux directement joignables
""")
b.P("Explique ce que sont ces trois plages, déjà déclarées dans <font face='DVM'>/etc/nftables.conf</font> sous le "
    "nom <font face='DVM'>$LAN6</font> :")
b.TABLE(["Plage", "C'est quoi", "Qui est dedans"], [
    ["<font face='DVM'>2a01:e0a:abe:f8e0::/64</font>", "", ""],
    ["<font face='DVM'>fd0f:ee:b0::/48</font>", "", ""],
    ["<font face='DVM'>fe80::/10</font>", "", ""],
], [4.6 * cm, (W - 4.6 * cm) / 2, (W - 4.6 * cm) / 2])
b.P("<i>Indice :</i> l'une est publique et routable, l'une est « privée » (ULA, l'équivalent du 192.168.x.x), "
    "l'une ne quitte jamais le lien local.")
b.PB()

# ============================================================ 2. LE FICHIER
b.H1("2. Écrire le fichier de maintenance")
b.EXO("Exo 2.1 — /etc/nftables.d/maintenance.nft")
b.P("Tu as un modèle sous les yeux : les deux règles TEMP actuellement en mémoire.")
b.CODE("sudo nft list chain inet filter output | grep TEMP")
b.P("Écris le fichier. Contraintes :")
b.NUM([
    "Il ne contient <b>pas</b> de <font face='DVM'>flush ruleset</font> — il s'ajoute à la table existante.",
    "Il déclare la même table et la même chaîne (<font face='DVM'>table inet filter { chain output { … } }</font>) : "
    "nftables fusionne, il n'écrase pas.",
    "Il n'ouvre <b>rien</b> vers <font face='DVM'>$LAN</font> ni <font face='DVM'>$LAN6</font>. "
    "Attention : peut-il utiliser ces variables ? (Teste. Indice : les <font face='DVM'>define</font> "
    "sont-ils visibles depuis un fichier inclus ?)",
    "Chaque règle porte un <font face='DVM'>counter</font> et un <font face='DVM'>comment \"maintenance\"</font> — "
    "c'est ce qui permettra de vérifier son état en un <font face='DVM'>grep</font>.",
])
b.P("Squelette :")
b.CODE("""
#!/usr/sbin/nft -f
# MODE MAINTENANCE — sortie web ouverte. Ne doit PAS rester chargé en fonctionnement normal.
table inet filter {
    chain output {
        ip  daddr != ____________  tcp dport { 80, 443 } ct state new counter accept comment "maintenance"
        ip6 daddr != { ____________ } tcp dport { 80, 443 } ct state new counter accept comment "maintenance"
    }
}
""")
b.H3("Le piège de l'ordre")
b.P("Un fichier inclus <b>à la fin</b> de <font face='DVM'>nftables.conf</font> ajoute ses règles… à la fin de la "
    "chaîne, donc <b>après</b> la règle <font face='DVM'>log prefix \"OUT-DROP \"</font>. Que se passe-t-il pour un "
    "paquet HTTPS ? (Il passe — mais relis la définition de <font face='DVM'>log</font> dans le cours, chapitre 3.)")
b.P("Trois façons de régler ça. Choisis-en une et justifie :")
b.LI([
    "déplacer le <font face='DVM'>include</font> dans <font face='DVM'>nftables.conf</font> juste avant la ligne "
    "<font face='DVM'>log</font> — est-ce possible à l'intérieur d'un bloc <font face='DVM'>chain</font> ? Teste ;",
    "supprimer la règle <font face='DVM'>log</font> de la chaîne principale et la mettre dans un fichier "
    "<font face='DVM'>/etc/nftables.d/zz-log.nft</font> chargé en dernier grâce à l'ordre alphabétique ;",
    "accepter le bruit dans le journal (mauvaise réponse — dis pourquoi).",
])

b.EXO("Exo 2.2 — Valider sans rien casser")
b.CODE("""
sudo nft -c -f /etc/nftables.conf        # -c : le fichier principal ET les includes sont vérifiés
sudo systemctl reload nftables            # = nft -f /etc/nftables.conf (voir systemctl cat nftables)
sudo nft list chain inet filter output   # les règles "maintenance" sont là ; les TEMP ont disparu
curl -sI https://archive.ubuntu.com | head -1
""")
b.BOX("À ce moment précis, les règles TEMP que j'avais posées n'existent plus, remplacées par les tiennes. "
      "Si <font face='DVM'>curl</font> répond 200 et que je réponds encore, le mode maintenance est fonctionnel. "
      "Si je ne réponds plus : ton fichier a un défaut, et tu as 3 minutes pour le trouver avant que le filet "
      "ne se déclenche — arme-le avant, comme au TP 1.", "w")
b.PB()

# ============================================================ 3. ON / OFF
b.H1("3. L'interrupteur")
b.P("Le mode est défini par la <b>présence</b> du fichier. Il te faut donc un moyen fiable de le faire apparaître "
    "et disparaître, puis de recharger.")
b.EXO("Exo 3.1 — Le script fw-maint")
b.P("Écris <font face='DVM'>/usr/local/sbin/fw-maint</font> avec trois sous-commandes. Squelette à compléter :")
b.CODE("""
#!/bin/bash
# fw-maint on|off|status — bascule le mode maintenance du pare-feu
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
    ______________________________________
    ______________________________________
    ______________________________________
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
""")
b.P("<i>Questions :</i>")
b.NUM([
    "Pourquoi <font face='DVM'>nft -c</font> <b>avant</b> le reload, alors que le reload va de toute façon échouer "
    "si le fichier est faux ? (Indice : que se passe-t-il entre le <font face='DVM'>flush ruleset</font> et "
    "l'erreur de syntaxe ?)",
    "Pourquoi ne pas simplement <font face='DVM'>rm</font> le fichier dans <font face='DVM'>off</font> ?",
    "Que renvoie <font face='DVM'>status</font> juste après un reboot ? Est-ce le comportement voulu pour un "
    "honeypot ?",
])
b.CODE("""
sudo chmod 750 /usr/local/sbin/fw-maint
sudo fw-maint status
""")

b.EXO("Exo 3.2 — Cycle complet de test")
b.BOX("<b>Pendant la phase « off », je ne peux plus t'entendre</b> : ma session a besoin de nouvelles connexions "
      "443. Fais le cycle sans moi, puis remets <font face='DVM'>on</font>. L'application se reconnectera.", "w")
b.TABLE(["Étape", "Commande", "Attendu"], [
    ["1", "<font face='DVM'>sudo fw-maint off</font> puis <font face='DVM'>curl -sI https://archive.ubuntu.com</font>",
     "<font color='#c0392b'><b>échec</b></font> (délai dépassé)"],
    ["2", "<font face='DVM'>sudo dmesg | grep OUT-DROP | tail -3</font>",
     "une ligne <font face='DVM'>PROTO=TCP … DPT=443</font>"],
    ["3", "<font face='DVM'>getent hosts archive.ubuntu.com</font>", "<font color='#1e7e34'><b>résout</b></font> — le DNS n'est pas dans le mode maintenance"],
    ["4", "<font face='DVM'>sudo fw-maint on</font> puis le même <font face='DVM'>curl</font>", "<font color='#1e7e34'><b>200 OK</b></font>"],
    ["5", "<font face='DVM'>sudo fw-maint off &amp;&amp; sudo reboot</font>", "au retour : <font face='DVM'>fw-maint status</font> → NORMAL"],
    ["6", "<font face='DVM'>sudo fw-maint on</font>", "et tu me retrouves"],
], [1.2 * cm, 9.2 * cm, W - 10.4 * cm], keep=True)
b.PB()

# ============================================================ 4. DOCKER
b.H1("4. Installer Docker — et voir ce qu'il fait au pare-feu")
b.P("Mode maintenance activé. Installe Docker depuis le dépôt officiel (pas le paquet "
    "<font face='DVM'>docker.io</font> d'Ubuntu, souvent en retard) :")
b.CODE("""
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] \\
  https://download.docker.com/linux/ubuntu noble stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
""")
b.EXO("Exo 4.1 — Avant / après")
b.CODE("""
sudo nft list tables                       # AVANT docker : une seule table, inet filter
sudo systemctl start docker
sudo nft list tables                       # APRÈS : combien ? lesquelles ?
sudo nft list table ip nat                 # lis les chaînes DOCKER
sudo nft list chain ip filter DOCKER-USER  # ton point d'accroche : vide
sysctl net.ipv4.ip_forward                 # que vaut-il maintenant ?
""")
b.P("Note le nombre de tables, leur famille (<font face='DVM'>ip</font> — pas <font face='DVM'>inet</font> ! "
    "pourquoi c'est important pour l'IPv6 ?), et le nom des chaînes.")

b.EXO("Exo 4.2 — Le piège du flush ruleset")
b.P("Maintenant que Docker a écrit ses tables, fais :")
b.CODE("""
sudo systemctl reload nftables
sudo nft list tables
sudo docker run --rm alpine ping -c1 1.1.1.1
""")
b.P("<i>Questions :</i>")
b.NUM([
    "Que sont devenues les tables de Docker ? Pourquoi ?",
    "Le conteneur a-t-il du réseau ? Quel message ?",
    "Comment le réparer à chaud ? (<font face='DVM'>systemctl restart docker</font>.) Est-ce acceptable de devoir "
    "redémarrer Docker — et donc Cowrie — à chaque <font face='DVM'>fw-maint on/off</font> ?",
])
b.BOX("<b>C'est le piège le plus courant sur une machine Docker + nftables.</b> "
      "<font face='DVM'>flush ruleset</font> efface <i>toutes</i> les tables, y compris celles des autres "
      "programmes. La solution est de ne vider que <b>sa propre</b> table :", "e")
b.CODE("""
# en tête de /etc/nftables.conf, remplacer :
flush ruleset
# par :
table inet filter                  # crée la table si elle n'existe pas (premier démarrage)
flush table inet filter            # et ne vide QUE celle-là
""")
b.P("Applique cette modification, refais le test de l'exo 4.2, et vérifie que les tables Docker survivent au "
    "reload. <i>Question bonus :</i> pourquoi la ligne <font face='DVM'>table inet filter</font> seule est-elle "
    "nécessaire avant le <font face='DVM'>flush table</font> ?")

b.EXO("Exo 4.3 — Deux pare-feux, une priorité")
b.P("Ta chaîne <font face='DVM'>forward</font> est en <font face='DVM'>policy drop</font>. Celle de Docker "
    "(<font face='DVM'>ip filter FORWARD</font>) accepte le trafic de ses conteneurs. Les deux sont accrochées au "
    "même hook, avec la même priorité (<font face='DVM'>filter</font> = 0). Fais le test :")
b.CODE("""
sudo docker run --rm alpine ping -c2 1.1.1.1        # passe ? bloqué ?
sudo dmesg | grep FWD-DROP | tail -3
""")
b.P("<i>Questions :</i>")
b.NUM([
    "Un paquet doit-il être accepté par <b>une</b> des chaînes ou par <b>toutes</b> ? (Cours, chapitre 3, et "
    "exo 0.1 du TP 1 : le même principe s'applique entre deux tables nftables.)",
    "Il te faut donc autoriser, dans <b>ta</b> chaîne <font face='DVM'>forward</font>, ce que tu veux laisser "
    "aux conteneurs. Écris les règles pour : (a) les réponses des connexions établies — déjà là ; (b) ce qui "
    "<i>entre</i> vers un conteneur sur les ports de Cowrie ; (c) ce qui <i>sort</i> d'un conteneur vers ELK ; "
    "(d) ce qui sort d'un conteneur vers Internet — uniquement si le mode maintenance est actif, pour "
    "<font face='DVM'>docker pull</font>. Indice : <font face='DVM'>iifname \"docker0\"</font> et "
    "<font face='DVM'>oifname \"docker0\"</font>.",
    "Où finit alors le rôle de <font face='DVM'>DOCKER-USER</font> ? Est-il encore nécessaire si ta chaîne "
    "<font face='DVM'>forward</font> fait déjà le travail ? Argumente — les deux réponses se défendent.",
])
b.PB()

# ============================================================ 5. LIVRABLES
b.H1("5. Livrables")
b.NUM([
    "Sortie de <font face='DVM'>ip route</font> montrant la route par défaut IPv4 (exo 0.1).",
    "Le tableau de l'exo 1.2 complété.",
    "<font face='DVM'>/etc/nftables.d/maintenance.nft</font>, et ta réponse au piège de l'ordre (exo 2.1).",
    "<font face='DVM'>/usr/local/sbin/fw-maint</font> complet, et les réponses aux trois questions de l'exo 3.1.",
    "Le résultat du cycle de l'exo 3.2, reboot compris.",
    "Réponses aux exos 4.1 à 4.3, avec la nouvelle en-tête de <font face='DVM'>/etc/nftables.conf</font> et "
    "ta chaîne <font face='DVM'>forward</font> finale.",
    "Sortie de <font face='DVM'>sudo nft list ruleset</font> une fois Docker installé et le mode maintenance "
    "<b>désactivé</b> — c'est l'état de repos de ta future machine honeypot.",
])
b.BOX("<b>Étape suivante</b> après ce TP : Cowrie lui-même — le conteneur, la redirection 22 → 2222, la "
      "configuration de sortie vers Filebeat/Logstash, et le durcissement du conteneur (utilisateur non root, "
      "système de fichiers en lecture seule, pas de capacités). Ta chaîne <font face='DVM'>forward</font> de "
      "l'exo 4.3 sera le point de départ.", "g")

build(b.story, "/home/ubuserv/CyberProject/TP2-mode-maintenance.pdf",
      "TP 2 — Mode maintenance", "TP 2 — Mode maintenance nftables et préparation Docker", "nftables, docker")
print("OK")
