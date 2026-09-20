import sys
sys.path.insert(0, "/tmp/claude-1000/-home-ubuserv-CyberProject/376a1b90-229f-487c-98c9-68ff58902afb/scratchpad")
from common import *
import figures as F

b = Builder()

# ============================================================ COUVERTURE
b.SP(3.4 * cm)
b.P("Correction du TP", "title")
b.P("Pare-feu d'un honeypot Cowrie — nftables", "sub")
b.SP(14)
b.P("Corrigé établi à partir du fichier réellement présent sur la machine<br/>"
    "et des journaux du noyau, le 18 septembre 2026.", "sub")
b.SP(1.1 * cm)
b.FIG(F.fig_topologie(), "Le laboratoire tel qu'il ressort de ton cahier des charges et des journaux de la machine.")
b.SP(6)
b.BOX("<b>Ce document est une correction, pas un jugement.</b> Les erreurs commises ici — la "
      "<i>policy</i> par défaut, l'inversion source/destination, le DNS oublié — sont exactement celles que tout le "
      "monde fait en écrivant son premier pare-feu à état. Elles sont toutes instructives, et tes journaux en "
      "gardent la trace, ce qui permet de les corriger avec des preuves plutôt qu'avec des suppositions.", "i")
b.PB()

# ============================================================ SYNTHÈSE
b.H1("Synthèse")
b.P("Voici ce qui est acquis et ce qui reste à travailler. Le détail de chaque point suit dans les sections "
    "suivantes.")

b.H2("Ce qui est juste")
b.TABLE(["Point", "Commentaire"], [
    ["Structure du fichier", "Shebang, <font face='DVM'>flush ruleset</font>, <font face='DVM'>define</font>, "
     "table <font face='DVM'>inet</font>, trois chaînes : la charpente est correcte."],
    ["Usage des variables", "<font face='DVM'>$ADMIN_IP</font>, <font face='DVM'>$ELK_IP</font>, "
     "<font face='DVM'>$SSH_PORT</font> — bonne habitude, le fichier se relit et se modifie sans risque."],
    ["<font face='DVM'>ct state invalid drop</font> en tête", "Placé au bon endroit, avant tout le reste."],
    ["Restriction du SSH par IP source", "<font face='DVM'>tcp dport $SSH_PORT ip saddr $ADMIN_IP accept</font> : "
     "correct, et <b>ça a fonctionné</b> (voir la section « ce que tes journaux racontent »)."],
    ["Règles de journalisation", "<font face='DVM'>log prefix … limit rate</font> dans les deux chaînes : "
     "c'est grâce à elles que ce corrigé a pu être écrit."],
    ["Réponse à l'exercice 2.1", "Tu as trouvé le bug demandé : il manque "
     "<font face='DVM'>ct state established,related accept</font> dans la chaîne output. <b>C'était bien la réponse.</b>"],
    ["Réponse à l'exercice 3.1", "L'explication du filet de sécurité est juste et complète."],
], [4.6 * cm, W - 4.6 * cm])

b.H2("Ce qui est à revoir")
b.TABLE(["Point", "Gravité", "Section"], [
    ["Aucune <font face='DVM'>policy drop</font> : le pare-feu n'interdit rien", "<b>Critique</b>", "§3 bug 1"],
    ["Inversion <font face='DVM'>saddr</font> / <font face='DVM'>daddr</font> sur la règle ELK", "<b>Critique</b>", "§3 bug 2"],
    ["Confusion sur le rôle de chaque chaîne (ports 80/443/53 en entrée)", "Majeur", "§3 bug 4"],
    ["Chaîne <font face='DVM'>forward</font> vide et ouverte", "Majeur", "§3 bug 3"],
    ["IPv6 : NDP bloqué, et adresse publique non prise en compte", "Majeur", "§3 bug 6"],
    ["<font face='DVM'>nftables.service</font> désactivé : rien ne survit au redémarrage", "Majeur", "§3 bug 7"],
    ["Signification de <font face='DVM'>iif lo</font>", "À clarifier", "§2, exo 2.1"],
    ["Rôle de <font face='DVM'>ct state established</font>", "À clarifier", "§2, exo 2.1"],
], [W - 6.2 * cm, 2.4 * cm, 3.8 * cm])

b.BOX("<b>En une phrase :</b> le fichier est bien construit et bien commenté, mais dans son état actuel il "
      "<b>laisse tout passer</b>, parce qu'il manque la seule ligne qui transforme une liste d'autorisations en "
      "pare-feu : <font face='DVM'>policy drop</font>.", "w")
b.PB()

# ============================================================ §1 CORRECTION DES EXOS
b.H1("1. Correction des exercices")
b.P("Tes réponses sont reprises en bleu, telles que tu les as écrites.")

# --- 0.1
b.EXO("Exercice 0.1 — Un seul moteur ?")
b.QUOTE("J'ai le même retour pour « iptable » avec rien dedans, par contre j'imagine que on peut avoir des règles "
        "qu'on ne voit pas dans le legacy ou inversement mais les autres oui ? Je veux bien une explication.")
b.P("<b>Ton intuition est juste.</b> Voici le mécanisme exact.")
b.P("Le noyau Linux contient <b>deux moteurs de filtrage distincts</b>, hérités de deux époques :")
b.LI([
    "<font face='DVM'>x_tables</font> — l'ancien, piloté par <font face='DVM'>iptables-legacy</font> ;",
    "<font face='DVM'>nf_tables</font> — le moderne, piloté par <font face='DVM'>nft</font>.",
])
b.P("Sur Ubuntu 24.04, la commande <font face='DVM'>iptables</font> est en réalité un <i>traducteur</i> : elle accepte "
    "l'ancienne syntaxe mais écrit dans <font face='DVM'>nf_tables</font>. C'est ce que dit la mention "
    "<font face='DVM'>(nf_tables)</font> dans <font face='DVM'>iptables -V</font>. D'où le tableau :")
