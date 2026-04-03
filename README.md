<div align="center">

# 🎓 Skaolink

**Plateforme de Gestion Académique Sécurisée**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Nginx](https://img.shields.io/badge/Nginx-1.24-009639?style=flat-square&logo=nginx&logoColor=white)](https://nginx.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](./LICENSE)

*Projet réalisé dans le cadre du module **GCS2-UE7-2 DevSecOps** — Mars/Avril 2026*

</div>

---

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Stack technique](#-stack-technique)
- [Structure du projet](#-structure-du-projet)
- [Installation & déploiement](#-installation--déploiement)
- [Rôles & RBAC](#-rôles--rbac)
- [Sécurité](#-sécurité)
- [Pipeline CI/CD](#-pipeline-cicd)
- [Contributeurs](#-contributeurs)

---

## 🌐 Vue d'ensemble

Skaolink est une plateforme web multi-rôles permettant à un établissement scolaire de gérer de manière centralisée et sécurisée :

- Les **apprenants** et leurs **classes**
- Les **notes** et **évaluations**
- Les **absences** et alertes de suivi
- Les **emplois du temps**
- L'**agenda des devoirs**
- Une **messagerie instantanée** (WebSocket)
- Des **visioconférences** de classe *(bonus)*

L'accès est entièrement contrôlé par un système **RBAC (Role-Based Access Control)** à trois niveaux, implémenté côté serveur via des décorateurs Python. Toute tentative d'accès non autorisé renvoie un **HTTP 403 Forbidden**.

---

## ✨ Fonctionnalités

| Fonctionnalité | Description | Technologies |
|---|---|---|
| 🔐 Authentification | Connexion par email/mdp, session sécurisée, anti brute-force (5 req/min) | Flask-Login, bcrypt, Flask-Limiter |
| 📊 Notes & moyennes | Saisie par le prof, calcul côté serveur, mise à jour automatique du statut | SQLAlchemy, WTForms |
| 📅 Emploi du temps | Grille hebdomadaire interactive, API JSON Flask | FullCalendar.js 6.x |
| 🚨 Absences | Saisie avec motif, alerte si > 10h, visualisation statistiques | SQLAlchemy, Chart.js 4.x |
| 📝 Devoirs | Agenda par classe, publication prof → visible élèves | SQLAlchemy, WTForms |
| 💬 Messagerie DM | Temps réel via WebSocket, persistance MySQL, multi-workers via Redis | Flask-SocketIO, Redis 7 |
| 🔔 Notifications | Alertes système temps réel (statut, absences) | Flask-SocketIO, Redis pub/sub |
| 📹 Visioconférence | Salle Jitsi par classe, auth par token JWT généré par Flask | Jitsi self-hosted, PyJWT |

---

## 🏗️ Architecture

L'application tourne entièrement sur une **VM Ubuntu 22.04 LTS** unique. Docker Compose orchestre quatre services qui communiquent via un réseau bridge interne (`skaolink_net`). **Seul Nginx est exposé à Internet.**

```
INTERNET
    │ HTTPS :443 / HTTP :80 (redirect)
    ▼
┌─────────────────────┐
│     Nginx 1.24       │  ← Reverse Proxy · TLS 1.2/1.3 · Rate Limiting
└──────────┬──────────┘
           │ HTTP interne :5000
┌──────────▼──────────────────────────────┐
│         Gunicorn + Flask 3.x             │
│   (worker-class: eventlet pour SocketIO) │
│  Blueprints: auth · apprenants · classes │
│             notes · edt · messages       │
│  Extensions: Talisman · Login · WTF      │
│              Limiter · SQLAlchemy · SocketIO │
└──────┬───────────────────┬──────────────┘
       │ SQL               │ Redis pub/sub
┌──────▼──────┐    ┌───────▼──────┐    ┌──────────────┐
│  MySQL 8.0   │    │   Redis 7    │    │  Jitsi Meet  │
│  :3306 int.  │    │  :6379 int.  │    │  (sous-dom.) │
└─────────────┘    └──────────────┘    └──────────────┘
```

### Cycle de vie d'une requête

```
Navigateur → Nginx (TLS :443) → Gunicorn :5000 → Flask Blueprint → RBAC → SQLAlchemy → MySQL
```

1. Le navigateur envoie une requête **HTTPS** sur le port 443
2. Nginx **termine la connexion TLS** et proxifie en HTTP interne vers Gunicorn (:5000, jamais exposé)
3. Gunicorn dispatche vers Flask qui applique les middlewares : **Talisman** (headers), **Flask-WTF** (CSRF), **Flask-Login** (session)
4. Le Blueprint activé vérifie le rôle via `@role_required` → **HTTP 403** si refus
5. La logique métier interroge MySQL via **SQLAlchemy ORM** (requêtes paramétrées uniquement)
6. Réponse : HTML via **Jinja2** ou JSON pour les appels API (FullCalendar, Chart.js)

---

## 🛠️ Stack technique

| Couche | Technologie | Rôle |
|---|---|---|
| **Back-end** | Python 3.12 + Flask 3.x | Framework principal, API REST, vues Jinja2 |
| **Serveur WSGI** | Gunicorn (eventlet) | 4 workers, compatible Flask-SocketIO |
| **Base de données** | MySQL 8.0 | SGBD relationnel, accès via SQLAlchemy ORM |
| **Cache / Broker** | Redis 7 | Broker SocketIO multi-workers, stockage rate limits |
| **Reverse proxy** | Nginx 1.24 | TLS, rate limiting, static files, proxy |
| **Certificat TLS** | Certbot / Let's Encrypt | Renouvellement automatique |
| **Conteneurisation** | Docker + Docker Compose | Orchestration des 4 services |
| **Auth & Sessions** | Flask-Login + Flask-WTF | Sessions serveur, tokens CSRF |
| **Hachage MDP** | Flask-Bcrypt (cost 12) | Stockage sécurisé des mots de passe |
| **Headers HTTP** | Flask-Talisman | CSP, HSTS, X-Frame-Options, X-Content-Type |
| **Rate limiting** | Flask-Limiter | Anti brute-force (5 req/min sur /login) |
| **Validation** | WTForms + marshmallow | Double validation front (HTML5) + back (Python) |
| **WebSockets** | Flask-SocketIO + Socket.IO JS | Messagerie temps réel, notifications |
| **Calendrier** | FullCalendar.js 6.x | Affichage EDT via API JSON Flask |
| **Graphiques** | Chart.js 4.x | Statistiques absences et moyennes |
| **Visio** | Jitsi Meet self-hosted | Salles de classe, auth par token JWT (HS256) |
| **CI/CD** | GitHub Actions | Pipeline automatisée (lint → SAST → DAST → deploy) |
| **SAST** | SonarLint CLI | Analyse statique du code source |
| **DAST** | OWASP ZAP | Scan dynamique de l'app déployée |
| **Audit dépendances** | pip-audit / safety | Scan CVE des packages Python |

---

## 📁 Structure du projet

```
Skaolink/
├── backend/
│   ├── app.py                  # Application Flask principale (blueprints, extensions)
│   ├── Dockerfile              # Image Flask + Gunicorn
│   ├── requirements.txt        # Dépendances Python
│   └── templates/              # Templates Jinja2
│       ├── base.html           # Layout principal (sidebar, navbar)
│       ├── login.html          # Page de connexion
│       ├── admin_dashboard.html
│       ├── admin_classes.html
│       ├── admin_users.html
│       ├── prof.html           # Dashboard professeur
│       ├── prof_classes.html
│       ├── prof_classe_detail.html
│       ├── prof_edt.html
│       ├── prof_devoirs.html
│       ├── prof_student_stats.html
│       ├── prof_dm_*.html      # Messagerie professeur
│       ├── etudiant.html       # Dashboard étudiant
│       ├── notes.html
│       ├── absences.html
│       ├── edt.html
│       ├── agenda.html
│       ├── devoirs.html
│       ├── messages.html       # Messagerie DM (WebSocket)
│       ├── dm_*.html
│       ├── resultat.html
│       └── settings.html
├── nginx/
│   ├── nginx.conf              # Config reverse proxy, TLS, rate limiting
│   └── certs/
│       ├── skaolink.crt        # Certificat TLS (dev auto-signé / prod Let's Encrypt)
│       └── skaolink.key
├── zap_reports/                # Rapports OWASP ZAP (DAST)
├── zap.yaml                    # Config OWASP ZAP headless
├── docker-compose.yml          # Orchestration des services Docker
├── LICENSE
└── README.md
```

---

## 🚀 Installation & déploiement

> Ce guide couvre le déploiement complet sur une **VM Ubuntu 22.04 LTS** (VPS OVH, Hetzner, DigitalOcean…). C'est l'environnement cible du projet.

### Prérequis

- Un VPS Ubuntu 22.04 LTS accessible en SSH
- Un nom de domaine pointant vers l'IP de la VM (enregistrement DNS type A) — requis pour le certificat TLS
- Git installé sur votre machine locale

---

### Étape 1 — Préparer la VM

Connexion en SSH, puis mise à jour du système :

```bash
ssh user@<IP_VM>

sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw
```

---

### Étape 2 — Configurer le pare-feu (UFW)

Autoriser uniquement SSH, HTTP et HTTPS. Bloquer tout le reste.

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

> ⚠️ Toujours autoriser `OpenSSH` **avant** `ufw enable`, sinon vous perdez l'accès SSH.

---

### Étape 3 — Installer Docker & Docker Compose

```bash
# Installation via le script officiel Docker
curl -fsSL https://get.docker.com | sudo sh

# Ajouter votre utilisateur au groupe docker (évite sudo à chaque commande)
sudo usermod -aG docker $USER
newgrp docker

# Vérification
docker --version
docker compose version
```

---

### Étape 4 — Cloner le dépôt

```bash
cd /opt
sudo git clone https://github.com/alt-then-F4/Skaolink.git
sudo chown -R $USER:$USER /opt/Skaolink
cd /opt/Skaolink
```

---

### Étape 5 — Configurer les variables d'environnement

```bash
nano .env
```

Contenu du fichier `.env` :

```env
FLASK_SECRET_KEY=une_cle_secrete_longue_et_aleatoire
MYSQL_PASSWORD=mot_de_passe_mysql
MYSQL_ROOT_PASSWORD=mot_de_passe_root_mysql
REDIS_PASSWORD=mot_de_passe_redis
```

> 💡 Générer une `SECRET_KEY` solide : `python3 -c "import secrets; print(secrets.token_hex(32))"`

> ⚠️ Le fichier `.env` est dans `.gitignore`. Ne jamais le commiter.

---

### Étape 6 — Lancer l'application

```bash
cd /opt/Skaolink
docker compose up -d --build
```

Vérifier que les 4 conteneurs sont bien démarrés :

```bash
docker compose ps
```

```
NAME             STATUS
skaolink-nginx   Up
skaolink-flask   Up
skaolink-mysql   Up
skaolink-redis   Up
```

| Service | Port exposé | Port interne |
|---|---|---|
| `nginx` | `:80`, `:443` | `:80`, `:443` |
| `flask_app` | ❌ aucun | `:5000` |
| `mysql_db` | ❌ aucun | `:3306` |
| `redis_broker` | ❌ aucun | `:6379` |

L'application est accessible sur **<addresse ip de la vm>**.
Mais avant il faudra se rendre sur ce site **<https://<adresse ip de la vm>/init-db>**

---

### Étape 7 — Consulter les logs

```bash
# Tous les services en direct
docker compose logs -f

# Un service en particulier
docker compose logs -f flask_app
docker compose logs -f nginx
```

---

### Étape 8 — Mettre à jour l'application

Pour déployer une nouvelle version depuis GitHub :

```bash
cd /opt/Skaolink
git pull origin main
docker compose up -d --build
```

---

### Commandes utiles

```bash
# Démarrer
docker compose up -d --build

# Arrêter
docker compose down

# Redémarrer un service
docker compose restart flask

# Voir les logs en direct
docker compose logs -f

# Statut des conteneurs
docker compose ps

# Accéder au shell MySQL
docker compose exec mysql_db mysql -u root -p
```

---

## 👥 Rôles & RBAC

Le RBAC est implémenté **exclusivement côté serveur** via des décorateurs Python (`@login_required`, `@role_required`). Toute tentative d'accès non autorisé retourne **HTTP 403** et est journalisée.

### Flux d'authentification

```
[1] Accès à https://skaolink.fr → redirect /login
[2] Saisie email + mot de passe (formulaire CSRF-protégé)
[3] Vérification bcrypt
    ├─ Échec  → flash "Identifiants invalides" (bloqué après 5 tentatives/min)
    └─ Succès → session Flask-Login créée
[4] Lecture du rôle (colonne `role` de la table users)
    ├─ [ETUDIANT] → /etudiant/dashboard
    ├─ [PROF]     → /prof/dashboard
    └─ [ADMIN]    → /admin/dashboard
[5] Déconnexion → session détruite → redirect /login
```

### Permissions par rôle

| Rôle | Permissions | Restrictions |
|---|---|---|
| 🔑 **Admin** | Créer/modifier classes, créer tous les comptes, gérer élèves, accès total back-office | — |
| 👨‍🏫 **Professeur** | Consulter ses classes, saisir notes et absences, créer devoirs, voir son EDT | Ses classes assignées uniquement |
| 🎓 **Étudiant** | Consulter ses notes, son EDT, ses absences, son agenda, messagerie | Données personnelles uniquement |

### Garanties d'isolation de session

- Cookie de session : `HttpOnly` + `SameSite=Lax` — inaccessible depuis JavaScript
- Toutes les requêtes SQL filtrent sur `current_user.id` — impossible de récupérer les données d'un autre utilisateur en manipulant l'URL
- Un étudiant accédant à `/prof/` reçoit **HTTP 403** — aucune donnée exposée

---

## 🔒 Sécurité

| Exigence OWASP | Mécanisme | Vérifié par |
|---|---|---|
| Mots de passe hachés | bcrypt (cost factor 12) | pip-audit + revue code |
| Brute-force login | Flask-Limiter (5 req/min sur `/login`) | OWASP ZAP + tests |
| Protection CSRF | Flask-WTF (tokens sur tous les formulaires) | OWASP ZAP |
| Validation des entrées | WTForms + HTML5 (front + back) | Tests unitaires |
| Injection SQL | SQLAlchemy ORM — requêtes paramétrées uniquement | SonarLint |
| Headers HTTP sécurité | Flask-Talisman (CSP, HSTS, X-Frame-Options…) | ZAP headers check |
| Sessions sécurisées | Flask-Login (HttpOnly, SameSite) | Tests manipulation session |
| Isolation RBAC | Décorateurs `@role_required` sur chaque route protégée | Tests RBAC croisés |
| Sécurité WebSocket | Flask-SocketIO + auth namespace | Tests non-authentifié |
| Visio JWT *(bonus)* | Token JWT HS256 signé par Flask pour Jitsi | Revue code |

---

## ⚙️ Pipeline CI/CD

La pipeline GitHub Actions se déclenche à chaque push sur `main`. Les étapes sont **séquentielles** — un échec bloque les suivantes.

```
push → main
    │
    ├─ 01 · Lint & Style    → Flake8 + Black
    ├─ 02 · SAST            → SonarLint CLI
    ├─ 03 · Audit dépendances → pip-audit / safety
    ├─ 04 · Build Docker    → Docker Buildx
    ├─ 05 · Deploy staging  → Docker Compose (env de test)
    ├─ 06 · DAST            → OWASP ZAP headless
    └─ 07 · Deploy prod     → SSH + Docker Compose (VM Ubuntu)
```

Les secrets de déploiement (`SECRET_KEY`, `DB_PASSWORD`, `REDIS_PASSWORD`, `JITSI_SECRET`) sont stockés dans **GitHub Secrets** et injectés au moment du déploiement.

---

## 👨‍💻 Contributeurs

Projet réalisé en groupe de 4 dans le cadre du module **GCS2-UE7-2 DevSecOps**.

---

<div align="center">

*GCS2-UE7-2 DevSecOps · Stack Technique v2.1 · Mars 2026*

</div>
