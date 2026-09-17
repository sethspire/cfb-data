# College Football Data Platform

An AWS-based data engineering platform for ingesting, validating, correcting, and analyzing historical college football data.

The project is designed around a **medallion data architecture** that preserves immutable source data while producing validated, reproducible datasets for analytics and predictive modeling.

## Architecture

External APIs / Data Sources  
**↓**  
Bronze: Immutable Raw JSON  
**↓**  
Validation + Transformation  **→**  Quarantine (Invalid Rows)  **→**  Corrections  **→**  Reprocess  **⟲**  
**↓**  
Silver: Validated Parquet  
**↓**  
Gold: Analytics / Features  


## Design Goals

The pipeline is built around several data-engineering principles:

- preserve the original source data
- never silently discard invalid records
- make corrections reproducible and auditable
- separate ingestion from analytical datasets
- allow failed records to be corrected and replayed
- support efficient historical queries and downstream modeling

## Bronze Layer

Raw API responses are stored unchanged in Amazon S3 with ingestion metadata and Hive-style partitioning.

Example:

`bronze/source=cfbdata/entity=games/ingest_date=2026-09-01/`

This provides an immutable record of the data received from each upstream source.

## Validation and Quarantine

Records are validated before entering canonical datasets.

Invalid records are written to a quarantine layer containing:

- the problematic record
- validation errors
- ingestion metadata
- relevant pipeline context

This prevents malformed data from contaminating downstream datasets while preserving enough information for debugging and recovery.

## Silver Layer

Validated data is standardized and stored as partitioned Parquet.

Processing includes:

- schema validation
- type normalization
- deduplication
- entity normalization
- timestamp standardization
- approved corrections

The resulting datasets are optimized for analytical querying through tools such as Amazon Athena.

## Reproducible Corrections

Known source-data issues are stored independently rather than modifying the original Bronze data.

Approved corrections can then be applied when quarantined records are reprocessed, providing an auditable and reproducible approach to data cleaning.

## Gold Layer

The Gold layer is being designed for derived analytical datasets such as:

- EPA and efficiency metrics
- opponent-adjusted ratings
- rolling statistics
- model features
- dashboards and APIs

## Technologies

Python · Pandas · Pandera · PyArrow/Parquet · pytest · AWS S3 · Athena · Chalice · REST APIs