b.TABLE(["Commande", "Lit / écrit dans", "Voit les règles de nft ?"], [
    ["<font face='DVM'>nft list ruleset</font>", "nf_tables", "<font color='#1e7e34'><b>oui</b></font>"],
    ["<font face='DVM'>iptables -L</font>", "nf_tables (traduction)", "<font color='#1e7e34'><b>oui</b></font>, mais affichées en syntaxe iptables"],
    ["<font face='DVM'>iptables-legacy -L</font>", "x_tables", "<font color='#c0392b'><b>non</b></font> — un univers séparé"],
], [5.2 * cm, 4.4 * cm, W - 9.6 * cm])
b.H3("Pourquoi c'est dangereux")
b.P("Les deux moteurs s'accrochent aux <b>mêmes points du noyau</b> et sont consultés <b>tous les deux</b>. Un paquet "
    "doit donc être accepté par les deux pour passer. Conséquence : une règle "
    "<font face='DVM'>DROP</font> oubliée dans <font face='DVM'>x_tables</font> bloque le trafic, "
    "et tu peux relire ton <font face='DVM'>nft list ruleset</font> pendant des heures sans jamais la voir. "
    "C'est un des grands classiques du dépannage réseau sous Linux.")
b.CODE("""
# le réflexe de diagnostic, à faire une fois :
sudo iptables-legacy -L -n -v          # doit être vide
sudo ip6tables-legacy -L -n -v         # idem, on oublie souvent l'IPv6
lsmod | grep -E 'ip_tables|nf_tables'  # quel moteur est réellement chargé
""")

# --- 1.1.1
b.EXO("Exercice 1.1 (1) — L'architecture d'envoi des logs")
b.QUOTE("Je ne comprends pas.")
b.P("C'est la question la plus importante du TP, parce que la réponse détermine <b>dans quelle chaîne</b> tu dois "
    "écrire ta règle. Cowrie produit un journal au format JSON. Il existe deux façons de l'acheminer vers ELK :")
b.TABLE(["", "Chemin A — via Filebeat <font color='#1e7e34'>(ton choix)</font>", "Chemin B — envoi direct"], [
    ["Qui écrit", "Cowrie écrit dans un fichier : <font face='DVM'>log/cowrie.json</font>",
     "Cowrie utilise son greffon <font face='DVM'>[output_elasticsearch]</font>"],
    ["Qui envoie", "<b>Filebeat</b>, installé sur la machine hôte, lit le fichier",
     "<b>Cowrie lui-même</b>, depuis l'intérieur du conteneur"],
    ["Vers quoi", "<b>Logstash</b>, port <b>5044</b> (protocole Beats)",
     "<b>Elasticsearch</b>, port <b>9200</b> (HTTP)"],
    ["Chaîne nftables concernée",
     "<font color='#c0392b'><b>output</b></font> — c'est un processus de la machine qui ouvre la connexion",
     "<font color='#b26a00'><b>forward</b></font> — c'est le conteneur qui ouvre la connexion, le paquet traverse la machine"],
], [3.1 * cm, (W - 3.1 * cm) / 2, (W - 3.1 * cm) / 2])
b.BOX("Tu as renseigné <font face='DVM'>ELK_PORT = 5044</font> : tu as donc choisi le <b>chemin A</b>. Ta règle a "
      "bien sa place dans la chaîne <font face='DVM'>output</font>. Retiens simplement que si un jour tu passes au "
      "chemin B, la règle devra migrer dans <font face='DVM'>forward</font> — sinon elle ne servira à rien.", "i")
b.BOX("<b>À vérifier de ton côté :</b> depuis la machine, <font face='DVM'>192.168.1.35</font> ne répond ni au ping "
      "ni sur le port 5044. Soit la VM ELK est éteinte, soit son adresse a changé, soit Logstash n'écoute pas encore. "
      "Tant que ce point n'est pas réglé, tu ne pourras pas valider la règle de sortie en conditions réelles.", "w")

# --- 1.1.2
b.EXO("Exercice 1.1 (2) — Le port d'exposition de Cowrie")
b.QUOTE("D'après le cahier des charges c'est le port 22 qui est utilisé par Cowrie.")
b.P("<b>Correct sur le principe</b>, avec une nuance de mise en œuvre qui compte. Cowrie ne doit "
    "<b>jamais tourner en root</b> : c'est un logiciel dont le métier est de se faire attaquer. Or les ports "
    "inférieurs à 1024 exigent des privilèges root. La pratique est donc :")
b.LI([
    "Cowrie écoute en interne sur un port haut, <font face='DVM'>2222</font>, sans privilège ;",
    "on <b>redirige</b> 22 vers 2222, soit par Docker (<font face='DVM'>-p 22:2222</font>), soit par une règle de "
    "traduction d'adresse en nftables.",
])
b.P("Le port 22 est donc le port <i>vu de l'extérieur</i>, pas celui sur lequel le programme écoute. "
    "Et comme tu as déplacé ton vrai SSH sur 2727, le 22 est effectivement libre : c'est un bon choix, "
    "et c'est précisément l'intérêt d'avoir déménagé le SSH d'administration.")

# --- 1.1.3
b.EXO("Exercice 1.1 (3) — La sortie Internet")
b.QUOTE("Quand je le décide.")
b.P("<b>C'est la bonne décision pour un honeypot</b>, et elle est cohérente avec ta réponse à l'exercice 1.2. "
    "Elle a deux conséquences concrètes que tu dois assumer :")
b.NUM([
    "Pas de règle <font face='DVM'>tcp dport {80, 443}</font> dans le fichier permanent. Tu la charges "
    "ponctuellement, par un fichier séparé (fourni en §5).",
    "<font face='DVM'>unattended-upgrades</font> ne pourra plus faire son travail. Soit tu l'acceptes et tu mets "
    "à jour à la main pendant tes fenêtres de maintenance, soit tu le désactives pour qu'il cesse d'échouer en "
    "silence tous les jours.",
])

# --- 1.2
b.EXO("Exercice 1.2 — La question piège")
b.QUOTE("Les fichiers sont enregistrés dans un répertoire spécifique -> download_path = dl")
b.P("<b>Exact, mais c'est la moitié de la réponse</b> — et la moitié manquante est justement le piège.")
b.BOX("Pour <i>enregistrer</i> le fichier dans <font face='DVM'>dl/</font>, Cowrie doit d'abord "
      "<b>le télécharger pour de vrai</b>. Le <font face='DVM'>wget</font> de l'attaquant est émulé côté shell, "
      "mais la requête HTTP sort réellement de ta machine, avec ton adresse IP publique.", "e")
