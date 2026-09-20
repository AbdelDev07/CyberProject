"""Schémas vectoriels pour le cours et la correction."""
from common import *
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle, Ellipse, PolyLine

WD = 470.0  # largeur utile des figures


def D(h):
    d = Drawing(WD, h)
    return d


# ------------------------------------------------------------------ 1. topologie
def fig_topologie():
    d = D(210)
    # Internet
    d.add(Ellipse(60, 170, 46, 20, fillColor=colors.HexColor("#e8eaf0"), strokeColor=DGREY, strokeWidth=0.9))
    txt(d, 60, 170, "Internet", 8.5, NAVY, "DV-B")
    # Freebox
    box(d, 195, 170, 110, 34, "Freebox (routeur/NAT)\n192.168.1.254", LBLUE, BLUE, NAVY, 7.6)
    arrow(d, 107, 170, 139, 170, DGREY)
    txt(d, 123, 183, "IPv4 : NAT\nIPv6 : routé", 6.2, DGREY)
    # bus LAN
    d.add(Line(30, 112, 445, 112, strokeColor=NAVY, strokeWidth=2.2))
    txt(d, 415, 120, "LAN 192.168.1.0/24", 7.4, NAVY, "DV-B", anchor="end")
    d.add(Line(195, 153, 195, 112, strokeColor=NAVY, strokeWidth=1.4))

    def leaf(x, title, sub, fill, stroke, dash=None):
        d.add(Line(x, 112, x, 86, strokeColor=NAVY, strokeWidth=1.2))
        box(d, x, 62, 104, 46, title + "\n" + sub, fill, stroke, NAVY, 7.3, dash=dash)

    leaf(72, "PC admin", "192.168.1.33\nSSH -> 2727", LGREEN, GREEN)
    leaf(195, "HONEYPOT", "192.168.1.63\nCowrie + nftables", LORANGE, ORANGE)
    leaf(318, "VM ELK", "192.168.1.35\nLogstash 5044", LBLUE, BLUE)
    leaf(422, "?", "192.168.1.178\nvu dans IN-DROP", colors.HexColor("#f4f4f5"), DGREY, dash=[2, 2])

    arrow(d, 240, 62, 274, 62, GREEN, 1.4, label="logs")
    txt(d, 235, 20, "Seul flux sortant autorisé vers le LAN : 192.168.1.63 → 192.168.1.35:5044 (tcp)",
        7.6, GREEN, "DV-B")
    return d


# ------------------------------------------------------------------ 2. hooks
def fig_hooks():
    d = D(250)
    y0 = 200      # ligne haute (forward)
    ym = 140      # ligne pre/post
    yb = 62       # ligne locale

    box(d, 42, ym, 62, 30, "carte\nréseau", GREY, DGREY, NAVY, 7.2)
    box(d, 140, ym, 86, 30, "PREROUTING", colors.HexColor("#ede9fe"), colors.HexColor("#6d28d9"),
        colors.HexColor("#4c1d95"), 7.6, sw=1.2)
    box(d, 336, ym, 86, 30, "POSTROUTING", colors.HexColor("#ede9fe"), colors.HexColor("#6d28d9"),
        colors.HexColor("#4c1d95"), 7.6, sw=1.2)
    box(d, 432, ym, 62, 30, "carte\nréseau", GREY, DGREY, NAVY, 7.2)

    box(d, 238, y0, 96, 30, "FORWARD", LORANGE, ORANGE, colors.HexColor("#7a4a00"), 8.2, sw=1.4)
    box(d, 160, yb, 86, 30, "INPUT", LGREEN, GREEN, colors.HexColor("#0d3d1d"), 8.2, sw=1.4)
    box(d, 316, yb, 86, 30, "OUTPUT", LRED, RED, colors.HexColor("#5b160e"), 8.2, sw=1.4)
    box(d, 238, 16, 150, 26, "processus local\n(sshd, curl, apt…)", colors.white, NAVY, NAVY, 7.4)

    arrow(d, 73, ym, 97, ym, DGREY)
    # route -> forward
    elbow(d, [(183, ym), (206, ym), (206, y0), (190, y0)], ORANGE, 1.3)
    elbow(d, [(286, y0), (302, y0), (302, ym), (293, ym)], ORANGE, 1.3)
    # route -> input
    elbow(d, [(140, 125), (140, yb), (117, yb)], GREEN, 1.3)
    arrow(d, 203, yb, 238, 29, GREEN, 1.3)
    # output
    arrow(d, 238, 29, 273, yb, RED, 1.3)
    elbow(d, [(359, yb), (382, yb), (382, 125)], RED, 1.3)
    arrow(d, 379, ym, 401, ym, DGREY)

    txt(d, 206, 228, "le paquet TRAVERSE la machine (conteneurs Docker !)", 6.9, ORANGE, "DV-B")
    txt(d, 96, 96, "pour\nnous", 6.6, GREEN, "DV-B")
    txt(d, 400, 96, "émis\npar nous", 6.6, RED, "DV-B")
    txt(d, 148, 104, "décision\nde routage", 6.2, DGREY, anchor="start")
    return d


