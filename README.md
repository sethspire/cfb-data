# College Football Data ETL+Analytics Pipeline

## Overview
This project serves as an implementation of a production analytics pipeline for College Football data. It will be hosted fully in AWS allowing for scheduled jobs for ETL processes as well as constantly updating analytics.

## ETL
The project uses a medallion-style data lake architecture built on AWS S3. Data progresses through multiple layers as it becomes more refined, validated, and analytics-ready.

### *Bronze Layer (Raw Data)*

The Bronze layer stores immutable raw source data exactly as received from upstream APIs and external datasets.Data is partitioned in S3 using Hive-style paths:

`bronze/source=cfbdata/entity=games/ingest_date=2026-09-01/`

Raw payloads are stored primarily as JSON files with ingestion metadata and timestamps.

### *Quarantine Layer*

Records that fail validation or transformation rules are written to a quarantine layer rather than discarded. This ensures:
- no silent data loss
- auditability
- reproducible debugging
- replayable pipeline recovery

Quarantined records contain:

raw/transformed row data
validation errors
ingestion metadata
pipeline context

### *Silver Layer (Validated Canonical Data)*

The Silver layer contains cleaned, standardized, and validated datasets derived from Bronze data.

Typical processing includes:

- schema validation
- type normalization
- deduplication
- entity normalization
- timestamp standardization

Silver datasets are stored as partitioned Parquet files in S3 for efficient analytical querying.

Example structure:

`silver/entity=plays/season=2026/week=7/`

Parquet + Hive-style partitioning enables:

- efficient Athena queries
- partition pruning
- columnar compression
- scalable historical analytics

### *Gold Layer (Analytics & Feature Data)*

The Gold layer contains curated analytical datasets and derived metrics used for:

- statistical analysis
- feature engineering
- predictive modeling
- dashboards and APIs

Gold datasets are reproducible and regenerated from Silver data whenever:

- source data changes
- validation rules change
- new metrics/features are introduced

Examples:

- EPA metrics
- opponent-adjusted efficiencies
- team ratings
- rolling statistics
- model feature sets

## Deployment

1. update the following values:
    - **/ingestion/cfbd_ingest/.chalice/config-ex.json**:
        - rename file to **config.json**
        - update `BRONZE_BUCKET` to the name of your S3 bucket
        - update `CFBD_API_KEY` to your CollegeFootballDatabase.com API key