b.P("Les conséquences :")
b.LI([
    "<b>Ton adresse IP apparaît</b> dans les journaux du serveur qui héberge le logiciel malveillant. Tu te signales "
    "à l'attaquant et à son infrastructure.",
    "Tu <b>télécharges volontairement du code malveillant</b> sur une machine de ton réseau domestique. C'est le but "
    "recherché quand on collecte des échantillons — c'est un risque inutile quand on apprend.",
    "Selon ton hébergeur ou ton opérateur, du trafic sortant vers des infrastructures malveillantes peut déclencher "
    "un signalement.",
])
b.P("<b>La bonne réponse en deux phrases :</b> non, un honeypot d'apprentissage ne doit pas pouvoir sortir sur "
    "Internet ; Cowrie enregistrera alors l'URL tentée dans son journal — ce qui est l'information intéressante — "
    "sans jamais récupérer le fichier. On n'ouvre la sortie que si l'on fait de la collecte d'échantillons de façon "
    "délibérée, et de préférence depuis une machine isolée et jetable.")
b.PB()

# --- 2.1
b.EXO("Exercice 2.1 — Les annotations ligne par ligne")
b.P("Tu as annoté chaque ligne. Je reprends chacune de tes annotations.")

b.H3("« table inet filter » — table sur l'IPv4 et v6, je sais pas à quoi ça correspond")
b.P("<font face='DVM'>inet</font> est une <b>famille d'adresses</b>. Elle indique quel type de trafic la table voit :")
b.TABLE(["Famille", "Voit", "Quand l'utiliser"], [
    ["<font face='DVM'>ip</font>", "IPv4 seulement", "Anciennes configurations"],
    ["<font face='DVM'>ip6</font>", "IPv6 seulement", "Anciennes configurations"],
    ["<font face='DVM'>inet</font>", "IPv4 <b>et</b> IPv6", "<b>Le choix par défaut aujourd'hui</b> — une seule règle pour les deux"],
    ["<font face='DVM'>bridge</font> / <font face='DVM'>netdev</font>", "Trafic ponté / au ras de la carte réseau", "Cas avancés"],
], [3.2 * cm, 4.2 * cm, W - 7.4 * cm])
b.BOX("<b>Le piège de <font face='DVM'>inet</font>, et tu es tombé dedans :</b> la table voit les deux protocoles, "
      "mais une règle qui commence par <font face='DVM'>ip saddr</font> ne concerne que l'IPv4, et "
      "<font face='DVM'>ip6 saddr</font> que l'IPv6. En revanche <font face='DVM'>tcp dport 5044</font>, qui ne "
      "mentionne aucune version, s'applique <b>aux deux</b>. Écrire une table <font face='DVM'>inet</font> ne suffit "
      "donc pas à couvrir l'IPv6 : il faut y penser règle par règle.", "w")

b.H3("« iif lo accept » — fais repartir la règle depuis le début, je ne comprends pas trop")
b.BOX("<b>C'est la seule erreur d'interprétation vraiment gênante de ta copie</b>, parce qu'elle porte sur une "
      "notation qui revient partout. Il n'y a ici aucune boucle et aucun retour en arrière.", "e")
b.TABLE(["Notation", "Se lit", "Signifie"], [
    ["<font face='DVM'>iif</font>", "<i>input interface</i>", "l'interface <b>par laquelle le paquet est entré</b>"],
    ["<font face='DVM'>oif</font>", "<i>output interface</i>", "l'interface <b>par laquelle le paquet va sortir</b>"],
    ["<font face='DVM'>lo</font>", "<i>loopback</i>", "l'interface de bouclage : 127.0.0.1 et ::1, la machine qui se parle à elle-même"],
], [2.6 * cm, 3.4 * cm, W - 6 * cm])
b.P("<font face='DVM'>iif lo accept</font> se lit donc : <b>« si ce paquet est arrivé par l'interface de bouclage, "
    "accepte-le »</b>. Et c'est vital : sur ta machine, <font face='DVM'>systemd-resolved</font> écoute sur "
    "<font face='DVM'>127.0.0.53</font>. Chaque résolution de nom passe par le bouclage. Sans cette règle, avec une "
    "<font face='DVM'>policy drop</font>, tu perds la résolution DNS de toute la machine.")

b.H3("« ct state established,related accept » — les réponses se font automatiquement, sans passer par le pare-feu ?")
b.P("<b>Non</b>, et la nuance est importante : <b>chaque paquet</b>, sans exception, traverse le pare-feu et est "
    "évalué règle par règle. Ce que fait cette règle, c'est <b>reconnaître d'un coup</b> tous les paquets qui "
    "appartiennent à une conversation déjà autorisée, au lieu de t'obliger à écrire une règle inverse pour chacune.")
b.P("Sans elle, pour autoriser une simple requête web, il faudrait écrire : « laisse sortir le paquet vers le port "
    "443 », puis « laisse entrer les paquets qui viennent du port 443 de n'importe quelle adresse » — ce qui revient "
    "à ouvrir grand la porte d'entrée. Le suivi de connexion supprime ce dilemme : c'est ce qui distingue un "
    "pare-feu <b>à état</b> d'un simple filtre.")

b.H3("« Il manque : ct state established,related accept » dans la chaîne output")
b.BOX("<b>Bonne réponse. C'était exactement le bug recherché.</b>", "g")
b.P("Le scénario concret, si l'on applique ce ruleset pendant une session SSH :")
b.NUM([
    "Ton PC envoie un paquet SYN vers 192.168.1.63:2727. La chaîne <font face='DVM'>input</font> l'accepte : "
    "la règle <font face='DVM'>tcp dport 2727 ip saddr 192.168.1.33</font> matche.",
    "<font face='DVM'>sshd</font> répond par un SYN-ACK. Ce paquet est <b>émis</b> par la machine : il traverse la "
    "chaîne <font face='DVM'>output</font>.",
    "Dans <font face='DVM'>output</font>, aucune règle ne le matche : ce n'est ni du bouclage, ni du trafic vers "
    "l'ELK. Il tombe sur <font face='DVM'>policy drop</font>.",
    "La réponse ne part jamais. <b>Ta session gèle et tu perds la machine</b> — d'où l'exercice 3.1.",
])

# --- 3.1
b.EXO("Exercice 3.1 — Le filet de sécurité")
b.QUOTE("Commande qui attend 2 minutes et supprime toutes les règles si on ne la kill pas ; ça nous permet d'avoir "
        "une sécu si on s'est bloqué. Pourquoi utiliser bash -c ?")
