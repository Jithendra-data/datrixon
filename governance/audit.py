"""Local build evidence; deliberately excludes record values, questions and secrets."""
from datetime import datetime, timezone
import json


class AuditLog:
    def __init__(self, path, run_id):
        self.path = path
        self.run_id = run_id
        self.events = []

    def record(self, event, status='PASS', asset='pipeline'):
        row = dict(event_id=f'{self.run_id}:{len(self.events)+1}', run_id=self.run_id,
                   timestamp=datetime.now(timezone.utc).isoformat(), event=event, status=status, asset=asset)
        self.events.append(row)
        with self.path.open('a', encoding='utf-8') as stream: stream.write(json.dumps(row) + '\n')
        return row
