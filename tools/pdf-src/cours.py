import sys
sys.path.insert(0, "/tmp/claude-1000/-home-ubuserv-CyberProject/376a1b90-229f-487c-98c9-68ff58902afb/scratchpad")
from common import *
import figures as F

b = Builder()

# ============================================================ COUVERTURE
b.SP(3.2 * cm)
b.P("nftables", "title")
b.P("Filtrer le trafic d'une machine Linux — le cours", "sub")
b.SP(16)
b.P("Écrit à partir des points bloquants rencontrés pendant le TP « pare-feu d'un honeypot Cowrie ».", "sub")
b.SP(1.2 * cm)
b.FIG(F.fig_hooks())
b.SP(4)
b.BOX("<b>Comment lire ce cours.</b> Chaque chapitre part d'une question concrète, explique le mécanisme avec un "
      "schéma, puis donne la formulation nftables correspondante. Les encadrés rouges signalent les erreurs "
      "classiques — celles qui coûtent une machine ; les encadrés bleus, les réflexes à garder.", "i")
b.PB()

# ============================================================ SOMMAIRE
b.H1("Sommaire")
b.TABLE(["", "Chapitre", "La question à laquelle il répond"], [
    ["1", "Filtrer, et pourquoi c'est difficile", "Pourquoi une liste de ports ne suffit pas"],
    ["2", "Le voyage d'un paquet", "Pourquoi il existe plusieurs chaînes, et laquelle choisir"],
    ["3", "Anatomie d'un ruleset", "Que veulent dire <font face='DVM'>table</font>, <font face='DVM'>chain</font>, <font face='DVM'>hook</font>, <font face='DVM'>inet</font>"],
    ["4", "Comment une chaîne est évaluée", "Pourquoi l'ordre des règles change tout"],
    ["5", "La <i>policy</i>", "La ligne qui transforme une liste en pare-feu"],
    ["6", "Le suivi de connexion", "Pourquoi <font face='DVM'>ct state established</font> est partout"],
    ["7", "Source et destination", "Pourquoi la même machine est tantôt <font face='DVM'>saddr</font>, tantôt <font face='DVM'>daddr</font>"],
    ["8", "Les flux qu'on oublie toujours", "Bouclage, DNS, NTP, ICMP : ce qui casse en silence"],
    ["9", "IPv6", "Pourquoi c'est le sujet le plus important d'un honeypot"],
    ["10", "Docker", "Pourquoi un conteneur ignore votre chaîne <font face='DVM'>input</font>"],
    ["11", "Écrire, tester, déboguer", "La méthode, et comment lire un journal"],
    ["12", "Mémo", "Tout tient sur deux pages"],
], [0.9 * cm, 5.6 * cm, W - 6.5 * cm])
b.PB()

# ============================================================ 1
b.H1("1. Filtrer, et pourquoi c'est difficile")
b.P("L'idée d'un pare-feu paraît simple : décider quels paquets entrent et quels paquets sortent. La difficulté "
    "n'est pas d'écrire une règle, elle est ailleurs — dans trois pièges que ce cours va lever un par un.")

b.H2("Piège 1 : une conversation, ce n'est pas un sens unique")
b.P("Quand ta machine interroge un serveur web, elle envoie des paquets <i>et</i> elle en reçoit. Si tu n'autorises "
    "que la sortie, rien ne fonctionne : les réponses sont refusées à l'entrée. Si tu ouvres l'entrée en grand pour "
    "laisser passer les réponses, tu n'as plus de pare-feu. La solution — le <b>suivi de connexion</b> — fait "
    "l'objet du chapitre 6.")

b.H2("Piège 2 : tout le trafic ne passe pas au même endroit")
b.P("Un paquet destiné à ta machine, un paquet qu'elle émet, et un paquet qui la <i>traverse</i> pour aller vers un "
    "conteneur ne suivent pas le même chemin dans le noyau. Écrire la bonne règle au mauvais endroit, c'est écrire "
    "une règle qui ne servira jamais. C'est le chapitre 2.")

b.H2("Piège 3 : ce que tu autorises n'est pas ce que tu crois")
b.P("Une machine moderne émet en permanence du trafic auquel personne ne pense : résolution de noms, "
    "synchronisation d'horloge, découverte de voisins IPv6, dialogue avec elle-même. Un pare-feu écrit « proprement » "
    "casse presque toujours l'un de ces flux, et le symptôme visible ne désigne jamais la bonne règle. "
    "C'est le chapitre 8, et c'est celui qui fait gagner le plus de temps.")

b.BOX("<b>Le fil directeur de ce cours :</b> un pare-feu ne s'écrit pas en listant des ports. Il s'écrit en "
      "listant des <b>flux</b> — qui parle à qui, dans quel sens, et qui ouvre la conversation. Le port n'est que "
      "le dernier détail.", "i")
b.PB()

# ============================================================ 2
b.H1("2. Le voyage d'un paquet")
b.P("Le filtrage est intégré au noyau Linux, dans un sous-système appelé <b>netfilter</b>. Netfilter place des "
    "points de contrôle — des <b>hooks</b>, littéralement des crochets — à des endroits précis du parcours d'un "
    "paquet. Une chaîne nftables n'est rien d'autre qu'une liste de règles accrochée à l'un de ces points.")
b.FIG(F.fig_hooks(), "Les cinq points de contrôle de netfilter. Un paquet ne passe jamais par les trois chaînes : "
                     "il suit exactement un des trois chemins.")

b.H2("Les trois chemins possibles")
b.TABLE(["Chemin", "Le paquet…", "Chaînes traversées", "Exemple"], [
    ["<b>Entrant</b>", "est destiné à un programme de la machine",
     "prerouting → <b>input</b>", "une connexion SSH vers ta machine"],
    ["<b>Sortant</b>", "est émis par un programme de la machine",
     "<b>output</b> → postrouting", "<font face='DVM'>curl</font>, l'envoi des logs vers ELK"],
    ["<b>Traversant</b>", "ne fait que passer, il va ailleurs",
     "prerouting → <b>forward</b> → postrouting", "tout le trafic d'un conteneur Docker"],
], [2.3 * cm, 5 * cm, 4.3 * cm, W - 11.6 * cm])