b.P("<b>L'explication du principe est juste et complète.</b> Reste ta question sur "
    "<font face='DVM'>bash -c</font>, qui est une vraie subtilité du shell :")
b.CODE("""
sudo sleep 120 && nft flush ruleset          # PIÈGE
#    \\_________/    \\_______________/
#    exécuté en root   exécuté par TON shell, sans sudo -> "Permission denied"

sudo bash -c 'sleep 120 && nft flush ruleset'   # CORRECT
#    \\_______________________________________/
#    un shell root exécute toute la chaîne, sudo compris
""")
b.P("Le <font face='DVM'>&amp;&amp;</font> est interprété par le shell <i>appelant</i>. "
    "<font face='DVM'>sudo</font> ne s'applique qu'à la première commande. En passant toute la ligne à un shell "
    "lancé en root, l'ensemble hérite des privilèges. Les <b>apostrophes simples</b> sont indispensables : elles "
    "empêchent ton propre shell d'interpréter la chaîne avant de la transmettre.")
b.H3("L'alternative plus propre")
b.CODE("""
sudo systemd-run --on-active=120 --unit=fw-rollback nft flush ruleset
# ... tester ...
sudo systemctl stop fw-rollback.timer      # annuler le filet une fois rassuré
""")
b.P("Avantage décisif : la tâche est confiée à systemd, donc elle <b>survit à la fermeture du terminal</b>. "
    "Avec <font face='DVM'>&amp;</font>, si ta session SSH tombe — ce qui est précisément le scénario contre lequel "
    "tu te protèges — le processus peut être tué avec elle, et le filet disparaît au pire moment.")
b.PB()

# ============================================================ §2 JOURNAUX
b.H1("2. Ce que tes journaux racontent")
b.P("Tes règles <font face='DVM'>log</font> ont fonctionné : le noyau a conservé 777 lignes. Elles racontent "
    "précisément ce qui s'est passé pendant le TP. C'est la partie la plus utile de ce corrigé, parce qu'elle "
    "remplace les hypothèses par des faits.")
b.CODE("sudo dmesg | grep -E 'IN-DROP|OUT-DROP'")
b.TABLE(["Nombre", "Sens", "Protocole", "Ce que ça signifie"], [
    ["588", "sortant", "ICMPv6 types 135/136", "Découverte de voisins IPv6 bloquée — <b>IPv6 cassé</b> (bug 6)"],
    ["111", "sortant", "UDP port 53", "<b>Résolution DNS bloquée</b> — la vraie cause de ton « le web ne marche pas »"],
    ["54", "sortant", "TCP port 53", "Idem, requêtes DNS en TCP vers <font face='DVM'>fd0f:ee:b0::1</font>"],
    ["16", "entrant", "TCP port 2727", "Tentatives SSH <b>depuis 192.168.1.178</b> — ta règle a fait son travail"],
    ["8", "entrant", "ICMPv6", "Voisinage IPv6, côté entrant"],
], [1.8 * cm, 1.9 * cm, 3.5 * cm, W - 7.2 * cm])

b.H2("Le diagnostic du « les requêtes web ne fonctionnent pas »")
b.BOX("Tu as écrit dans ta copie : <i>« les requêtes web ne fonctionnent pas, j'ai fait n'importe quoi à la fin, "
      "j'ai dupliqué les accept 443 et dns »</i>. Les journaux montrent que le problème n'était "
      "<b>pas le web</b>, et donc que la correction ne pouvait pas être dans les règles 443.", "w")
b.FIG(F.fig_dns(), "Une requête web commence toujours par une requête DNS. Si le DNS est bloqué, "
                   "le navigateur ou curl échoue avant même d'avoir tenté d'ouvrir le port 443.")
b.P("Les 111 paquets UDP/53 refusés en sortie sont datés entre 9440 et 9516 secondes d'activité de la machine, "
    "soit une fenêtre de 76 secondes : exactement le moment où tu testais avec une "
    "<font face='DVM'>policy drop</font> active et sans règle DNS. Ce que ton système essayait d'atteindre :")
b.TABLE(["Destination", "Protocole", "Paquets refusés"], [
    ["<font face='DVM'>fd0f:ee:b0::1</font> (DNS de la Freebox, en IPv6)", "TCP/53", "54"],
    ["<font face='DVM'>fd0f:ee:b0::1</font>", "UDP/53", "39"],
    ["<font face='DVM'>8.8.8.8</font>", "UDP/53", "36"],
    ["<font face='DVM'>1.1.1.1</font>", "UDP/53", "36"],
], [W - 6.6 * cm, 3 * cm, 3.6 * cm])
b.BOX("<b>La leçon, et c'est la plus rentable du TP :</b> le symptôme visible (« le web est cassé ») désigne "
      "rarement la règle fautive. Le journal, lui, donne le protocole et le port exacts du paquet refusé. "
      "<b>Lis le journal avant de modifier une règle</b> — sinon on ajoute des autorisations au hasard, ce qui "
      "affaiblit le pare-feu sans résoudre le problème.", "i")

b.H2("Les tentatives SSH depuis 192.168.1.178")
b.P("Seize paquets à destination du port 2727 ont été refusés, tous venant de "
    "<font face='DVM'>192.168.1.178</font>. C'est une bonne et une moins bonne nouvelle :")
b.LI([
    "<b>Bonne</b> : ta règle <font face='DVM'>ip saddr $ADMIN_IP</font> fonctionne exactement comme prévu. Une "
    "machine du réseau qui n'est pas ton poste d'administration ne peut pas atteindre le SSH.",
    "<b>À éclaircir</b> : sais-tu ce qu'est <font face='DVM'>192.168.1.178</font> ? Si c'est un autre de tes "
    "appareils, tout va bien. Sinon, une machine de ton réseau cherche le SSH — ce qui mérite un coup d'œil.",
])
b.CODE("""
ip neigh | grep 192.168.1.178      # adresse MAC -> constructeur de l'appareil
sudo nmap -sn 192.168.1.0/24       # inventaire du réseau local
""")
b.PB()

# ============================================================ §3 LES BUGS
b.H1("3. Analyse de ton ruleset")
b.P("Chaque bug est présenté ainsi : ce que tu as écrit, ce que fait réellement le noyau, et la correction.")

