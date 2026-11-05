<p align="center"><a href="https://once-email.com"><img src="../assets/unpack-flow-banner.png" alt="UnpackFlow by Once Email" width="100%"></a></p>

# UnpackFlow : décompression imbriquée sans surveillance

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

Avec `-r`, si le nom de sortie existe déjà, UnpackFlow ajoute le dossier source, par exemple `sample-backup-legacy-set-unpacked`, puis `-2`, `-3` pour les collisions suivantes, sans écrasement ni omission.

La petite suite `unpack-flow-minimal-testcases-v1.zip` couvre ZIP, TAR.GZ, Unicode, archives imbriquées, `part01.exe` multipartie et un échec attendu pour volume manquant, sans gros logiciel et sans exécuter le SFX.

La validation native utilise des données synthétiques dans `/data/unpack-flow-testcases` ; le chemin peut être remplacé avec `UNPACK_FLOW_TEST_ROOT`. Les grandes suites restent facultatives et réservées aux performances ou compatibilités supplémentaires.

UnpackFlow traite les distributions logicielles, jeux de données, sauvegardes, ressources multimédias et autres grandes archives. Il détecte le premier volume, extrait les couches successivement et affiche paquet, phase, niveau et durée.

## Utilisation et installation

Utilisez `unpack-flow list 'Archive*'`, `plan`, `unpack-flow 'Archive*'`, `status`. Linux utilise Bash ; Windows PowerShell et 7-Zip ; macOS PowerShell 7+ et `7zz`. `scripts/build-release.sh` produit trois paquets et SHA-256.

Python n'est pas requis pour exécuter `unpack-flow` ou extraire des archives. Python 3 sert uniquement à l'installation automatique du Skill sous Linux/macOS avec `install_local.py` ou `install_local.sh`, ainsi qu'à l'audit Python. Windows utilise `install_local.ps1` en PowerShell ; la copie manuelle du Skill ne nécessite pas Python.

## Scénarios de décompression pris en charge

UnpackFlow extrait en lot des dossiers ou des motifs, déroule les archives imbriquées couche par couche et reconnaît le premier volume des ensembles RAR fractionnés. Il inspecte aussi les archives RAR auto-extractibles sans lancer d'EXE inconnu. Il convient aux logiciels, données, sauvegardes, médias, journaux et images ISO ou WIM.

Par défaut, il parcourt jusqu'à 10 couches internes. Une archive interne endommagée ou incomplète est conservée, signalée et ignorée afin de poursuivre les autres traitements ; utilisez `-StopOnError` pour arrêter au premier échec.

## Exemples d'apprentissage

Utilisez `list`, `plan`, `start`, `status`, `log` et `wait` pour les sauvegardes, données, journaux, logiciels ou archives fractionnées. Le jeu n'est qu'un exemple, pas la limite du produit.

Sur les trois systèmes, `run` reste au premier plan avec la progression, tandis que `start` lance une tâche en arrière-plan et renvoie son identifiant.

Pendant les longues opérations 7-Zip ou UnRAR, le temps est actualisé chaque seconde et un signal d'activité est journalisé toutes les 30 secondes.

Sous macOS et Windows, `start` détache tous les flux interactifs ; la progression va uniquement au journal, sans séquences ANSI ni bips du terminal.

Utilisez `-r` ou `-Recursive` pour découvrir toutes les archives des sous-dossiers et extraire leurs couches internes ; un conflit de nom produit `nom-unpacked`.

`unpack-flow run *` est également accepté. Même si le shell développe `*`, l'analyse ne conserve que les archives simples et les premiers volumes tels que `part1.exe`, `part1.rar`, `.7z.001` ou `.zip.001`, en écartant `.sha256`, les fichiers sans rapport et les volumes suivants.

`unpack-flow help` affiche l'aide combinée en anglais et en chinois simplifié.

## Tâches en arrière-plan et journaux

`unpack-flow start "archive" -Output "destination"` lance l'extraction en arrière-plan et renvoie un identifiant. Utilisez `unpack-flow status [id]`, `unpack-flow log [id]` et `unpack-flow wait [id]` ; sans identifiant, la dernière tâche est utilisée. Les journaux se trouvent dans `%LOCALAPPDATA%\unpack-flow\state` sous Windows et `~/.local/state/unpack-flow` sous macOS/Linux.

TAR, TAR.GZ/TGZ et GZ autonome sont pris en charge. Après 7-Zip, le programme essaie selon le format UnRAR, `tar`, GZip ou ZIP natif, nettoie chaque tentative échouée puis, si toutes les options échouent, conserve l'archive, journalise l'échec et poursuit la suivante sans boucle infinie.

Linux x64 inclut l'UnRAR 7.23 officiel. Windows x64/ARM64 inclut la version complète officielle de 7-Zip 26.02 ; x64 inclut aussi UnRAR. Les paquets et licences d'origine sont conservés.

## Démarrage rapide complet

```bash
unpack-flow list '/data/archives/*'
unpack-flow plan '/data/archives/backup.part1.rar'
unpack-flow run '/data/archives/*' -Output '/data/extracted'
```

Pour lancer une tâche en arrière-plan :

```bash
unpack-flow start '/data/archives/*' -Output '/data/extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

`run` reste au premier plan ; `start` renvoie immédiatement un identifiant. Les archives sources sont conservées dans les deux cas.

## Installer l’outil en ligne de commande

### Linux

```bash
./install-linux.sh --check
./install-linux.sh
unpack-flow version
```

### macOS

```bash
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

### Windows

```bat
install.bat -Check
install.bat
unpack-flow version
```

Les vérifications signalent les dépendances manquantes sans installer automatiquement de logiciel système.

## Récursion, journaux et erreurs

Utilisez `-r` ou `-Recursive` pour parcourir les sous-dossiers et ouvrir les couches internes. La limite par défaut est de 10 couches internes.

| Plateforme | Répertoire d’état par défaut |
|---|---|
| Windows | `%LOCALAPPDATA%\unpack-flow\state` |
| Linux/macOS | `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` |

UnpackFlow suit une chaîne limitée : 7-Zip, UnRAR pour RAR, puis les outils natifs adaptés à TAR, GZ ou ZIP. Chaque tentative incomplète est nettoyée. Si tout échoue, l’archive est conservée, l’erreur est journalisée et le traitement continue. Utilisez `-StopOnError` uniquement pour arrêter au premier échec.

## Tests et installation comme Agent Skill

```bash
bash tests/generate-minimal-public-suite.sh
bash tests/test-minimal-public-suite.sh
pwsh -NoProfile -File tests/test-minimal-public-suite.ps1
scripts/install_local.sh .
```

Sous Windows, installez le Skill avec `scripts/install_local.ps1`. Python n’est pas nécessaire pour l’extraction ; il sert uniquement à l’installation automatisée du Skill sous Linux/macOS et à l’audit Python.

## Sécurité, projet et assistance

UnpackFlow conserve les fichiers sources, n’écrase pas les destinations et n’exécute aucun fichier EXE inconnu.

- Site officiel : [once-email.com](https://once-email.com)
- Créatrice et développeuse : helen.jar
- Projet GitHub : [pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow)
- E-mail d’assistance : [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

Pour toute question, écrivez à [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com) ou [ouvrez un ticket GitHub](https://github.com/pangxin12345/unpack-flow/issues).

Licence MIT, version 2.1.4.
