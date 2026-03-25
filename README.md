# RAT-Python

Projet final M1 Cybersécurité ESGI — Remote Administration Tool en Python.

> **Projet éducatif uniquement.** Ne pas utiliser sur des machines sans autorisation.

## Description

RAT client/serveur avec communication chiffrée (ChaCha20-Poly1305, échange de clé ECDH X25519).
Le client (agent) tourne sur la cible, le serveur sur la machine de l'opérateur.

## Installation

Prérequis : Python 3.10+, [Poetry](https://python-poetry.org/)

```bash
git clone git@github.com:jackalstv/RAT-Python-ESGI.git
cd RAT-Python-ESGI
poetry install
pre-commit install
```

## Lancement

Serveur :
```bash
poetry run python -m src.main server
poetry run python -m src.main server --host 0.0.0.0 --port 8888
```

Client :
```bash
poetry run python -m src.main client --host <IP_SERVEUR> --port 8888
```

## Commandes

### Menu serveur (`rat >`)

- `sessions` — liste les agents connectés
- `interact <id>` — interagir avec un agent
- `help` — aide
- `exit` — quitter

### Menu agent (`rat agent X >`)

- `help` — aide
- `shell <cmd>` — exécuter une commande
- `ipconfig` — infos réseau
- `screenshot` — capture écran
- `download <path>` — télécharger un fichier depuis l'agent
- `upload <local> <distant>` — envoyer un fichier vers l'agent
- `search <nom>` — rechercher un fichier
- `hashdump` — dump /etc/shadow ou SAM
- `keylogger start/stop` — keylogger
- `webcam_snapshot` — photo webcam
- `webcam_stream` — stream webcam (CTRL+C pour stop)
- `record_audio <sec>` — enregistrer le micro
- `back` — retour menu principal

## Tests

```bash
poetry run pytest tests/ -v
```

## Architecture

```
src/
├── main.py
├── client/
│   ├── agent.py
│   ├── commands/
│   │   ├── capture.py
│   │   ├── files.py
│   │   ├── monitoring.py
│   │   └── system.py
│   └── network/
│       └── connection.py
├── server/
│   ├── server.py
│   ├── session.py
│   ├── cli.py
│   └── network/
│       └── listener.py
└── utils/
    ├── config.py
    ├── crypto.py
    ├── lib.py
    ├── logger.py
    └── protocol.py
```

## Auteurs

- André MARTINS
- Théo DELABRE