# ---- bug 1
b.H2("Bug 1 — Aucune policy : le pare-feu n'interdit rien")
b.P("<b>Gravité : critique.</b> C'est la clé de voûte manquante.")
b.CODE("""
# ce que tu as écrit
type filter hook input priority 0;

# ce que le noyau a retenu (sortie de: sudo nft list ruleset)
type filter hook input priority filter; policy accept;
                                        ^^^^^^^^^^^^^
""")
b.P("Quand la <font face='DVM'>policy</font> n'est pas précisée, nftables retient "
    "<font face='DVM'>accept</font>. Ta chaîne est donc une liste d'autorisations… suivie d'une autorisation "
    "générale. Tout ce que tu n'as pas prévu passe quand même.")
b.FIG(F.fig_policy(), "À gauche ce que fait ton fichier aujourd'hui, à droite ce qu'il devrait faire. "
                      "Les règles sont identiques : seule la dernière ligne change tout.")
b.BOX("Effet pervers : tes règles <font face='DVM'>log</font> continuent d'écrire « IN-DROP » et « OUT-DROP » dans "
      "le journal. <b>Le préfixe ment</b> : <font face='DVM'>log</font> journalise mais ne rend aucun verdict, et le "
      "paquet poursuit son chemin jusqu'à la <i>policy</i>, qui l'accepte. C'est pour cela que tout « fonctionne » "
      "sur ta machine en ce moment.", "w")
b.P("<b>Correction :</b>")
b.CODE("type filter hook input priority filter; policy drop;")
b.P("Au passage, <font face='DVM'>priority filter</font> est préférable à <font face='DVM'>priority 0</font> : "
    "c'est le même nombre, mais le mot-clé reste juste si les conventions changent, et il se relit mieux.")

# ---- bug 2
b.H2("Bug 2 — Inversion de la source et de la destination")
b.P("<b>Gravité : critique.</b> La règle la plus importante de ton pare-feu — celle qui justifie tout le TP — ne "
    "peut jamais matcher.")
b.CODE("""
# ton fichier, chaîne output :
tcp dport $ELK_PORT ip saddr $ELK_IP accept
                    ^^^^^^^^^^^^^^^^
                    « le paquet VIENT de 192.168.1.35 »
""")
b.P("Dans la chaîne <font face='DVM'>output</font>, le paquet est <b>émis par ta machine</b> : sa source est "
    "toujours <font face='DVM'>192.168.1.63</font>. La condition <font face='DVM'>ip saddr 192.168.1.35</font> est "
    "donc impossible à satisfaire. Avec une <font face='DVM'>policy drop</font>, tes logs ne seraient jamais partis "
    "vers ELK.")
b.FIG(F.fig_saddr_daddr(), "Le même couple d'adresses s'inverse selon la chaîne. C'est le point de vue de la "
                           "machine qui compte, jamais celui du service distant.")
b.BOX("<b>Le réflexe à acquérir :</b> avant d'écrire une règle, demande-toi « <i>qui ouvre la connexion ?</i> ». "
      "Si c'est ma machine → chaîne <font face='DVM'>output</font>, le correspondant est en "
      "<font face='DVM'>daddr</font>. Si c'est le correspondant → chaîne <font face='DVM'>input</font>, il est en "
      "<font face='DVM'>saddr</font>.", "i")
b.P("<b>Correction :</b>")
b.CODE("ip daddr $ELK_IP tcp dport $ELK_PORT ct state new accept")
b.P("Le <font face='DVM'>ct state new</font> ajouté n'est pas obligatoire, mais il est plus précis : il dit "
    "« autorise l'<i>ouverture</i> de cette connexion ». La suite du dialogue est déjà couverte par la règle "
    "<font face='DVM'>established,related</font> placée plus haut.")

# ---- bug 3
b.H2("Bug 3 — La chaîne forward, vide et grande ouverte")
b.CODE("""
chain forward {
        type filter hook forward priority filter;    # -> policy accept
}
""")
b.P("Cette chaîne concerne tout le trafic qui <b>traverse</b> la machine sans lui être destiné : c'est-à-dire, "
    "à partir du moment où tu installeras Docker, <b>l'intégralité du trafic de Cowrie</b> — celui des attaquants "
    "vers le conteneur, et celui du conteneur vers ton réseau. La laisser en <font face='DVM'>accept</font> revient "
    "à annuler l'objectif du TP : empêcher un honeypot compromis d'aller voir tes autres machines.")
b.P("<b>Correction :</b> <font face='DVM'>policy drop</font>, plus le trio habituel "
    "(<font face='DVM'>invalid</font>, <font face='DVM'>established</font>, journalisation). Le détail Docker est "
    "traité en §6.")

# ---- bug 4
b.H2("Bug 4 — Des ports ouverts en entrée par confusion de sens")
b.P("<b>Gravité : majeure</b> — et c'est la conséquence directe du diagnostic raté du §2.")
b.CODE("""
# ton fichier, chaîne input :
tcp dport 53 accept
udp dport 53 accept
tcp dport {443, 80} accept
""")
b.P("En chaîne <font face='DVM'>input</font>, <font face='DVM'>dport</font> désigne un port <b>de ta machine</b>. "
    "Ces trois lignes se lisent donc :")
b.LI([
    "« n'importe qui sur Internet peut interroger un serveur DNS hébergé sur cette machine » ;",
    "« n'importe qui sur Internet peut atteindre un serveur web hébergé sur cette machine ».",
])
b.P("Ce n'est évidemment pas ce que tu voulais : tu cherchais à réparer tes requêtes <i>sortantes</i>. "
    "Les réponses à tes propres requêtes n'ont besoin d'aucune de ces règles — elles sont déjà couvertes par "
    "<font face='DVM'>ct state established,related accept</font>.")
b.BOX("Aujourd'hui ces règles n'ouvrent rien de concret, parce qu'aucun service n'écoute sur ces ports. "
      "Mais elles constituent une <b>bombe à retardement</b> : le jour où tu lances un conteneur avec un serveur "
      "web, il devient joignable depuis Internet sans que tu aies rien décidé. Un pare-feu doit énoncer une "
      "intention, pas des vestiges de dépannage.", "w")
b.P("<b>Correction :</b> supprimer ces trois lignes de la chaîne <font face='DVM'>input</font>, et corriger la "
    "sortie dans <font face='DVM'>output</font> en nommant les serveurs DNS :")