# ------------------------------------------------------------------ 3. arbo
def fig_arbo():
    d = D(196)
    box(d, 118, 172, 190, 28, "table inet filter", NAVY, NAVY, colors.white, 9, font="DVM-B")
    txt(d, 300, 178, "famille : ip (v4) · ip6 (v6) · inet (les deux)", 7.2, DGREY, anchor="start")
    txt(d, 300, 166, "nom libre : « filter » est une convention", 7.2, DGREY, anchor="start")

    ys = [128, 88, 48]
    names = ["chain input", "chain forward", "chain output"]
    cols = [(LGREEN, GREEN), (LORANGE, ORANGE), (LRED, RED)]
    d.add(Line(40, 158, 40, 48, strokeColor=NAVY, strokeWidth=1))
    for y, n, (f, s) in zip(ys, names, cols):
        d.add(Line(40, y, 58, y, strokeColor=NAVY, strokeWidth=1))
        box(d, 128, y, 140, 26, n, f, s, NAVY, 8.4, font="DVM")
    txt(d, 300, 134, "type filter hook input priority filter; policy drop;", 7.1, DGREY, "DVM", anchor="start")
    txt(d, 300, 122, "^ où l'on se branche          ^ défaut si rien ne matche", 6.4, DGREY, anchor="start")

    box(d, 128, 16, 300, 22, "règle : ip daddr 192.168.1.35 tcp dport 5044 accept", CODEBG, BORDER, NAVY, 7.8, font="DVM")
    d.add(Line(128, 35, 128, 27, strokeColor=DGREY, strokeWidth=0.9))
    txt(d, 300, 16, "conditions … puis verdict", 7, DGREY, anchor="start")
    return d


# ------------------------------------------------------------------ 4. évaluation
def fig_chain_eval():
    d = D(250)
    x = 150
    rows = [
        ("ct state invalid drop", "non", LRED, RED),
        ("ct state established,related accept", "non", LGREEN, GREEN),
        ("iif lo accept", "non", LGREEN, GREEN),
        ("tcp dport 2727 ip saddr 192.168.1.33 accept", "OUI", LGREEN, GREEN),
        ("tcp dport 22 accept", "", GREY, DGREY),
        ("log prefix \"IN-DROP \"", "", GREY, DGREY),
    ]
    y = 214
    for i, (r, m, f, s) in enumerate(rows):
        dim = (m == "")
        box(d, x, y, 268, 22, r, f if not dim else colors.HexColor("#fafafa"),
            s if not dim else colors.HexColor("#d4d4d8"),
            NAVY if not dim else colors.HexColor("#a1a1aa"), 7.4, font="DVM")
        if m == "non":
            txt(d, 300, y, "pas de match → règle suivante", 6.8, DGREY, anchor="start")
            arrow(d, x, y - 11, x, y - 24, DGREY, 0.9, 4)
        elif m == "OUI":
            arrow(d, 286, y, 312, y, GREEN, 1.5, 5)
            txt(d, 318, y + 10, "MATCH → accept", 7.4, GREEN, "DV-B", anchor="start")
            txt(d, 318, y - 14, "le paquet sort de la chaîne :\nles règles suivantes ne sont\njamais évaluées", 6.4, GREEN, anchor="start")
        y -= 34
    box(d, x, y + 6, 268, 22, "policy drop   ← le filet du fond", colors.HexColor("#fee2e2"), RED, colors.HexColor("#7f1d1d"), 7.6, font="DVM-B")
    txt(d, x, 246, "paquet entrant : tcp 192.168.1.33:51234 → 192.168.1.63:2727", 7.6, NAVY, "DV-B")
    return d