b.BOX("<b>C'est la décision de routage qui tranche.</b> Juste après <i>prerouting</i>, le noyau regarde l'adresse de "
      "destination et se demande : « est-ce pour moi ? ». Si oui, le paquet part vers <font face='DVM'>input</font>. "
      "Sinon, vers <font face='DVM'>forward</font>. Tu ne choisis pas : c'est la destination du paquet qui décide, "
      "et donc la topologie de ton installation.", "i")

b.H2("La conséquence pratique")
b.P("Avant d'écrire une règle, la première question n'est jamais « quel port ? », mais <b>« ce paquet est-il pour "
    "moi, de moi, ou à travers moi ? »</b>. Trois exemples tirés du TP :")
b.TABLE(["Flux", "Qui ouvre la connexion", "Chaîne"], [
    ["Ton PC se connecte en SSH à la machine", "le PC", "<font color='#1e7e34'><b>input</b></font>"],
    ["La machine envoie ses logs à ELK", "la machine", "<font color='#c0392b'><b>output</b></font>"],
    ["Un attaquant atteint Cowrie dans un conteneur", "l'attaquant, mais la cible est le conteneur",
     "<font color='#b26a00'><b>forward</b></font>"],
], [W - 8 * cm, 4.4 * cm, 3.6 * cm])
b.BOX("<b>Erreur classique</b> — celle du TP : écrire <font face='DVM'>tcp dport 22 accept</font> dans "
      "<font face='DVM'>input</font> en pensant ouvrir l'accès à Cowrie. Si Cowrie tourne dans un conteneur, "
      "ce paquet ne passera jamais par <font face='DVM'>input</font>, et la règle ne servira à rien.", "e")
b.PB()

# ============================================================ 3
b.H1("3. Anatomie d'un ruleset")
b.P("Un ruleset s'organise sur trois niveaux : une <b>table</b> contient des <b>chaînes</b>, qui contiennent des "
    "<b>règles</b>.")
b.FIG(F.fig_arbo(), "Les trois niveaux, et la ligne de déclaration d'une chaîne, qui concentre l'essentiel.")

b.H2("La table et sa famille")
b.P("La <b>famille</b> indique quel type de trafic la table peut voir. C'est le premier mot après "
    "<font face='DVM'>table</font>.")
b.TABLE(["Famille", "Voit", "Remarque"], [
    ["<font face='DVM'>ip</font>", "IPv4 seulement", "Historique"],
    ["<font face='DVM'>ip6</font>", "IPv6 seulement", "Historique — obligeait à tout écrire deux fois"],
    ["<font face='DVM'>inet</font>", "IPv4 <b>et</b> IPv6", "<b>Le choix par défaut.</b> Une table, deux protocoles"],
    ["<font face='DVM'>arp</font>, <font face='DVM'>bridge</font>, <font face='DVM'>netdev</font>",
     "Trafic ARP, ponté, ou au ras de la carte", "Cas avancés"],
], [3.4 * cm, 3.8 * cm, W - 7.2 * cm])
b.BOX("<b>Le piège d'<font face='DVM'>inet</font>.</b> La table voit les deux protocoles, mais chaque règle "
      "reste spécifique à ce qu'elle nomme :<br/>"
      "• <font face='DVM'>ip saddr 192.168.1.33</font> → IPv4 uniquement<br/>"
      "• <font face='DVM'>ip6 saddr fe80::/10</font> → IPv6 uniquement<br/>"
      "• <font face='DVM'>tcp dport 5044</font> → <b>les deux</b>, car aucune version n'est mentionnée<br/>"
      "Autrement dit : déclarer une table <font face='DVM'>inet</font> ne couvre pas l'IPv6 automatiquement. "
      "Il faut y penser règle par règle.", "w")

b.H2("La ligne de déclaration d'une chaîne")
b.CODE("""
type filter hook input priority filter; policy drop;
     ~~~~~~      ~~~~~          ~~~~~~          ~~~~
       |           |              |               `-- verdict par défaut (chapitre 5)
       |           |              `----------------- ordre vis-à-vis des autres chaînes
       |           `-------------------------------- à quel point de contrôle on s'accroche
       `-------------------------------------------- ce que la chaîne a le droit de faire
""")
b.TABLE(["Élément", "Valeurs", "À quoi ça sert"], [
    ["<font face='DVM'>type</font>", "<font face='DVM'>filter</font>, <font face='DVM'>nat</font>, <font face='DVM'>route</font>",
     "<font face='DVM'>filter</font> = accepter ou refuser. <font face='DVM'>nat</font> = réécrire des adresses."],
    ["<font face='DVM'>hook</font>", "<font face='DVM'>input</font>, <font face='DVM'>output</font>, <font face='DVM'>forward</font>, "
     "<font face='DVM'>prerouting</font>, <font face='DVM'>postrouting</font>", "Le point de contrôle du chapitre 2"],
    ["<font face='DVM'>priority</font>", "un entier, ou un mot-clé", "Si deux chaînes visent le même hook, "
     "la <b>priorité la plus basse passe en premier</b>. <font face='DVM'>filter</font> vaut 0, "
     "<font face='DVM'>raw</font> vaut −300."],
    ["<font face='DVM'>policy</font>", "<font face='DVM'>accept</font> (défaut) ou <font face='DVM'>drop</font>",
     "Le verdict si aucune règle ne matche. Chapitre 5."],
], [3 * cm, 5.4 * cm, W - 8.4 * cm])
b.BOX("La priorité n'est pas un détail théorique : c'est le mécanisme qui permet de faire passer ses propres règles "
      "<b>avant</b> celles que Docker installe. Une chaîne <font face='DVM'>forward</font> déclarée avec "
      "<font face='DVM'>priority -10</font> est évaluée avant celle de Docker, qui est à 0.", "i")