b.CODE("""
# dans output — on autorise, mais seulement vers les résolveurs déclarés
ip daddr { 8.8.8.8, 1.1.1.1 } udp dport 53 accept
ip daddr { 8.8.8.8, 1.1.1.1 } tcp dport 53 accept
""")

# ---- bug 5
b.H2("Bug 5 — Les ports de Cowrie dans la mauvaise chaîne")
b.CODE("tcp dport {22, 23} accept        # dans input")
b.P("L'intention est juste, l'emplacement non. Une fois Cowrie lancé dans Docker, les paquets des attaquants "
    "sont redirigés vers l'adresse interne du conteneur : ils <b>traversent</b> la machine et passent par "
    "<font face='DVM'>forward</font>, jamais par <font face='DVM'>input</font>. Cette règle ne servira donc à rien — "
    "et, plus déroutant, Cowrie fonctionnera quand même, parce que Docker installe ses propres règles. "
    "Voir §6, c'est le piège principal du sujet.")

# ---- bug 6
b.H2("Bug 6 — IPv6 : le point le plus important pour un honeypot")
b.P("<b>Gravité : majeure.</b> Deux constats indépendants.")
b.H3("a. La découverte de voisins est bloquée")
b.P("588 paquets ICMPv6 de types 135 et 136 refusés en sortie. Ce sont les messages "
    "<i>neighbor solicitation</i> et <i>neighbor advertisement</i> : l'équivalent IPv6 d'ARP. Sans eux, la machine "
    "ne peut plus associer une adresse IPv6 à une adresse matérielle, et l'IPv6 cesse de fonctionner. Ta chaîne "
    "<font face='DVM'>input</font> les autorisait ; ta chaîne <font face='DVM'>output</font> les avait oubliés.")
b.H3("b. Ta machine possède une adresse IPv6 publique")
b.CODE("""
$ ip -6 -br addr
wlp3s0   UP   2a01:e0a:abe:f8e0:a2d3:7aff:feb5:58ab/64   fe80::a2d3:7aff:feb5:58ab/64
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ adresse publique, routable
""")
b.FIG(F.fig_ipv6(), "En IPv4 la box te protège par effet de bord, grâce au NAT. En IPv6 il n'y a pas de NAT : "
                    "seul le pare-feu décide.")
b.BOX("<b>À retenir absolument.</b> En IPv4 tu es derrière le NAT de la Freebox : rien n'entre sans redirection de "
      "port explicite. En IPv6, ta machine est <b>directement routable depuis Internet</b>. Le seul rempart est "
      "ton pare-feu, et il est aujourd'hui en <font face='DVM'>policy accept</font>. Pour un honeypot — une machine "
      "dont le métier est d'être attaquée — c'est le point de vigilance numéro un.", "e")
b.P("<b>Correction :</b> une <font face='DVM'>policy drop</font> qui s'applique bien aux deux familles (c'est le cas "
    "avec <font face='DVM'>inet</font>), et un jeu de règles ICMPv6 complet <b>dans les deux chaînes</b>. "
    "Contrairement à l'IPv4, on ne peut pas filtrer l'ICMPv6 à la serpe : il porte des fonctions vitales "
    "(voisinage, découverte de routeur, taille maximale de paquet).")

# ---- bug 7
b.H2("Bug 7 — Rien ne survit au redémarrage")
b.CODE("""
$ systemctl is-enabled nftables
disabled
$ systemctl is-active nftables
inactive
""")
b.P("Ton ruleset a été chargé à la main par <font face='DVM'>nft -f</font>. Il vit uniquement en mémoire. "
    "Au prochain redémarrage, la machine repart <b>sans aucune règle</b>. C'est d'autant plus trompeur que "
    "<font face='DVM'>/etc/nftables.conf</font> existe et paraît en place.")
b.P("<b>Correction :</b> une fois le fichier validé et testé,")
b.CODE("sudo systemctl enable --now nftables")
b.BOX("À faire <b>en dernier</b>, et jamais avant d'avoir vérifié que tu conserves l'accès SSH — sinon un "
      "redémarrage suffit à te verrouiller dehors définitivement.", "w")

# ---- bugs mineurs
b.H2("Points mineurs")
b.TABLE(["Ce que tu as écrit", "Remarque"], [
    ["<font face='DVM'>ip saddr 192.168.1.0/24 icmp type { … destination-unreachable, time-exceeded }</font>",
     "Ces deux messages d'erreur viennent surtout d'<b>Internet</b>, pas du réseau local : ils signalent une "
     "route cassée ou un paquet trop grand. Les restreindre au LAN peut provoquer des blocages difficiles à "
     "diagnostiquer. Ils sont de toute façon classés <font face='DVM'>related</font> par le suivi de connexion."],
    ["<font face='DVM'>log prefix \"IN-DROP \"</font> sans <font face='DVM'>level</font>",
     "Le niveau par défaut est <font face='DVM'>warn</font>, ce qui remonte dans la console. "
     "<font face='DVM'>level info</font> est plus discret et suffit."],
    ["Ordre des règles",
     "<font face='DVM'>ct state established,related accept</font> gagne à être la première règle après "
     "<font face='DVM'>invalid</font> : c'est par elle que passe l'immense majorité des paquets, et chaque règle "
     "placée avant est évaluée inutilement pour chacun d'eux."],
    ["<font face='DVM'>udp dport 123 accept</font> sans destination",
     "Fonctionne, mais autorise le NTP vers n'importe quelle adresse. On peut le restreindre aux serveurs "
     "effectivement utilisés (<font face='DVM'>systemctl status systemd-timesyncd</font> les affiche)."],
], [7.4 * cm, W - 7.4 * cm])
b.PB()

# ============================================================ §4 RULESET CORRIGÉ
b.H1("4. Le ruleset corrigé")
b.P("Voici le fichier complet. Il a été <b>vérifié syntaxiquement</b> sur ta machine avec "
    "<font face='DVM'>nft -c -f</font>, sans être appliqué. Les choix suivent tes réponses : sortie Internet "
    "fermée, logs vers 192.168.1.35:5044, administration depuis 192.168.1.33 seulement.")
