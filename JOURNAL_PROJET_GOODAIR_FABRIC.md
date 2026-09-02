# Journal de bord — Migration GoodAir vers Microsoft Fabric

> **Document vivant.** Mis à jour après chaque session de travail.
> Ne pas attendre la fin du projet pour le remplir : 10 minutes en fin de session valent mieux qu'une reconstitution de mémoire trois semaines plus tard.

---

## 1. Fiche d'identité du projet

| Champ | Valeur |
|---|---|
| **Projet** | GoodAir — Portage de la plateforme Big Data environnementale sur Microsoft Fabric |
| **Auteur** | Maou DIARRA |
| **Formation** | Mastère 1 SIN EID — EPSI Paris — RNCP36921 Expert en Ingénierie des Données |
| **Origine** | MSPR TPRE843 (Bloc 3) et TPRE845 (Bloc 5) — stack Airflow / MinIO / PostgreSQL / Django |
| **Objectif** | Reproduire et industrialiser la plateforme sur Fabric, puis viser la certification DP-700 |
| **Date de début** | 02/09/2026 |
| **Fin d'essai Fabric** | 31/10/2026 (capacité d'évaluation, région France Central) |
| **Dépôt Git** | `<à compléter — ex. github.com/<user>/goodair-fabric>` |
| **Workspace Fabric** | `<à compléter>` |

### Historique des versions du document

| Version | Date | Auteur | Modifications |
|---|---|---|---|
| 0.1 | 02/09/2026 | M. DIARRA | Création du squelette |
| | | | |

---

## 2. Contexte et objectifs

### 2.1 Point de départ

La plateforme GoodAir existe déjà en version auto-hébergée : collecte horaire des API AQICN et OpenWeatherMap pour 10 villes françaises, Data Lake MinIO en architecture médaillon, Data Warehouse PostgreSQL en schéma étoile, orchestration Apache Airflow, modèle RandomForest (R² = 0.9397) et dashboard Django/Leaflet.

### 2.2 Pourquoi migrer sur Fabric

*(à personnaliser — quelques pistes)*

- Monter en compétence sur la plateforme data Microsoft, très demandée sur le marché français
- Confronter une architecture auto-hébergée à son équivalent managé, et savoir argumenter les deux
- Couvrir le référentiel de l'examen DP-700 par la pratique plutôt que par le cours
- Produire un livrable démontrable en entretien : le même besoin métier, deux implémentations

### 2.3 Objectifs mesurables

| # | Objectif | Indicateur de réussite | Statut |
|---|---|---|---|
| O1 | Ingestion des 2 API vers OneLake | Fichiers bronze présents pour 10 villes | ⬜ À faire |
| O2 | Couches Silver et Gold en tables Delta | Tables interrogeables, pas de doublons | ⬜ À faire |
| O3 | Warehouse en schéma étoile | 5 tables + intégrité référentielle | ⬜ À faire |
| O4 | Orchestration horaire automatisée | Pipeline planifié, ≥ 20 runs consécutifs OK | ⬜ À faire |
| O5 | Contrôles qualité automatisés | Table `rapport_qualite` alimentée | ⬜ À faire |
| O6 | Brique temps réel | Eventstream + Eventhouse + requêtes KQL | ⬜ À faire |
| O7 | Modèle ML tracké | Expériences MLflow + modèle enregistré | ⬜ À faire |
| O8 | Restitution Power BI | Rapport Direct Lake avec carte | ⬜ À faire |
| O9 | CI/CD | Git connecté + déploiement DEV → PROD | ⬜ À faire |
| O10 | Certification | DP-700 passée | ⬜ À faire |

*Légende : ⬜ À faire · 🟡 En cours · ✅ Terminé · ⛔ Bloqué · ⏸️ Abandonné (justifier)*

---

## 3. Architecture cible et correspondance des briques