b.H2("L'anatomie d'une règle")
b.CODE("""
ip daddr 192.168.1.35   tcp dport 5044   ct state new   accept
~~~~~~~~~~~~~~~~~~~~~   ~~~~~~~~~~~~~~   ~~~~~~~~~~~~   ~~~~~~
        condition          condition       condition    verdict

Toutes les conditions doivent être vraies EN MÊME TEMPS (c'est un ET).
Le verdict est toujours en dernier.
""")
b.P("Les verdicts possibles :")
b.TABLE(["Verdict", "Effet"], [
    ["<font face='DVM'>accept</font>", "Le paquet est accepté et <b>sort immédiatement de la chaîne</b>"],
    ["<font face='DVM'>drop</font>", "Le paquet est jeté sans un mot. L'émetteur attendra jusqu'à expiration du délai"],
    ["<font face='DVM'>reject</font>", "Le paquet est refusé <b>avec une réponse</b> — l'émetteur sait tout de suite. "
     "Plus courtois sur un réseau interne, mais révèle l'existence de la machine"],
    ["<font face='DVM'>log</font>", "<b>N'est pas un verdict.</b> Écrit une ligne dans le journal et l'évaluation "
     "<b>continue</b> à la règle suivante"],
    ["<font face='DVM'>counter</font>", "Idem : compte les paquets, n'interrompt rien. Précieux pour déboguer"],
    ["<font face='DVM'>jump</font> / <font face='DVM'>goto</font>", "Renvoie vers une chaîne nommée, pour organiser un gros ruleset"],
], [3.2 * cm, W - 3.2 * cm])
b.BOX("<b>À retenir absolument :</b> <font face='DVM'>log</font> ne bloque rien. Une chaîne qui se termine par "
      "<font face='DVM'>log prefix \"DROP \"</font> sans <font face='DVM'>policy drop</font> écrit « DROP » dans le "
      "journal… et laisse passer le paquet. Le préfixe ment. C'est exactement ce qui se produisait sur ta machine.", "e")
b.PB()

# ============================================================ 4
b.H1("4. Comment une chaîne est évaluée")
b.P("Le noyau lit les règles <b>de haut en bas</b>, une par une. Dès qu'une règle correspond au paquet et rend un "
    "verdict, l'évaluation <b>s'arrête</b> : les règles suivantes ne sont jamais examinées.")
b.FIG(F.fig_chain_eval(), "Un paquet SSH traverse la chaîne. Il est accepté à la quatrième règle ; "
                          "les deux suivantes ne le concerneront jamais.")

b.H2("Pourquoi l'ordre change tout")
b.FIG(F.fig_ordre(), "Les deux chaînes contiennent exactement les mêmes règles. Seul l'ordre diffère, "
                     "et le résultat est opposé.")
b.P("La règle de composition qui en découle, et qu'on retrouve dans tous les pare-feux bien écrits :")
b.NUM([
    "d'abord ce qui est <b>anormal</b> — <font face='DVM'>ct state invalid drop</font> ;",
    "puis ce qui est <b>massif et déjà autorisé</b> — <font face='DVM'>ct state established,related accept</font> ; "
    "c'est par là que passe l'essentiel du trafic, autant l'évacuer tout de suite ;",
    "puis le <b>bouclage</b> — <font face='DVM'>iif lo accept</font> ;",
    "puis les autorisations <b>du plus précis au plus général</b> ;",
    "enfin la <b>journalisation</b>, juste avant la <i>policy</i> qui jette le reste.",
])
b.BOX("<b>Effet de bord utile :</b> placer <font face='DVM'>established</font> en deuxième position est aussi un "
      "choix de performance. Sur une machine qui reçoit beaucoup de trafic, chaque règle placée au-dessus est "
      "évaluée pour chacun des paquets d'une conversation en cours — c'est-à-dire pour la quasi-totalité du trafic.", "i")
b.PB()

# ============================================================ 5
b.H1("5. La policy : la ligne qui fait le pare-feu")
b.P("C'est le point le plus important de tout ce cours. La <b>policy</b> est le verdict appliqué à un paquet "
    "qu'<b>aucune règle</b> n'a reconnu. Elle se déclare sur la ligne de la chaîne, et si tu l'omets, nftables "
    "retient <font face='DVM'>accept</font>.")
b.FIG(F.fig_policy(), "Deux chaînes rigoureusement identiques. Une seule ligne les sépare, et elle décide de "
                      "tout : à gauche une liste de suggestions, à droite un pare-feu.")

b.H2("Les deux philosophies")
b.TABLE(["", "<font face='DVM'>policy accept</font>", "<font face='DVM'>policy drop</font>"], [
    ["Principe", "Tout passe, sauf ce que j'interdis", "Tout est bloqué, sauf ce que j'autorise"],
    ["Nom courant", "liste noire", "<b>liste blanche</b>"],
    ["Ce qu'il faut prévoir", "toutes les menaces — impossible", "tous les flux légitimes — fini et connaissable"],
    ["Quand tu oublies quelque chose", "<b>une faille</b>, et tu ne t'en aperçois pas",
     "<b>une panne</b>, visible immédiatement et écrite dans le journal"],
    ["À utiliser", "presque jamais", "<b>toujours</b>"],
], [3.4 * cm, (W - 3.4 * cm) / 2, (W - 3.4 * cm) / 2])
b.BOX("<b>Le raisonnement qui justifie la liste blanche :</b> dans les deux cas tu vas oublier quelque chose — "
      "c'est certain. La seule question est de savoir ce que cet oubli produit. En "
      "<font face='DVM'>policy drop</font>, il produit une panne : tu la vois, le journal t'indique le paquet "
      "manquant, tu ajoutes la règle, c'est réglé en deux minutes. En <font face='DVM'>policy accept</font>, il "
      "produit un trou dont tu n'entendras parler que le jour où quelqu'un l'aura trouvé.", "i")