b.CODE("""
#!/usr/sbin/nft -f
flush ruleset

define ADMIN_IP     = 192.168.1.33
define SSH_PORT     = 2727
define ELK_IP       = 192.168.1.35
define ELK_PORT     = 5044
define LAN          = 192.168.1.0/24
define DNS_V4       = { 8.8.8.8, 1.1.1.1 }
define COWRIE_PORTS = { 22, 23 }

table inet filter {

    chain input {
        type filter hook input priority filter; policy drop;

        ct state invalid drop
        ct state established,related accept
        iif lo accept

        ip saddr $LAN icmp type { echo-request, echo-reply } accept
        icmpv6 type { echo-request, echo-reply, nd-neighbor-solicit,
                      nd-neighbor-advert, nd-router-solicit, nd-router-advert,
                      packet-too-big, time-exceeded, parameter-problem,
                      destination-unreachable } accept

        tcp dport $SSH_PORT ip saddr $ADMIN_IP ct state new accept
        tcp dport $COWRIE_PORTS ct state new accept

        log prefix "IN-DROP " level info limit rate 5/minute
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state invalid drop
        ct state established,related accept
        log prefix "FWD-DROP " level info limit rate 5/minute
    }

    chain output {
        type filter hook output priority filter; policy drop;

        ct state invalid drop
        ct state established,related accept
        oif lo accept

        icmpv6 type { nd-neighbor-solicit, nd-neighbor-advert,
                      nd-router-solicit, destination-unreachable,
                      packet-too-big, time-exceeded, parameter-problem } accept
        ip saddr $LAN icmp type echo-request accept

        ip daddr $ELK_IP tcp dport $ELK_PORT ct state new accept

        ip daddr $DNS_V4 udp dport 53 accept
        ip daddr $DNS_V4 tcp dport 53 accept
        udp dport 123 accept

        log prefix "OUT-DROP " level info limit rate 5/minute
    }
}
""")
b.H2("Ce qui a changé, et pourquoi")
b.TABLE(["Modification", "Raison"], [
    ["<font face='DVM'>policy drop</font> sur les trois chaînes", "Bug 1 — sans elle, rien n'est filtré."],
    ["<font face='DVM'>ip daddr $ELK_IP</font> au lieu de <font face='DVM'>saddr</font>", "Bug 2 — la règle ne pouvait jamais matcher."],
    ["Chaîne <font face='DVM'>forward</font> fermée et journalisée", "Bug 3 — c'est par là que passera tout Cowrie."],
    ["Suppression des <font face='DVM'>dport 80/443/53</font> en entrée", "Bug 4 — ils ouvraient des services inexistants."],
    ["DNS en sortie restreint aux résolveurs déclarés", "Bug 4 — on autorise un flux nommé, pas « le port 53 »."],
    ["ICMPv6 complet dans <b>output</b> aussi", "Bug 6 — sans NDP sortant, l'IPv6 ne fonctionne plus."],
    ["ICMP entrant limité à <font face='DVM'>echo-request/reply</font>", "Les messages d'erreur sont déjà couverts par <font face='DVM'>related</font>."],
    ["<font face='DVM'>ct state new</font> sur les ouvertures", "Précision : on autorise l'ouverture, pas un paquet isolé."],
    ["Aucune règle 80/443 en sortie", "Ta réponse à l'exercice 1.1 (3) : sortie Internet à la demande."],
    ["<font face='DVM'>level info</font> sur les logs", "Évite de polluer la console."],
], [7 * cm, W - 7 * cm])
b.BOX("<b>Note sur les ports de Cowrie.</b> La règle <font face='DVM'>tcp dport $COWRIE_PORTS</font> est conservée "
      "en <font face='DVM'>input</font> pour le cas où tu lancerais Cowrie <i>hors</i> Docker. Dès que tu passes par "
      "un conteneur, c'est la chaîne <font face='DVM'>forward</font> et la chaîne "
      "<font face='DVM'>DOCKER-USER</font> qui prennent le relais (§6).", "i")
b.PB()

# ============================================================ §5 DÉPLOIEMENT
b.H1("5. Mise en place, sans perdre la machine")
b.P("L'ordre des opérations est la partie qui compte. Chaque étape est réversible tant que la précédente a été "
    "respectée.")
b.H2("Étape 1 — Deux terminaux et un filet")
b.CODE("""
# terminal A : on laisse une session SSH ouverte et on n'y touche plus

# terminal B :
sudo systemd-run --on-active=180 --unit=fw-rollback nft flush ruleset
""")
b.H2("Étape 2 — Vérifier la syntaxe sans appliquer")
b.CODE("""
sudo nft -c -f /etc/nftables.conf      # -c : contrôle seul, rien n'est chargé
""")
b.H2("Étape 3 — Appliquer et tester immédiatement")
b.CODE("""
sudo nft -f /etc/nftables.conf
sudo nft list ruleset | head -20       # vérifier que "policy drop" apparaît bien
""")
b.P("Puis, <b>dans le terminal A</b> — celui qui était déjà ouvert — tape simplement une commande. Si elle répond, "
    "ta session a survécu. Ensuite seulement, ouvre une <b>troisième</b> connexion SSH depuis ton PC : c'est elle "
    "qui prouve qu'une <i>nouvelle</i> connexion est encore possible.")
b.BOX("Une session SSH déjà ouverte survit grâce à <font face='DVM'>ct state established</font>, même si la règle "
      "d'ouverture est fautive. <b>Seule une nouvelle connexion prouve que le pare-feu est correct.</b> C'est le "
      "test que l'on oublie, et c'est celui qui coûte cher.", "w")
