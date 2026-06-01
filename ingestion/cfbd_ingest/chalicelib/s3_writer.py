import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BronzeWriter:
    def __init__(self, bucket: str | None = None, local_root: str | None = None):
        if (bucket and local_root) or (not bucket and not local_root):
            raise ValueError("Specify either bucket or local_root, not both")
        self.bucket = bucket
        self.local_root = local_root
        self._s3 = None
        if bucket:
            import boto3
            self._s3 = boto3.client("s3")
            log.info("BronzeWriter targeting S3 bucket: %s", bucket)
        else:
            log.info("BronzeWriter targeting local: %s", local_root)

    def write_entity(
        self,
        entity: str,
        data: dict | list[dict],
        source: str = "cfbdata",
        params: dict | None = None,
        ingest_time: str | None = None,
    ) -> str:
        ingest_ts = ingest_time or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        ingest_date = ingest_ts[:10]

        record_count = len(data) if isinstance(data, list) else 1

        envelope = {
            "ingest_timestamp": ingest_ts,
            "source": source,
            "entity": entity,
            "params": params or {},
            "record_count": record_count,
            "payload": data,
        }

        partition = f"bronze/source={source}/entity={entity}/ingest_date={ingest_date}"

        suffix = uuid.uuid4().hex[:8]
        filename = f"{entity}_{ingest_ts}_{suffix}.json"
        key = f"{partition}/{filename}"

        body = json.dumps(envelope, indent=2, default=str)

        if self._s3:
            try:
                self._s3.put_object(Bucket=self.bucket, Key=key, Body=body)
            except Exception:
                log.exception("S3 write failed: %s/%s", partition, filename)
                raise
        else:
            local_path = Path(self.local_root or "./bronze_data") / key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(body)

        log.info("Wrote bronze %s/%s (%d records)", partition, filename, record_count)
        return key