b.H2("Comment vérifier")
b.CODE("""
sudo nft list ruleset | grep -E 'chain|policy'

# ce que tu veux lire :
#   type filter hook input priority filter; policy drop;
# ce qui doit t'alerter :
#   type filter hook input priority filter; policy accept;
""")
b.BOX("Note importante : <font face='DVM'>nft</font> <b>affiche toujours</b> la policy effective, même quand tu ne "
      "l'as pas écrite. C'est donc le moyen le plus fiable de vérifier ce que le noyau a réellement retenu, "
      "par opposition à ce que tu crois avoir écrit dans ton fichier.", "w")
b.PB()

# ============================================================ 6
b.H1("6. Le suivi de connexion")
b.P("Le sous-système <b>conntrack</b> tient à jour la liste de toutes les conversations réseau en cours. C'est lui "
    "qui rend un pare-feu « à état » (<i>stateful</i>) — par opposition à un filtre qui examinerait chaque paquet "
    "isolément, sans mémoire.")
b.FIG(F.fig_conntrack(), "Chaque paquet est confronté à la table des connexions, qui lui attribue un état. "
                         "C'est cet état que l'on teste avec ct state.")

b.H2("Ce que ça change concrètement")
b.P("Sans suivi de connexion, pour autoriser une simple requête web, il faudrait écrire :")
b.CODE("""
# dans output :  laisser sortir la requête
tcp dport 443 accept
# dans input :   laisser entrer la réponse... mais comment la reconnaître ?
tcp sport 443 accept        # <-- n'importe qui peut émettre depuis le port 443
""")
b.P("Cette seconde règle est une porte ouverte : elle accepte tout paquet prétendant venir d'un port 443, "
    "y compris d'une machine que tu n'as jamais contactée. Avec le suivi de connexion, le problème disparaît :")
b.CODE("""
# dans input : une seule règle, pour TOUS les flux, dans les deux sens
ct state established,related accept
""")
b.BOX("<b>La réponse à une question posée pendant le TP :</b> non, les paquets de retour ne « contournent » pas le "
      "pare-feu. <b>Chaque paquet est évalué</b>, sans exception. Simplement, cette règle les reconnaît tous d'un "
      "coup, parce que le noyau se souvient que la conversation a été autorisée à s'ouvrir.", "i")

b.H2("Les quatre états, et ce qu'ils signifient")
b.TABLE(["État", "Signification", "Que faire"], [
    ["<font face='DVM'>new</font>", "Premier paquet d'une conversation : quelqu'un demande à ouvrir un dialogue",
     "C'est <b>ici</b> que se prend la décision d'autoriser ou non"],
    ["<font face='DVM'>established</font>", "Paquet appartenant à une conversation déjà connue, dans un sens ou dans l'autre",
     "<b>Accepter</b> — la décision a déjà été prise"],
    ["<font face='DVM'>related</font>", "Paquet lié à une conversation existante sans en faire partie : erreur ICMP, "
     "canal de données FTP…", "<b>Accepter</b> — sinon certains protocoles cassent de façon très obscure"],
    ["<font face='DVM'>invalid</font>", "Paquet incohérent : hors séquence, appartenant à aucune connexion connue",
     "<b>Jeter en première règle</b>, avant tout le reste"],
], [3 * cm, 7 * cm, W - 10 * cm])

b.H2("La structure canonique d'une chaîne")
b.CODE("""
chain input {
    type filter hook input priority filter; policy drop;

    ct state invalid drop              # 1. le pathologique, tout de suite
    ct state established,related accept # 2. le trafic déjà autorisé (99 % du volume)
    iif lo accept                       # 3. la machine qui se parle à elle-même

    # 4. ... ici, et seulement ici, les ouvertures de connexion autorisées ...

    log prefix "IN-DROP " level info limit rate 5/minute   # 5. tracer le reste
}                                                          # 6. policy drop le jette
""")
b.BOX("Ces trois premières lignes sont identiques dans toutes les chaînes de tous les pare-feux Linux bien écrits. "
      "Apprends-les par cœur : elles constituent le squelette, et la partie 4 est la seule qui change d'une "
      "machine à l'autre.", "g")

b.H2("Inspecter les connexions en cours")
b.CODE("""
sudo apt install conntrack
sudo conntrack -L                    # liste des conversations suivies
sudo conntrack -E                    # les voir apparaître en direct
""")
b.PB()

# ============================================================ 7
b.H1("7. Source et destination")
b.P("<font face='DVM'>saddr</font> signifie <i>source address</i>, <font face='DVM'>daddr</font> "
    "<i>destination address</i>. La difficulté n'est pas le vocabulaire : c'est que ces deux valeurs "
    "<b>s'échangent</b> selon la chaîne, pour une même conversation entre les deux mêmes machines.")
b.FIG(F.fig_saddr_daddr(), "La même machine est en daddr quand on lui parle, et en saddr quand elle nous parle. "
                           "Tout dépend du sens du paquet, jamais du rôle de la machine.")

b.H2("Le tableau de conversion")
b.TABLE(["Dans la chaîne…", "<font face='DVM'>saddr</font> désigne", "<font face='DVM'>daddr</font> désigne",
         "<font face='DVM'>dport</font> désigne"], [
    ["<b>input</b>", "la machine <b>distante</b>", "toi", "un port <b>ouvert chez toi</b>"],
    ["<b>output</b>", "toi", "la machine <b>distante</b>", "un port ouvert <b>chez le correspondant</b>"],
], [3.4 * cm, (W - 3.4 * cm) / 3, (W - 3.4 * cm) / 3, (W - 3.4 * cm) / 3])

b.BOX("<b>La question qui résout tous les cas :</b> « <i>qui ouvre la connexion ?</i> »<br/>"
      "• C'est <b>ma machine</b> → chaîne <font face='DVM'>output</font>, le correspondant est en "
      "<font face='DVM'>daddr</font>, et <font face='DVM'>dport</font> est le port de <i>son</i> service.<br/>"
      "• C'est <b>le correspondant</b> → chaîne <font face='DVM'>input</font>, il est en "
      "<font face='DVM'>saddr</font>, et <font face='DVM'>dport</font> est le port de <i>mon</i> service.", "i")