b.H2("Étape 4 — Batterie de tests")
b.TABLE(["Commande", "Depuis", "Attendu"], [
    ["<font face='DVM'>ssh -p 2727 ubuserv@192.168.1.63</font>", "PC admin (.33)", "<font color='#1e7e34'><b>passe</b></font>"],
    ["<font face='DVM'>ssh -p 2727 …</font>", "une autre machine du LAN", "<font color='#c0392b'><b>timeout</b></font>"],
    ["<font face='DVM'>getent hosts archive.ubuntu.com</font>", "la machine", "<font color='#1e7e34'><b>résout</b></font> (DNS autorisé)"],
    ["<font face='DVM'>curl -sI https://archive.ubuntu.com</font>", "la machine", "<font color='#c0392b'><b>échoue</b></font> — voulu : sortie fermée"],
    ["<font face='DVM'>nc -zv 192.168.1.35 5044</font>", "la machine", "<font color='#1e7e34'><b>passe</b></font> (si ELK est allumé)"],
    ["<font face='DVM'>nc -zv 192.168.1.50 22</font>", "la machine", "<font color='#c0392b'><b>échoue</b></font> + ligne OUT-DROP"],
    ["<font face='DVM'>ping6 -c2 2001:4860:4860::8888</font>", "la machine", "voir NDP : ne doit plus saturer le journal"],
], [7.4 * cm, 4.4 * cm, W - 11.8 * cm])
b.H2("Étape 5 — Annuler le filet, puis rendre permanent")
b.CODE("""
sudo systemctl stop fw-rollback.timer
sudo systemctl enable --now nftables
sudo reboot                             # la seule preuve qui vaille
""")
b.H2("Le fichier de maintenance (sortie Internet à la demande)")
b.P("Conformément à ta réponse à l'exercice 1.1 (3), la sortie web n'est pas dans le fichier permanent. "
    "Crée <font face='DVM'>/etc/nftables.d/maintenance.nft</font> :")
b.CODE("""
#!/usr/sbin/nft -f
# Ouvre la sortie web. À charger le temps d'une mise à jour, puis recharger le fichier normal.
table inet filter {
    chain output {
        ip daddr != 192.168.1.0/24 tcp dport { 80, 443 } ct state new accept
    }
}
""")
b.CODE("""
sudo nft -f /etc/nftables.d/maintenance.nft   # ouvrir
sudo apt update && sudo apt upgrade
sudo nft -f /etc/nftables.conf                # refermer (le flush ruleset remet tout à zéro)
""")
b.P("Le <font face='DVM'>ip daddr != 192.168.1.0/24</font> est important : il ouvre le web vers l'extérieur "
    "sans rouvrir de chemin vers tes autres machines du réseau local.")
b.PB()

# ============================================================ §6 DOCKER
b.H1("6. Ce qui t'attend : Docker")
b.P("Tu n'as pas encore installé Docker — <font face='DVM'>docker</font> est absent de la machine. C'est une bonne "
    "chose : tu abordes l'étape suivante avec un pare-feu propre. Voici ce qui va se passer.")
b.FIG(F.fig_docker(), "Un port publié par Docker ne traverse jamais la chaîne input : il est redirigé très tôt, "
                      "puis routé vers le conteneur en passant par forward.")
b.P("Au démarrage, Docker installe ses propres règles et active le routage "
    "(<font face='DVM'>net.ipv4.ip_forward=1</font>). Un <font face='DVM'>-p 22:2222</font> crée une redirection "
    "d'adresse qui s'applique <b>avant</b> ta chaîne <font face='DVM'>input</font> : le port devient joignable "
    "quelle que soit ta politique d'entrée.")
b.P("Docker laisse toutefois un point d'accroche explicite : la chaîne "
    "<font face='DVM'>DOCKER-USER</font>, évaluée avant ses propres règles. C'est là, et seulement là, que tes "
    "décisions sur le trafic des conteneurs doivent s'écrire.")
b.CODE("""
# autoriser Cowrie à parler à ELK, lui interdire le reste du réseau local
sudo iptables -I DOCKER-USER 1 -d 192.168.1.35 -p tcp --dport 5044 -j ACCEPT
sudo iptables -I DOCKER-USER 2 -d 192.168.1.0/24 -j DROP
""")
b.FIG(F.fig_ordre(), "L'ordre est vital : une règle DROP large placée avant l'autorisation ELK bloquerait "
                     "aussi les logs.")
b.BOX("<b>Le piège de la persistance :</b> Docker recrée ses chaînes à chaque démarrage du service et tes ajouts "
      "disparaissent. Trois approches, à comparer dans la suite du TP : le paquet "
      "<font face='DVM'>iptables-persistent</font> ; un <font face='DVM'>ExecStartPost</font> ajouté à "
      "<font face='DVM'>docker.service</font> ; ou une chaîne nftables branchée sur "
      "<font face='DVM'>forward</font> avec une priorité inférieure à celle de Docker, ce qui la fait passer avant.", "w")
b.PB()

# ============================================================ §7 SUITE
b.H1("7. Ce qu'il reste à faire")
b.TABLE(["#", "Action", "Pourquoi"], [
    ["1", "Corriger <font face='DVM'>/etc/nftables.conf</font> avec le fichier du §4, en suivant la procédure du §5",
     "C'est le cœur du TP"],
    ["2", "Vérifier l'état de la VM ELK (192.168.1.35 ne répond pas)",
     "Sans elle, la règle de sortie ne peut pas être validée"],
    ["3", "Identifier 192.168.1.178", "Une machine du réseau a cherché ton SSH"],
    ["4", "<font face='DVM'>systemctl enable nftables</font> après validation", "Sinon tout disparaît au redémarrage"],
    ["5", "Corriger <font face='DVM'>gateway4: 10.0.0.1</font> dans netplan", "Adresse hors de ton sous-réseau"],
    ["6", "Protéger <font face='DVM'>50-cloud-init.yaml</font> (<font face='DVM'>chmod 600</font>)",
     "Il contient la clé Wi-Fi en clair et il est lisible par tous"],
    ["7", "Installer Docker puis écrire les règles <font face='DVM'>DOCKER-USER</font>", "§6"],
    ["8", "Décider du sort d'<font face='DVM'>unattended-upgrades</font>", "Il échouera en silence avec la sortie fermée"],
], [0.9 * cm, 8.4 * cm, W - 9.3 * cm])

b.BOX("<b>Le mot de la fin.</b> Ce TP t'a fait rencontrer, en une séance, les quatre erreurs qui font perdre une "
      "machine à distance : oublier la <i>policy</i>, inverser source et destination, se tromper de chaîne, et "
      "oublier que l'IPv6 existe. Tu les as désormais rencontrées <b>avec les journaux pour les prouver</b>, ce qui "
      "vaut beaucoup mieux que de les avoir lues quelque part. La compétence à retenir n'est pas la syntaxe de "
      "nftables : c'est le réflexe de lire le journal avant de toucher à une règle.", "g")

build(b.story, "/home/ubuserv/CyberProject/TP-correction.pdf",
      "Correction du TP pare-feu Cowrie", "Correction du TP — pare-feu honeypot Cowrie (nftables)",
      "nftables, correction")
print("OK")