# ------------------------------------------------------------------ 5. conntrack
def fig_conntrack():
    d = D(212)
    box(d, 62, 172, 104, 30, "paquet reçu", GREY, DGREY, NAVY, 8)
    box(d, 218, 172, 120, 30, "conntrack\nregarde sa table", LBLUE, BLUE, NAVY, 7.8)
    arrow(d, 116, 172, 156, 172, DGREY)

    states = [
        (150, "NEW", "1re fois qu'on voit\ncette connexion", LORANGE, ORANGE),
        (108, "ESTABLISHED", "connexion déjà connue,\ndans les deux sens", LGREEN, GREEN),
        (66, "RELATED", "liée à une autre\n(erreur ICMP, FTP-data)", LGREEN, GREEN),
        (24, "INVALID", "incohérent : hors séquence,\nsans connexion connue", LRED, RED),
    ]
    for y, n, expl, f, s in states:
        elbow(d, [(280, 172), (300, 172), (300, y), (312, y)], DGREY, 0.9, 4)
        box(d, 356, y, 86, 26, n, f, s, NAVY, 8, font="DV-B")
        txt(d, 404, y, expl, 6.5, DGREY, anchor="start")
    txt(d, 235, 200, "conntrack = mémoire des connexions en cours (pare-feu « à état »)", 7.4, BLUE, "DV-B")
    return d


# ------------------------------------------------------------------ 6. saddr / daddr
def fig_saddr_daddr():
    d = D(250)
    # panneau OUTPUT
    d.add(Rect(4, 132, 462, 108, fillColor=colors.HexColor("#fff7f6"), strokeColor=RED, strokeWidth=0.8, rx=4, ry=4))
    txt(d, 60, 226, "chaîne OUTPUT", 9, RED, "DV-B")
    box(d, 96, 186, 118, 34, "HONEYPOT\n192.168.1.63", LORANGE, ORANGE, NAVY, 7.6)
    box(d, 372, 186, 118, 34, "ELK\n192.168.1.35", LBLUE, BLUE, NAVY, 7.6)
    arrow(d, 158, 190, 310, 190, RED, 1.5, label="le paquet part d'ici")
    txt(d, 234, 166, "saddr = 192.168.1.63  (nous)          daddr = 192.168.1.35  (ELK)", 7.6, NAVY, "DVM")
    txt(d, 234, 148, "→  ip daddr $ELK_IP tcp dport 5044 accept", 8.2, GREEN, "DVM-B")

    # panneau INPUT
    d.add(Rect(4, 14, 462, 106, fillColor=colors.HexColor("#f4fbf6"), strokeColor=GREEN, strokeWidth=0.8, rx=4, ry=4))
    txt(d, 56, 106, "chaîne INPUT", 9, GREEN, "DV-B")
    box(d, 96, 68, 118, 34, "HONEYPOT\n192.168.1.63", LORANGE, ORANGE, NAVY, 7.6)
    box(d, 372, 68, 118, 34, "PC admin\n192.168.1.33", LGREEN, GREEN, NAVY, 7.6)
    arrow(d, 310, 72, 158, 72, GREEN, 1.5, label="le paquet arrive ici")
    txt(d, 234, 48, "saddr = 192.168.1.33  (le PC)          daddr = 192.168.1.63  (nous)", 7.6, NAVY, "DVM")
    txt(d, 234, 30, "→  tcp dport 2727 ip saddr $ADMIN_IP accept", 8.2, GREEN, "DVM-B")
    return d


# ------------------------------------------------------------------ 7. DNS
def fig_dns():
    d = D(226)
    txt(d, 235, 216, "Ce qui se passe réellement derrière un simple  curl https://archive.ubuntu.com", 8, NAVY, "DV-B")
    steps = [
        (52, "curl", GREY, DGREY),
        (150, "systemd-\nresolved\n127.0.0.53", LBLUE, BLUE),
        (286, "8.8.8.8 : 53\nudp", LORANGE, ORANGE),
        (418, "185.125.x.x\ntcp 443", LGREEN, GREEN),
    ]
    for x, t, f, s in steps:
        box(d, x, 160, 92, 44, t, f, s, NAVY, 7.4)
    arrow(d, 98, 160, 104, 160, DGREY, 1.1, 4)
    arrow(d, 196, 172, 240, 172, ORANGE, 1.4)
    txt(d, 218, 186, "1. quelle IP ?", 6.6, ORANGE, "DV-B")
    arrow(d, 240, 150, 196, 150, ORANGE, 1.4)
    txt(d, 218, 136, "2. voici l'IP", 6.6, ORANGE, "DV-B")
    arrow(d, 332, 160, 372, 160, GREEN, 1.4)
    txt(d, 352, 174, "3. HTTPS", 6.6, GREEN, "DV-B")

    d.add(Rect(220, 92, 132, 30, fillColor=LRED, strokeColor=RED, strokeWidth=1, rx=3, ry=3))
    txt(d, 286, 107, "bloqué ici par OUT-DROP", 7.4, RED, "DV-B")
    arrow(d, 286, 124, 286, 136, RED, 1.2, 4)

    txt(d, 235, 66, "Symptôme observé : « le web ne marche pas » — en réalité l'étape 3 n'est jamais atteinte.", 7.8, NAVY)
    txt(d, 235, 50, "Le paquet bloqué n'est pas du 443 : c'est de l'UDP/53.", 7.8, RED, "DV-B")
    txt(d, 235, 30, "Preuve dans tes logs :  OUT-DROP … PROTO=UDP … DPT=53   (111 paquets)", 7.4, DGREY, "DVM")
    return d