b.H2("L'erreur symétrique, dans les deux sens")
b.TABLE(["Écrit", "Dans", "Ce que ça fait vraiment"], [
    ["<font face='DVM'>ip saddr $ELK_IP tcp dport 5044 accept</font>", "<font face='DVM'>output</font>",
     "<font color='#c0392b'><b>Ne matche jamais.</b></font> En sortie, la source est toujours ta propre adresse. "
     "Les logs ne partent pas, et rien n'explique pourquoi."],
    ["<font face='DVM'>tcp dport 443 accept</font>", "<font face='DVM'>input</font>",
     "<font color='#c0392b'><b>Ouvre un service.</b></font> Ça ne fait pas fonctionner tes requêtes web : "
     "ça autorise le monde entier à joindre un serveur web sur <i>ta</i> machine."],
], [7.2 * cm, 2.6 * cm, W - 9.8 * cm])
b.P("Ces deux erreurs ont la même racine : raisonner en « ce flux concerne le port 5044 / le port 443 » plutôt "
    "qu'en « qui appelle qui ». La deuxième est la plus dangereuse, parce qu'elle ne provoque aucune panne — "
    "elle ouvre juste une porte, silencieusement.")
b.PB()

# ============================================================ 8
b.H1("8. Les flux qu'on oublie toujours")
b.P("Une machine Linux émet en permanence du trafic auquel personne ne pense en écrivant son pare-feu. "
    "Voici la liste, par ordre de fréquence des dégâts.")

b.H2("1. Le bouclage — et pourquoi il est vital")
b.CODE("""
iif lo accept      # dans input   : "arrivé par l'interface de bouclage"
oif lo accept      # dans output  : "va sortir par l'interface de bouclage"
""")
b.P("<font face='DVM'>lo</font> est l'interface <i>loopback</i> : c'est la machine qui se parle à elle-même, sur "
    "<font face='DVM'>127.0.0.1</font> et <font face='DVM'>::1</font>. Ce trafic ne quitte jamais l'ordinateur.")
b.BOX("<b>Attention à une confusion fréquente :</b> <font face='DVM'>iif</font> se lit <i>input interface</i>, "
      "et n'a rien à voir avec un <i>if</i> conditionnel ni avec une boucle de programmation. "
      "<font face='DVM'>iif lo accept</font> signifie exactement : « si ce paquet est entré par l'interface de "
      "bouclage, accepte-le ». Rien d'autre.", "e")
b.P("Pourquoi c'est vital sur Ubuntu : <font face='DVM'>systemd-resolved</font> écoute sur "
    "<font face='DVM'>127.0.0.53</font>. Chaque résolution de nom passe donc par le bouclage. Sans cette règle et "
    "avec <font face='DVM'>policy drop</font>, plus rien ne résout, et le symptôme visible sera « Internet ne "
    "marche pas ».")

b.H2("2. Le DNS — la première panne de tout pare-feu")
b.FIG(F.fig_dns(), "Ce qui se passe réellement derrière une simple requête web. "
                   "Le port 443 n'est jamais atteint si l'étape 1 est bloquée.")
b.BOX("<b>La leçon la plus rentable de ce cours.</b> Quand « le web ne marche plus » après avoir activé un "
      "pare-feu, c'est le DNS neuf fois sur dix. Le réflexe correct n'est pas d'ajouter des règles au hasard, "
      "c'est de séparer les deux étapes :", "w")
b.CODE("""
getent hosts archive.ubuntu.com     # teste UNIQUEMENT la résolution de nom
curl -sI https://185.125.190.83     # teste UNIQUEMENT la connexion, sans DNS

# si le premier échoue et le second passe -> c'est le DNS, pas le web
""")
b.P("Et la règle correspondante, en nommant les résolveurs plutôt qu'en ouvrant « le port 53 » :")
b.CODE("""
ip daddr { 8.8.8.8, 1.1.1.1 } udp dport 53 accept
ip daddr { 8.8.8.8, 1.1.1.1 } tcp dport 53 accept   # TCP : réponses volumineuses, DNSSEC
""")
b.P("Pour connaître les résolveurs réellement utilisés par ta machine : "
    "<font face='DVM'>resolvectl status</font>. Attention, il y a souvent un résolveur IPv6 dans la liste, "
    "fourni par la box — il faut une règle <font face='DVM'>ip6 daddr</font> correspondante.")

b.H2("3. L'horloge")
b.CODE("udp dport 123 accept      # NTP")
b.P("Sans synchronisation, l'horloge dérive. Sur un honeypot, c'est une perte sèche : des journaux mal horodatés "
    "sont inexploitables pour reconstituer une attaque, et ne peuvent plus être corrélés avec ceux des autres "
    "machines dans ELK.")

b.H2("4. ICMP — ce n'est pas que le ping")
b.P("Bloquer tout l'ICMP est une vieille habitude, et une mauvaise idée. Certains messages portent des fonctions "
    "indispensables :")
b.TABLE(["Message", "Rôle", "Si tu le bloques"], [
    ["<font face='DVM'>echo-request / reply</font>", "Le ping", "Tu ne peux plus diagnostiquer — gênant, pas grave"],
    ["<font face='DVM'>destination-unreachable</font>", "« Cette adresse n'existe pas / ce port est fermé »",
     "Tes connexions échouent après un long délai au lieu d'échouer tout de suite"],
    ["<font face='DVM'>time-exceeded</font>", "Boucle de routage détectée, base de <font face='DVM'>traceroute</font>", "Plus de traceroute"],
    ["<font face='DVM'>packet-too-big</font> (type 2, IPv6)", "<b>Découverte de la taille maximale de paquet</b>",
     "<font color='#c0392b'><b>Cassure profonde</b></font> : les petites connexions passent, les gros transferts "
     "se figent au milieu. Diagnostic très difficile"],
], [4.4 * cm, 5.4 * cm, W - 9.8 * cm])
b.BOX("Bonne nouvelle : la plupart de ces messages d'erreur sont classés <font face='DVM'>related</font> par le "
      "suivi de connexion, donc déjà acceptés par la règle canonique. Il reste à autoriser explicitement "
      "<font face='DVM'>echo-request</font> si tu veux pouvoir pinguer la machine, et <b>tout l'ICMPv6 de "
      "voisinage</b>, qui n'est lié à aucune connexion (chapitre 9).", "i")
