# La méthode : apprendre avec une IA sans lui déléguer l'apprentissage

Ce dépôt documente un projet de sécurité fait **avec** Claude (Claude Code, exécuté sur la machine cible), selon une règle simple : **l'IA enseigne et corrige, je manipule.**

## Le contrat

| Claude fait | Je fais |
|---|---|
| Écrit les TP : objectifs, indices, tests de vérification — jamais la solution | Toutes les manipulations sur la machine |
| Lit l'état réel de la machine (fichiers, `nft list ruleset`, `dmesg`) pour corriger | J'annote le TP avec mes réponses et mes blocages |
| Écrit le cours **après** le TP, ciblé sur ce que je n'ai pas compris | Je relis, je refais, je pose des questions |
| Fait une action à ma place **uniquement** quand je le demande explicitement (reset initial, pose du pare-feu final) | Je garde la main sur tout ce qui est irréversible : reboot, réseau |

## Pourquoi ça marche

- La correction porte sur **mes** erreurs, prouvées par **mes** journaux — pas sur une liste d'erreurs génériques. La ligne `OUT-DROP … PROTO=UDP … DPT=53` de mon `dmesg` m'apprend plus que n'importe quel paragraphe sur le DNS.
- Le cours arrive **après** l'échec, quand la question est déjà posée dans ma tête.
- Les erreurs sont conservées dans le dépôt. Un ruleset sans `policy drop` qui « marche » est un meilleur souvenir qu'un ruleset parfait copié-collé.

## Ce que ça ne remplace pas

Claude a lui-même produit un incident en posant le pare-feu (`systemctl start nftables` a effacé sa règle temporaire — voir le [journal](../journal/2026-09-20-nftables.md)). Il l'a constaté, corrigé, et transformé en exercice. Une IA qui manipule une machine en production a besoin des mêmes filets de sécurité qu'un humain — et de quelqu'un qui relit.

## Chronologie

| Date | Étape |
|---|---|
| 18/09/2026 | Reset de la machine · TP 1 pare-feu (PDF) |
| 18–20/09 | Je fais le TP 1, je bloque sur les règles |
| 20/09 | Correction du TP 1 à partir de la machine · Cours nftables · Pose du pare-feu final · TP 2 |
