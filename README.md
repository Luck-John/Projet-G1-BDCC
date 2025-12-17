# Pipeline de données financières sur AWS

## Vue d’ensemble
Ce projet met en place un pipeline de données financières dans un Data Lake sur AWS, en privilégiant des services serverless pour l’élasticité, la traçabilité et le contrôle des coûts. Il couvre l’ingestion automatisée, la transformation, le catalogage, l’accès analytique et la gouvernance des accès, avec un accent sur la qualité des métadonnées et le principe du moindre privilège.

## Architecture globale
1. Code sur GitHub construit par AWS CodeBuild (CI/CD).
2. Image Docker déployée sur Amazon ECS/Fargate.
3. Planification via Amazon EventBridge (cron, exécution quotidienne à 16h NY).
4. Script Python (ETL) exécuté en conteneur, stockage des résultats sur Amazon S3.
5. Catalogage avec AWS Glue Crawler, requêtes via Amazon Athena.
6. Visualisation avec un dashboard Dash connecté à Athena.

## Zones du Data Lake (Amazon S3)
- `raw/` : données brutes, intégrité préservée.
- `curated/` : données nettoyées et optimisées en Parquet (compression, rapidité OLAP).

## Étapes du pipeline ETL
- **Ingestion** : scripts Python avec `yfinance` récupérant les données boursières via API, dépôt en zone `raw`.
- **Transformation** : tâche conteneurisée (ECS/Fargate) convertissant le brut en Parquet, dépôt en zone `curated`.
- **Catalogage** : AWS Glue Crawler infère le schéma des fichiers Parquet, stocke les métadonnées dans Glue Data Catalog ; partitionnement par exemple sur `data_date` pour limiter le scan.
- **Accès analytique** : Amazon Athena interroge S3 en SQL standard en s’appuyant sur le schéma Glue ; configuration d’un bucket S3 dédié aux résultats de requêtes.

## Orchestration
- Amazon EventBridge déclenche les tâches ECS selon une planification (cron).
- Exécution conteneurisée pour l’ETL, centralisant extraction, transformation et chargement.

## Validation et visualisation
- Requêtes SQL simples dans Athena pour valider bout en bout (schéma Glue + lisibilité S3).
- Correction des erreurs de métadonnées directement dans Glue si nécessaire (ex. doublons de colonnes).
- Dashboard Dash (Python) connectée à Athena/Glue pour la BI et l’analyse avancée.

## Choix AWS
AWS est retenu pour sa maturité Data Lake et l’intégration entre ECS, S3 et l’analytique serverless (Glue, Athena), avec un modèle pay-as-you-go et un contrôle fin du code ETL.

## Principales technologies
- CI/CD : AWS CodeBuild
- Exécution ETL : Amazon ECS/Fargate, Python (`yfinance`)
- Stockage : Amazon S3 (`raw/`, `curated/` en Parquet)
- Orchestration : Amazon EventBridge (cron)
- Catalogage : AWS Glue Crawler + Glue Data Catalog
- SQL serverless : Amazon Athena
- Visualisation : Dash (Python) connecté à Athena

## Liens
- Lien du dashboard : https://60bb60dc-ea8f-4949-9770-51ef6e176a97.plotly.app/
- Lien de la présentation Canva du pipeline : https://www.canva.com/design/DAG7oIHLEhI/W2LSULwzL3gBGUaz26eKTA/edit

# Auteurs
- Jean Luc BATABATI
- Paul BALAFAI
- Samba SOW
- Ahmadou NIASS
- Papa Amadou NIANG