b.PB()

# ============================================================ 9
b.H1("9. IPv6")
b.P("C'est le chapitre le plus important si ta machine est exposée. Deux raisons, indépendantes l'une de l'autre.")

b.H2("Raison 1 : il n'y a pas de NAT en IPv6")
b.FIG(F.fig_ipv6(), "En IPv4, la box te protège par effet de bord. En IPv6, elle route — et seul le pare-feu décide.")
b.P("En IPv4, ta machine porte une adresse privée. Personne, depuis Internet, ne peut l'atteindre sans que tu aies "
    "créé une redirection de port sur la box. Cette protection n'est pas voulue : c'est un <b>effet de bord du "
    "manque d'adresses IPv4</b>.")
b.P("En IPv6, les adresses ne manquent pas, donc il n'y a pas de NAT : chaque machine reçoit une adresse publique "
    "et routable. La box se contente de router. <b>Le seul rempart devient ton pare-feu.</b>")
b.CODE("""
ip -6 -br addr          # une adresse en 2xxx: est PUBLIQUE et joignable depuis Internet
                        # une adresse en fe80: est locale au lien, elle ne sort pas
""")
b.BOX("Conséquence directe pour un honeypot : une machine que tu croyais protégée derrière ta box peut être "
      "directement exposée. Et une <font face='DVM'>policy accept</font> oubliée n'est alors plus une négligence "
      "théorique — c'est une machine ouverte sur Internet.", "e")

b.H2("Raison 2 : l'IPv6 dépend d'ICMPv6 pour fonctionner")
b.P("En IPv4, la correspondance entre adresse IP et adresse matérielle se fait par ARP, un protocole distinct qui "
    "échappe au filtrage IP. En IPv6, cette fonction est assurée par <b>ICMPv6</b> — donc par des paquets que ton "
    "pare-feu filtre. Bloquer l'ICMPv6, c'est casser l'IPv6.")
b.TABLE(["Type", "Nom", "Rôle"], [
    ["135", "<font face='DVM'>nd-neighbor-solicit</font>", "« qui possède cette adresse ? » — l'équivalent d'ARP"],
    ["136", "<font face='DVM'>nd-neighbor-advert</font>", "« c'est moi » — la réponse"],
    ["133", "<font face='DVM'>nd-router-solicit</font>", "« y a-t-il un routeur ? »"],
    ["134", "<font face='DVM'>nd-router-advert</font>", "La réponse du routeur : préfixe réseau, route par défaut"],
    ["2", "<font face='DVM'>packet-too-big</font>", "Taille maximale de paquet — sans lui, les gros transferts se figent"],
], [1.6 * cm, 5 * cm, W - 6.6 * cm])
b.BOX("<b>Point qui piège tout le monde :</b> ces messages <b>ne sont liés à aucune connexion</b>. La règle "
      "<font face='DVM'>ct state established,related accept</font> ne les couvre donc pas. Il faut les autoriser "
      "explicitement, <b>et dans les deux chaînes</b> : une sollicitation de voisin part en "
      "<font face='DVM'>output</font> et la réponse arrive en <font face='DVM'>input</font>. "
      "Oublier la chaîne <font face='DVM'>output</font> est l'erreur la plus fréquente.", "w")
b.CODE("""
# à mettre dans input ET dans output
icmpv6 type { nd-neighbor-solicit, nd-neighbor-advert,
              nd-router-solicit, nd-router-advert,
              packet-too-big, time-exceeded, parameter-problem,
              destination-unreachable } accept
""")
b.P("Le symptôme typique de l'oubli : le journal du noyau se remplit de centaines de lignes "
    "<font face='DVM'>PROTO=ICMPv6 TYPE=135</font> refusées, et l'IPv6 devient intermittent sans raison "
    "apparente.")
b.PB()

# ============================================================ 10
b.H1("10. Docker")
b.P("Docker gère lui-même le réseau de ses conteneurs, et il le fait en écrivant ses propres règles de filtrage "
    "au démarrage du service. C'est la principale source de surprises.")
b.FIG(F.fig_docker(), "Le trafic vers un port publié est redirigé avant d'atteindre ta chaîne input, "
                      "puis routé vers le conteneur en traversant forward.")

b.H2("Ce que Docker fait sans te le dire")
b.LI([
    "Il active le routage : <font face='DVM'>net.ipv4.ip_forward=1</font>.",
    "Il crée des chaînes à lui : <font face='DVM'>DOCKER</font>, <font face='DVM'>DOCKER-ISOLATION</font>, "
    "<font face='DVM'>DOCKER-USER</font>.",
    "Pour chaque <font face='DVM'>-p</font>, il ajoute une <b>redirection d'adresse</b> dans "
    "<font face='DVM'>prerouting</font>, c'est-à-dire <b>avant</b> la décision de routage.",
    "Il traduit les adresses sortantes des conteneurs en <font face='DVM'>postrouting</font>.",
])
b.BOX("<b>Les deux conséquences à retenir :</b><br/>"
      "1. Un <font face='DVM'>-p 22:2222</font> rend le port joignable <b>quelle que soit ta chaîne "
      "<font face='DVM'>input</font></b>, parce que le paquet est réécrit puis routé vers le conteneur : il ne "
      "passe jamais par <font face='DVM'>input</font>.<br/>"
      "2. Le trafic <i>émis</i> par un conteneur passe par <font face='DVM'>forward</font>, "
      "<b>pas par <font face='DVM'>output</font></b>. Ta chaîne <font face='DVM'>output</font>, si soignée soit-elle, "
      "ne filtre pas ce que fait Cowrie.", "e")