| Brique GoodAir (existant) | Équivalent Fabric | Statut portage | Commentaire |
|---|---|---|---|
| MinIO — buckets bronze/silver/gold | OneLake — Lakehouse `lh_goodair` | ⬜ | |
| `etl_aqicn.py`, `etl_openweather.py` | Notebook PySpark + pipeline Data Factory | ⬜ | |
| `bronze_to_silver.py` | Notebook PySpark → tables Delta | ⬜ | |
| `silver_to_gold.py` | Notebook PySpark → tables agrégées | ⬜ | |
| PostgreSQL — schéma étoile | Warehouse Fabric (T-SQL) | ⬜ | |
| DAG Airflow `@hourly` | Pipeline Data Factory planifié | ⬜ | |
| `data_quality.py` | Notebook + table `rapport_qualite` | ⬜ | |
| `model_aqi.joblib` (sklearn) | Notebook Data Science + MLflow | ⬜ | |
| Django + Leaflet | Power BI Direct Lake + visuel carte | ⬜ | |
| Fichier `.env` | Connexions Fabric / Azure Key Vault | ⬜ | |
| — (nouveau) | Eventstream + Eventhouse KQL | ⬜ | Brique absente de l'existant |

### Schéma d'architecture cible

> *Insérer ici le diagramme (draw.io, Excalidraw ou export Fabric). Conserver le fichier source dans `/docs/schemas/`.*

---

## 4. Journal de bord

> Une entrée par session de travail. Copier le bloc modèle ci-dessous.
> Règle : on note **ce qui a échoué autant que ce qui a marché**. Les erreurs résolues sont la partie la plus utile du document, en soutenance comme en entretien.

### Bloc modèle à copier

```
### Session NN — JJ/MM/AAAA — <titre court>

**Durée :** Xh
**Objectif de la session :** …

**Réalisé**
- …

**Difficultés rencontrées**
| Problème | Cause identifiée | Solution appliquée | Temps perdu |
|---|---|---|---|
| | | | |

**Décisions prises** *(reporter dans le registre §6 si structurante)*
- …

**Preuves** *(captures dans /docs/captures/ — nommage : sNN_description.png)*
- …

**Compétences DP-700 travaillées :** …

**Prochaine étape :** …
```

---

### Session 01 — 02/09/2026 — Mise en place de l'environnement

**Durée :** —
**Objectif de la session :** activer l'essai Fabric, créer le workspace, valider l'accès aux workloads.

**Réalisé**
- Activation de la version d'évaluation Fabric (60 jours, expire le 31/10/2026, région France Central)
- Création du workspace `<nom>`
- …

**Difficultés rencontrées**

| Problème | Cause identifiée | Solution appliquée | Temps perdu |
|---|---|---|---|
| Onglet « Power BI Premium » vide dans le portail d'administration | Les capacités Fabric sont sous « Capacité de l'infrastructure », pas Premium | Vérification via la création de workspace | 15 min |

**Décisions prises**
- …

**Preuves**
- …

**Compétences DP-700 travaillées :** Implémenter et gérer une solution d'analytique — configuration d'espace de travail

**Prochaine étape :** créer le Lakehouse et le premier notebook d'ingestion.

---

## 5. Suivi par lot de travail

### Lot 1 — Ingestion et couche Bronze

**Période cible :** semaines 1-2 · **Statut :** ⬜

- [ ] Lakehouse créé, arborescence `Files/` définie
- [ ] Notebook d'ingestion AQICN (10 villes) fonctionnel
- [ ] Notebook d'ingestion OpenWeatherMap fonctionnel
- [ ] Gestion des erreurs API (timeout, quota, statut ≠ ok) reprise de l'existant
- [ ] Clés API externalisées (pas de secret en dur dans le notebook)
- [ ] Même ingestion refaite en pipeline Data Factory (activité Web + ForEach)
- [ ] Convention de nommage des chemins documentée

**Notes techniques :**

**Écarts avec l'existant GoodAir :**

---

### Lot 2 — Silver, Gold et Warehouse

**Période cible :** semaines 3-4 · **Statut :** ⬜

