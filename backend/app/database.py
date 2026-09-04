from pymongo import MongoClient

from app.config import settings


client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
db = client[settings.mongodb_database]

payments_collection = db["payments"]
recoveries_collection = db["recoveries"]
receivables_collection = db["receivables"]
audit_collection = db["audit_events"]
batch_runs_collection = db["batch_runs"]

payments_collection.create_index("payment_id", unique=True)
recoveries_collection.create_index("recovery_id", unique=True)
recoveries_collection.create_index("payment_id", unique=True)
recoveries_collection.create_index("payment_link_id", sparse=True)

receivables_collection.create_index("invoice_id", unique=True)
receivables_collection.create_index("status")
receivables_collection.create_index("customer_id")

audit_collection.create_index([("entity_type", 1), ("entity_id", 1)])
audit_collection.create_index("timestamp")

batch_runs_collection.create_index("batch_id", unique=True)
batch_runs_collection.create_index("started_at")