b.H2("Le point d'accroche prévu : DOCKER-USER")
b.P("Docker crée une chaîne vide, <font face='DVM'>DOCKER-USER</font>, évaluée <b>avant</b> ses propres règles, et "
    "il s'engage à ne jamais y toucher. C'est là que doivent aller tes décisions sur le trafic des conteneurs.")
b.CODE("""
# Cowrie a le droit de parler à ELK...
sudo iptables -I DOCKER-USER 1 -d 192.168.1.35 -p tcp --dport 5044 -j ACCEPT
# ...mais à rien d'autre sur le réseau local
sudo iptables -I DOCKER-USER 2 -d 192.168.1.0/24 -j DROP
""")
b.P("L'ordre est vital, et <font face='DVM'>-I … 1</font> / <font face='DVM'>-I … 2</font> sert précisément à le "
    "maîtriser : inversées, ces deux règles bloqueraient aussi les logs.")
b.BOX("<b>La persistance est le vrai problème.</b> Docker recrée ses chaînes à chaque redémarrage du service, et "
      "tes ajouts disparaissent. Trois approches : le paquet <font face='DVM'>iptables-persistent</font> ; un "
      "<font face='DVM'>ExecStartPost</font> ajouté à <font face='DVM'>docker.service</font> ; ou — la plus propre — "
      "une chaîne nftables branchée sur <font face='DVM'>forward</font> avec une "
      "<font face='DVM'>priority</font> inférieure à 0, donc évaluée avant celles de Docker.", "w")

b.H2("L'option radicale")
b.CODE("""
/etc/docker/daemon.json
{ "iptables": false }
""")
b.P("Docker cesse alors de toucher au pare-feu, et tu écris toi-même les redirections et la traduction d'adresses "
    "en nftables. Plus propre et parfaitement lisible — mais tout ce que Docker faisait automatiquement devient "
    "ton travail, y compris la sortie Internet des conteneurs. À réserver au moment où le reste est maîtrisé.")
b.PB()

# ============================================================ 11
b.H1("11. Écrire, tester, déboguer")
b.FIG(F.fig_debug(), "La boucle de travail. Le journal n'est pas un constat d'échec : "
                     "c'est lui qui dicte la règle suivante.")

b.H2("Les trois outils de diagnostic")
b.H3("1. Le journal — ce qui a été refusé")
b.CODE("""
# une règle de journalisation, juste avant la fin de chaque chaîne
log prefix "OUT-DROP " level info limit rate 5/minute

sudo dmesg | grep OUT-DROP           # relire
sudo journalctl -kf | grep DROP      # suivre en direct
""")
b.P("Une ligne se lit ainsi :")
b.CODE("""
OUT-DROP IN= OUT=wlp3s0 SRC=192.168.1.63 DST=8.8.8.8 PROTO=UDP SPT=51923 DPT=53
         ~~~ ~~~~~~~~~~ ~~~~~~~~~~~~~~~~ ~~~~~~~~~~~ ~~~~~~~~~ ~~~~~~~~~ ~~~~~~
          |      |            |               |          |         |       `-- port destination
          |      |            |               |          |         `---------- port source
          |      |            |               |          `-------------------- protocole
          |      |            |               `------------------------------- vers qui
          |      |            `----------------------------------------------- de qui
          |      `------------------------------------------------------------ interface de sortie
          `------------------------------------------------------------------- vide = paquet émis par nous
""")
b.BOX("<b>Les deux champs qui résolvent presque tout :</b> <font face='DVM'>PROTO=</font> et "
      "<font face='DVM'>DPT=</font>. Ils te disent exactement quel flux manque. Dans l'exemple ci-dessus : "
      "UDP vers le port 53, c'est du DNS — il manque la règle DNS. Aucune supposition n'est nécessaire.", "i")
b.P("Le <font face='DVM'>limit rate 5/minute</font> n'est pas décoratif : sans lui, un scan de ports ou une "
    "tempête NDP remplit le journal à la vitesse du disque.")

b.H3("2. Les compteurs — ce qui a matché")
b.CODE("""
sudo nft list ruleset -a                       # -a affiche aussi les "handle"
sudo nft add rule inet filter output ip daddr 192.168.1.35 counter
sudo nft list chain inet filter output         # lire les compteurs
""")
b.P("Un compteur à zéro sur une règle que tu croyais utilisée est le signe le plus fiable qu'elle ne matche pas. "
    "C'est ce test, appliqué à la règle ELK, qui aurait révélé l'inversion "
    "<font face='DVM'>saddr</font> / <font face='DVM'>daddr</font> en quelques secondes.")

b.H3("3. Les tests, dans le bon ordre")
b.TABLE(["Question", "Commande"], [
    ["La route existe-t-elle ?", "<font face='DVM'>ip route get 192.168.1.35</font>"],
    ["La machine répond-elle ?", "<font face='DVM'>ping -c2 192.168.1.35</font>"],
    ["Le port est-il joignable ?", "<font face='DVM'>nc -zv 192.168.1.35 5044</font>"],
    ["La résolution fonctionne-t-elle ?", "<font face='DVM'>getent hosts example.com</font>"],
    ["Que voit-on de l'extérieur ?", "<font face='DVM'>nmap -p- 192.168.1.63</font> depuis une autre machine"],
], [7 * cm, W - 7 * cm])
b.BOX("<b>Le seul test qui prouve quelque chose</b> pour l'accès SSH est une <b>nouvelle</b> connexion. Une session "
      "déjà ouverte survit grâce à <font face='DVM'>ct state established</font>, même si ta règle d'ouverture est "
      "fausse. C'est le piège qui coûte des machines : tout semble aller bien jusqu'au moment où l'on se "
      "déconnecte.", "e")