- [ ] Tables Delta Silver créées (schéma explicite, pas d'inférence)
- [ ] Règles de validation portées (AQI 0-500, temp -30/+60, humidité 0-100, pression 900-1100)
- [ ] Champ `qualite` (OK/WARNING) et liste des anomalies conservés
- [ ] `MERGE` sur clé métier (ville + timestamp) pour l'idempotence des runs horaires
- [ ] Tables Gold : agrégats journaliers + dataset ML
- [ ] Warehouse créé, DDL du schéma étoile porté depuis PostgreSQL
- [ ] Contraintes et clés étrangères vérifiées
- [ ] Shortcut ou raccourci Lakehouse → Warehouse validé

**Notes techniques :**

**Écarts avec l'existant GoodAir :**

---

### Lot 3 — Orchestration et qualité

**Période cible :** semaine 5 · **Statut :** ⬜

- [ ] Pipeline enchaînant les notebooks (équivalent du DAG `goodair_pipeline`)
- [ ] Planification horaire active
- [ ] Retries configurés
- [ ] Notifications ou alertes en cas d'échec
- [ ] Table `rapport_qualite` alimentée à chaque run
- [ ] Supervision : au moins 20 runs consécutifs analysés

**Suivi des exécutions :**

| Date | Runs | Succès | Échecs | Durée moyenne | Incident |
|---|---|---|---|---|---|
| | | | | | |

---

### Lot 4 — Temps réel

**Période cible :** semaine 6 · **Statut :** ⬜

- [ ] Eventstream créé
- [ ] Eventhouse / base KQL alimentée
- [ ] 5 requêtes KQL représentatives écrites et commentées
- [ ] Comparaison écrite : KQL vs SQL analytique, quand utiliser quoi

**Notes techniques :**

---

### Lot 5 — Machine Learning

**Période cible :** semaine 7 · **Statut :** ⬜

- [ ] Dataset Gold consommé depuis le Lakehouse
- [ ] Modèle réentraîné (RandomForestRegressor, baseline R² = 0.9397 à retrouver ou dépasser)
- [ ] Expériences tracées avec MLflow
- [ ] Modèle enregistré dans le registre de modèles
- [ ] Comparaison d'au moins 2 algorithmes

**Résultats :**

| Run | Algorithme | Features | R² test | RMSE | Commentaire |
|---|---|---|---|---|---|
| | | | | | |

---

### Lot 6 — Restitution Power BI

**Période cible :** semaine 7 · **Statut :** ⬜

- [ ] Modèle sémantique en Direct Lake
- [ ] Mesures DAX principales (AQI moyen, min, max, nombre de mesures)
- [ ] Visuel carte par ville
- [ ] Historique temporel
- [ ] Comparaison avec le dashboard Django/Leaflet existant

**Notes techniques :**

---

### Lot 7 — CI/CD et gouvernance

**Période cible :** semaine 8 · **Statut :** ⬜

- [ ] Intégration Git activée sur le workspace
- [ ] Dépôt structuré et commits réguliers
- [ ] Workspace PROD créé
- [ ] Deployment pipeline DEV → PROD testé
- [ ] Rôles d'accès OneLake configurés
- [ ] Sensibilité / gouvernance : ce qui est faisable et ce qui ne l'est pas en essai

**Notes techniques :**

---

### Lot 8 — Certification DP-700

**Statut :** ⬜

| Domaine d'examen | Poids | Auto-évaluation /5 | Révisé le |
|---|---|---|---|
| Implémenter et gérer une solution d'analytique | ~1/3 | | |
| Ingérer et transformer les données | ~1/3 | | |
| Superviser et optimiser une solution d'analytique | ~1/3 | | |

- [ ] Parcours Microsoft Learn terminé
- [ ] Voucher gratuit demandé (Fabric Data Days)
- [ ] Examens blancs : score ≥ 80 %
- [ ] Date d'examen réservée : ______
- [ ] Résultat : ______

---

## 6. Registre des décisions techniques

> Une ligne par choix structurant. Ce registre est ce qui transforme un travail d'exécution en travail d'ingénierie : il montre que vous avez arbitré, pas seulement suivi un tutoriel.

| # | Date | Décision | Options écartées | Justification | Conséquences |
|---|---|---|---|---|---|
| D1 | 02/09/2026 | Portage sur Fabric plutôt que sur Databricks ou une stack Azure éclatée | Databricks, ADF + ADLS + Azure SQL | Couverture bout-en-bout sous une seule licence, alignement DP-700, essai gratuit disponible | Dépendance à l'écosystème Microsoft ; un mini-projet ADF « classique » sera mené en parallèle pour la couverture marché |
| D2 | | Format de stockage Delta plutôt que JSON/CSV | | | |
| D3 | | | | | |

---

## 7. Registre des incidents

| # | Date | Incident | Impact | Cause racine | Résolution | Prévention |
|---|---|---|---|---|---|---|
| I1 | | | | | | |

---

## 8. Suivi de la capacité et des coûts

| Date | Type de capacité | SKU | Coût | Remarque |
|---|---|---|---|---|
| 02/09/2026 | Version d'évaluation | Trial | 0 € | Expire le 31/10/2026 |
| | | | | |

**Plan de sortie d'essai** *(à décider avant le 15/10/2026)* :
- Option A — Capacité F2 payante sur Azure, mise en pause hors sessions de travail
- Option B — Export complet des livrables et arrêt de l'environnement
- Option C — Nouveau tenant via Microsoft 365 Developer Program

**Décision retenue :** ______ le ______

---

## 9. Couverture des compétences

### 9.1 Référentiel DP-700

| Compétence | Lot concerné | Preuve | Niveau /5 |
|---|---|---|---|
| Configurer un espace de travail | Lot 1 | | |
| Implémenter le contrôle de version | Lot 7 | | |
| Ingérer en batch | Lot 1 | | |
| Ingérer en streaming | Lot 4 | | |
| Transformer avec PySpark | Lot 2 | | |
| Transformer avec SQL | Lot 2 | | |
| Transformer avec KQL | Lot 4 | | |
| Orchestrer | Lot 3 | | |
| Sécuriser et gouverner | Lot 7 | | |
| Superviser et optimiser | Lot 3 | | |

### 9.2 Points faibles identifiés à combler en priorité

*(à partir du bulletin 2025-2026)*

| Sujet | Note | Lot du projet qui y répond | Statut |
|---|---|---|---|
| Streaming data architecture | 10/20 | Lot 4 | ⬜ |
| Administration / déploiement de pipelines | 10/20 | Lot 3 et 7 | ⬜ |
| Entrepôts de données (Datamart) | 8/20 | Lot 2 | ⬜ |
| Écosystème Hadoop | 0/20 | Lot 2 (équivalent Spark managé) | ⬜ |

---

## 10. Bilan comparatif (à rédiger en fin de projet)

### 10.1 Ce que Fabric apporte par rapport à la stack auto-hébergée

### 10.2 Ce que la stack auto-hébergée conserve comme avantages

### 10.3 Effort de migration réel

| Brique | Temps estimé | Temps réel | Écart | Cause |
|---|---|---|---|---|
| | | | | |

### 10.4 Ce que je referais différemment

---

## 11. Organisation du dépôt

```
goodair-fabric/
├── README.md                    # Vitrine : avant / après, schémas, résultats
├── JOURNAL_PROJET.md            # Ce document
├── docs/
│   ├── schemas/                 # Diagrammes source (draw.io, excalidraw)
│   └── captures/                # sNN_description.png
├── notebooks/
│   ├── 01_ingestion_aqicn.ipynb
│   ├── 02_ingestion_openweather.ipynb
│   ├── 03_bronze_to_silver.ipynb
│   ├── 04_silver_to_gold.ipynb
│   ├── 05_data_quality.ipynb
│   └── 06_ml_aqi.ipynb
├── warehouse/
│   └── ddl_schema_etoile.sql
├── pipelines/                   # Export JSON des pipelines Data Factory
├── kql/                         # Requêtes Eventhouse
└── legacy/                      # Renvoi vers le projet Airflow/MinIO d'origine
```

---

## 12. Annexes

### 12.1 Glossaire des termes Fabric

| Terme | Équivalent connu | Définition courte |
|---|---|---|
| OneLake | MinIO / S3 / HDFS | Lac de données unique du tenant, format Delta Parquet |
| Lakehouse | Data Lake + tables | Stockage fichiers + tables Delta interrogeables en SQL |
| Warehouse | PostgreSQL | Entrepôt relationnel T-SQL, écriture transactionnelle |
| Shortcut | Montage / lien symbolique | Référence vers des données externes sans copie |
| Mirroring | CDC | Réplication quasi temps réel d'une base opérationnelle |
| Direct Lake | — | Mode Power BI lisant directement les tables Delta, sans import ni requête SQL |
| Eventstream | Kafka / Event Hubs | Flux d'événements managé |
| Eventhouse | — | Base analytique temps réel interrogée en KQL |
| Capacité (SKU F) | Cluster | Unité de calcul mutualisée entre tous les workloads |

### 12.2 Ressources utilisées

| Ressource | Lien | Utilité |
|---|---|---|
| Microsoft Learn — parcours Fabric Data Engineer | | Référence principale |
| Documentation Fabric | | |
| | | |

### 12.3 Contacts et entraide

| Nom | Rôle | Sujet |
|---|---|---|
| | | |
