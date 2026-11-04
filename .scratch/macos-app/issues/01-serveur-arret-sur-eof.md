# 01: Le serveur du dashboard s'arrête quand son canal de contrôle se ferme

**What to build:** `library.py monitor --stop-on-stdin-eof` sert le dashboard comme aujourd'hui et s'arrête proprement (code 0) dès que son entrée standard atteint EOF. Sans l'option, `make monitor` est strictement inchangé. Contrat : section « Contrat du serveur » de [`spec.md`](../spec.md).

**Blocked by:** None (can start immediately)

**Status:** resolved

- [ ] Avec l'option, fermer le pipe stdin arrête le serveur en moins de 3 s et libère le port (test sur port 0).
- [ ] Sans l'option, stdin n'est jamais lu ; `make monitor` et Ctrl+C se comportent comme avant.
- [ ] La ligne `Build monitor: http://127.0.0.1:8767` reste imprimée seulement après un bind réussi ; un bind impossible sort avec un code non nul sans cette ligne.
- [ ] Port, hôtes admis, contrôles Host/Origin, routes et en-têtes inchangés (tests existants verts).
- [ ] `make test` vert.