b.H2("Le filet de sécurité, en une ligne")
b.CODE("""
sudo systemd-run --on-active=180 --unit=fw-rollback nft flush ruleset
# ... appliquer, tester, ouvrir une NOUVELLE session SSH ...
sudo systemctl stop fw-rollback.timer     # annuler le filet, une fois rassuré
""")
b.P("Le principe : programmer <b>à l'avance</b> l'effacement de toutes les règles. Si tu te bloques, tu attends "
    "trois minutes et l'accès revient. À préférer à <font face='DVM'>sleep &amp;</font> : la tâche est portée par "
    "systemd, donc elle survit à la perte de ta session — ce qui est exactement le scénario redouté.")
b.PB()

# ============================================================ 12
b.H1("12. Mémo")
b.H2("Les commandes")
b.TABLE(["Commande", "Effet"], [
    ["<font face='DVM'>nft list ruleset</font>", "Affiche toutes les règles actives, <b>policy comprise</b>"],
    ["<font face='DVM'>nft list ruleset -a</font>", "Idem, avec les <i>handle</i> nécessaires pour supprimer une règle"],
    ["<font face='DVM'>nft -c -f fichier</font>", "<b>Vérifie la syntaxe sans rien appliquer</b>"],
    ["<font face='DVM'>nft -f fichier</font>", "Charge le fichier"],
    ["<font face='DVM'>nft flush ruleset</font>", "Efface tout — plus aucun filtrage"],
    ["<font face='DVM'>nft delete rule inet filter output handle 7</font>", "Supprime une règle précise"],
    ["<font face='DVM'>nft monitor</font>", "Affiche en direct les modifications du ruleset (utile avec Docker)"],
    ["<font face='DVM'>systemctl enable --now nftables</font>", "Recharge <font face='DVM'>/etc/nftables.conf</font> au démarrage"],
], [8 * cm, W - 8 * cm])

b.H2("Les conditions les plus courantes")
b.TABLE(["Expression", "Signification"], [
    ["<font face='DVM'>iif lo</font> / <font face='DVM'>oif lo</font>", "Interface d'entrée / de sortie (ici le bouclage)"],
    ["<font face='DVM'>ip saddr 192.168.1.33</font>", "Adresse source IPv4"],
    ["<font face='DVM'>ip daddr 192.168.1.0/24</font>", "Adresse de destination dans un sous-réseau"],
    ["<font face='DVM'>ip daddr != 192.168.1.0/24</font>", "Négation : tout sauf ce sous-réseau"],
    ["<font face='DVM'>tcp dport { 80, 443 }</font>", "Port de destination dans un ensemble"],
    ["<font face='DVM'>tcp dport 1024-65535</font>", "Intervalle de ports"],
    ["<font face='DVM'>ct state established,related</font>", "Connexion déjà connue du suivi"],
    ["<font face='DVM'>ct state new</font>", "Ouverture de connexion — c'est là qu'on décide"],
    ["<font face='DVM'>icmpv6 type nd-neighbor-solicit</font>", "Voisinage IPv6 — indispensable, non couvert par <font face='DVM'>related</font>"],
    ["<font face='DVM'>meta l4proto</font>", "Protocole de transport, indépendamment de la version d'IP"],
    ["<font face='DVM'>limit rate 5/minute</font>", "Limitation de débit, pour les journaux notamment"],
], [8 * cm, W - 8 * cm])

b.H2("Les sept erreurs qui coûtent une machine")
b.TABLE(["#", "Erreur", "Symptôme"], [
    ["1", "Oublier <font face='DVM'>policy drop</font>", "Aucun. Le pare-feu ne filtre rien et rien ne le signale"],
    ["2", "Oublier <font face='DVM'>established</font> dans <font face='DVM'>output</font>",
     "La session SSH gèle dès l'application des règles"],
    ["3", "Confondre <font face='DVM'>saddr</font> et <font face='DVM'>daddr</font>",
     "La règle ne matche jamais, sans message d'erreur"],
    ["4", "Oublier le DNS", "« Internet ne marche plus » — alors que c'est la résolution de noms"],
    ["5", "Oublier <font face='DVM'>iif lo</font>", "Le DNS local casse, les services qui se parlent en interne échouent"],
    ["6", "Oublier l'ICMPv6 en sortie", "IPv6 intermittent, journal saturé de types 135/136"],
    ["7", "Oublier <font face='DVM'>systemctl enable nftables</font>", "Tout fonctionne… jusqu'au prochain redémarrage"],
], [0.8 * cm, 7.4 * cm, W - 8.2 * cm])

b.H2("Le squelette à recopier")
b.CODE("""
#!/usr/sbin/nft -f
flush ruleset

define ADMIN_IP = 192.168.1.33
define LAN      = 192.168.1.0/24

table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state invalid drop
        ct state established,related accept
        iif lo accept
        icmpv6 type { nd-neighbor-solicit, nd-neighbor-advert, nd-router-advert,
                      packet-too-big, time-exceeded, parameter-problem,
                      destination-unreachable, echo-request } accept
        ip saddr $LAN icmp type echo-request accept
        # --- ouvertures autorisées ---
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
        icmpv6 type { nd-neighbor-solicit, nd-neighbor-advert, nd-router-solicit,
                      packet-too-big, time-exceeded, parameter-problem,
                      destination-unreachable } accept
        # --- sorties autorisées ---
        log prefix "OUT-DROP " level info limit rate 5/minute
    }
}
""", keep=False)

b.BOX("<b>La seule chose à retenir si tu ne devais en retenir qu'une.</b> Un pare-feu ne se relit pas, il se "
      "teste. Écris la règle, applique, provoque le flux, lis le journal. Le journal te dira toujours ce qui "
      "manque — et il ne se trompe jamais, contrairement au raisonnement qu'on tient devant son fichier.", "g")

build(b.story, "/home/ubuserv/CyberProject/Cours-nftables.pdf",
      "nftables — le cours", "nftables — filtrer le trafic d'une machine Linux", "nftables, pare-feu, Linux")
print("OK")
