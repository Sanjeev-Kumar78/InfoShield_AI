import csv
import os
import uuid
from datetime import datetime


class DBManager:
    def __init__(self, db_path="data/pending_verifications.csv"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["session_id", "timestamp", "query",
                                "location", "urgency", "credibility", "status"])

    def add_pending_verification(self, query, location, urgency, credibility):
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        with open(self.db_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([session_id, timestamp, query,
                            location, urgency, credibility, "PENDING"])

        return session_id

    def get_pending(self):
        items = []
        with open(self.db_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['status'] == 'PENDING':
                    items.append(row)
        return items