# ------------------------------------------------------------------ 8. policy
def fig_policy():
    d = D(196)

    def panel(x0, title, pol, col, lcol, verdict, vc, note):
        d.add(Rect(x0, 18, 218, 164, fillColor=colors.white, strokeColor=col, strokeWidth=1.1, rx=4, ry=4))
        band(d, x0 + 109, 168, 218, 26, title, col)
        ys = [140, 118, 96]
        for i, r in enumerate(["… accept", "… accept", "… accept"]):
            box(d, x0 + 109, ys[i], 186, 17, r, CODEBG, BORDER, DGREY, 7, font="DVM")
        box(d, x0 + 109, 72, 186, 18, 'log prefix "DROP "', CODEBG, BORDER, DGREY, 7, font="DVM")
        box(d, x0 + 109, 48, 186, 19, pol, lcol, col, col, 7.6, font="DVM-B")
        txt(d, x0 + 109, 29, verdict, 7.8, vc, "DV-B")
        txt(d, x0 + 109, 8, note, 6.6, DGREY)

    panel(6, "CE QUE TU AS ÉCRIT", "(policy accept implicite)", RED, LRED,
          "→ le paquet non prévu PASSE", RED, "le log s'affiche… et le paquet passe quand même")
    panel(246, "CE QU'IL FAUT", "policy drop", GREEN, LGREEN,
          "→ le paquet non prévu est JETÉ", GREEN, "le log dit ce que tu as oublié d'autoriser")
    return d


# ------------------------------------------------------------------ 9. docker
def fig_docker():
    d = D(228)
    box(d, 54, 190, 92, 30, "attaquant\nInternet", GREY, DGREY, NAVY, 7.4)
    box(d, 186, 190, 112, 30, "PREROUTING\nnat : DNAT -p", colors.HexColor("#ede9fe"),
        colors.HexColor("#6d28d9"), colors.HexColor("#4c1d95"), 7.4)
    box(d, 336, 190, 108, 30, "FORWARD", LORANGE, ORANGE, colors.HexColor("#7a4a00"), 8)
    arrow(d, 102, 190, 128, 190, DGREY)
    arrow(d, 244, 190, 280, 190, DGREY)
    box(d, 336, 126, 150, 30, "conteneur Cowrie\n172.17.0.2:2222", LGREEN, GREEN, NAVY, 7.4)
    arrow(d, 336, 174, 336, 143, ORANGE, 1.3)

    box(d, 130, 126, 132, 30, "chaîne INPUT\npolicy drop", LRED, RED, colors.HexColor("#5b160e"), 7.6)
    ln = Line(176, 176, 140, 145, strokeColor=DGREY, strokeWidth=1.1)
    ln.strokeDashArray = [3, 2]
    d.add(ln)
    d.add(Line(146, 178, 172, 146, strokeColor=RED, strokeWidth=2.6))
    d.add(Line(146, 146, 172, 178, strokeColor=RED, strokeWidth=2.6))
    txt(d, 130, 103, "JAMAIS TRAVERSÉE", 7.4, RED, "DV-B")

    d.add(Rect(246, 44, 200, 44, fillColor=LORANGE, strokeColor=ORANGE, strokeWidth=1, rx=3, ry=3))
    txt(d, 346, 72, "ton point d'accroche :", 7.2, colors.HexColor("#7a4a00"), "DV-B")
    txt(d, 346, 58, "chaîne DOCKER-USER", 8.6, colors.HexColor("#7a4a00"), "DVM-B")
    arrow(d, 346, 90, 346, 108, ORANGE, 1.2, 4)

    txt(d, 120, 62, "Un  -p 2222:22  ouvre le port\nà tout le monde, quelle que soit\nta chaîne input.", 7.4, NAVY)
    txt(d, 235, 14, "Règle à retenir : ce qui entre dans un conteneur passe par FORWARD, pas par INPUT.", 7.6, NAVY, "DV-B")
    return d


# ------------------------------------------------------------------ 10. ipv6
def fig_ipv6():
    d = D(196)
    # v4
    d.add(Rect(6, 106, 458, 78, fillColor=colors.HexColor("#f4fbf6"), strokeColor=GREEN, strokeWidth=0.8, rx=4, ry=4))
    txt(d, 44, 172, "IPv4", 9.5, GREEN, "DV-B")
    box(d, 106, 140, 84, 30, "Internet", GREY, DGREY, NAVY, 7.4)
    box(d, 240, 140, 118, 30, "Freebox\nNAT", LBLUE, BLUE, NAVY, 7.4)
    box(d, 392, 140, 116, 30, "192.168.1.63\nadresse privée", LORANGE, ORANGE, NAVY, 7.2)
    arrow(d, 150, 140, 179, 140, DGREY)
    d.add(Line(299, 155, 299, 125, strokeColor=RED, strokeWidth=2))
    txt(d, 299, 116, "bloqué sauf redirection de port", 6.6, RED, "DV-B")

    # v6
    d.add(Rect(6, 14, 458, 80, fillColor=colors.HexColor("#fff7f6"), strokeColor=RED, strokeWidth=0.8, rx=4, ry=4))
    txt(d, 44, 82, "IPv6", 9.5, RED, "DV-B")
    box(d, 106, 48, 84, 30, "Internet", GREY, DGREY, NAVY, 7.4)
    box(d, 240, 48, 118, 30, "Freebox\nrouteur (pas de NAT)", LBLUE, BLUE, NAVY, 7)
    box(d, 392, 48, 116, 32, "2a01:e0a:abe:f8e0:…\nadresse PUBLIQUE", LRED, RED, colors.HexColor("#5b160e"), 7)
    arrow(d, 150, 48, 179, 48, DGREY)
    arrow(d, 301, 52, 332, 52, RED, 1.6)
    txt(d, 316, 70, "route directe", 6.4, RED, "DV-B")
    return d


# ------------------------------------------------------------------ 11. ordre des règles
def fig_ordre():
    d = D(150)
    txt(d, 235, 140, "L'ordre compte : la première règle qui matche gagne", 8.4, NAVY, "DV-B")

    def col(x0, title, rules, verdict, c, lc):
        d.add(Rect(x0, 16, 214, 104, fillColor=colors.white, strokeColor=c, strokeWidth=1, rx=4, ry=4))
        band(d, x0 + 107, 106, 214, 22, title, c)
        y = 80
        for r, hit in rules:
            box(d, x0 + 107, y, 190, 18, r, lc if hit else CODEBG, c if hit else BORDER,
                NAVY if hit else DGREY, 6.9, font="DVM")
            y -= 22
        txt(d, x0 + 107, 26, verdict, 7.4, c, "DV-B")

    col(8, "DROP en premier", [("ip daddr 192.168.1.0/24 drop", True),
                               ("ip daddr 192.168.1.35 tcp dport 5044 accept", False)],
        "les logs ne partent JAMAIS", RED, LRED)
    col(248, "ACCEPT d'abord, DROP ensuite", [("ip daddr 192.168.1.35 tcp dport 5044 accept", True),
                                              ("ip daddr 192.168.1.0/24 drop", False)],
        "les logs partent, le reste est bloqué", GREEN, LGREEN)
    return d


# ------------------------------------------------------------------ 12. méthode debug
def fig_debug():
    d = D(160)
    steps = [
        ("1. Décrire\nle flux", "qui → qui\nport, protocole", LBLUE, BLUE),
        ("2. Écrire\nla règle", "nft -c -f\n(vérif syntaxe)", LGREEN, GREEN),
        ("3. Tester", "curl / nc / ping\ndepuis la machine", LORANGE, ORANGE),
        ("4. Lire\nle log", "dmesg | grep DROP\nPROTO= et DPT=", LRED, RED),
    ]
    x = 62
    for t, s, f, st in steps:
        box(d, x, 100, 98, 52, t, f, st, NAVY, 8, font="DV-B")
        txt(d, x, 62, s, 6.9, DGREY)
        if x < 380:
            arrow(d, x + 52, 100, x + 63, 100, DGREY, 1.1, 4.5)
        x += 115
    elbow(d, [(408, 74), (408, 40), (62, 40), (62, 72)], DGREY, 1.1, 5)
    txt(d, 235, 14, "le log te dit exactement quel paquet manque : c'est lui qui écrit la règle suivante",
        7.4, NAVY, "DV-B")
    return d
