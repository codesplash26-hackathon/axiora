import os
import json
import logging
import threading
from typing import Any, Dict, Optional, List

logger = logging.getLogger("cardiorecourse.firebase")

LOCAL_DB_FILE = os.getenv("LOCAL_FIRESTORE_DB_FILE", os.path.join("data", "local_firestore_db.json"))
_db_lock = threading.Lock()

_firestore_client = None
_is_mock_client = False


class InMemoryDocumentSnapshot:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        if self._data is None:
            return None
        return dict(self._data)


class InMemoryQuery:
    def __init__(self, collection: "InMemoryCollectionReference", filters: Optional[List[tuple]] = None):
        self._collection = collection
        self._filters = filters or []

    def where(self, field: str, op: str, value: Any) -> "InMemoryQuery":
        new_filters = list(self._filters)
        new_filters.append((field, op, value))
        return InMemoryQuery(self._collection, new_filters)

    def stream(self):
        for doc_id, data in self._collection._docs.items():
            matches = True
            for field, op, value in self._filters:
                doc_val = data.get(field)
                if op == "==":
                    if doc_val != value:
                        matches = False
                        break
                elif op == "!=":
                    if doc_val == value:
                        matches = False
                        break
                elif op == ">":
                    if doc_val is None or doc_val <= value:
                        matches = False
                        break
                elif op == "<":
                    if doc_val is None or doc_val >= value:
                        matches = False
                        break
            if matches:
                yield InMemoryDocumentSnapshot(doc_id, data)


class InMemoryDocumentReference:
    def __init__(self, collection: "InMemoryCollectionReference", doc_id: str, client: "InMemoryFirestoreClient"):
        self.id = doc_id
        self._collection = collection
        self._client = client
        self._subcollections: Dict[str, "InMemoryCollectionReference"] = {}

    def get(self) -> InMemoryDocumentSnapshot:
        data = self._collection._docs.get(self.id)
        return InMemoryDocumentSnapshot(self.id, data)

    def set(self, data: Dict[str, Any], merge: bool = False):
        if merge and self.id in self._collection._docs:
            self._collection._docs[self.id].update(data)
        else:
            self._collection._docs[self.id] = dict(data)
        self._client._save_to_disk()
        return True

    def update(self, data: Dict[str, Any]):
        if self.id not in self._collection._docs:
            raise KeyError(f"Document {self.id} does not exist")
        self._collection._docs[self.id].update(data)
        self._client._save_to_disk()
        return True

    def collection(self, name: str) -> "InMemoryCollectionReference":
        if name not in self._subcollections:
            self._subcollections[name] = InMemoryCollectionReference(name, client=self._client, parent_doc=self)
        return self._subcollections[name]


class InMemoryCollectionReference:
    def __init__(self, name: str, client: "InMemoryFirestoreClient", parent_doc: Optional[InMemoryDocumentReference] = None):
        self.name = name
        self._client = client
        self._parent_doc = parent_doc
        self._docs: Dict[str, Dict[str, Any]] = {}
        self._doc_refs: Dict[str, InMemoryDocumentReference] = {}

    def document(self, doc_id: Optional[str] = None) -> InMemoryDocumentReference:
        if not doc_id:
            import uuid
            doc_id = str(uuid.uuid4())
        if doc_id not in self._doc_refs:
            self._doc_refs[doc_id] = InMemoryDocumentReference(self, doc_id, client=self._client)
        return self._doc_refs[doc_id]

    def where(self, field: str, op: str, value: Any) -> InMemoryQuery:
        return InMemoryQuery(self, [(field, op, value)])

    def stream(self):
        for doc_id, data in self._docs.items():
            yield InMemoryDocumentSnapshot(doc_id, data)


class InMemoryFirestoreClient:
    def __init__(self, db_file: Optional[str] = None):
        self.db_file = db_file or LOCAL_DB_FILE
        self._collections: Dict[str, InMemoryCollectionReference] = {}
        self._load_from_disk()

    def collection(self, name: str) -> InMemoryCollectionReference:
        if name not in self._collections:
            self._collections[name] = InMemoryCollectionReference(name, client=self)
        return self._collections[name]

    def _load_from_disk(self):
        if not self.db_file or not os.path.exists(self.db_file):
            return
        try:
            with _db_lock:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

            for col_name, docs_dict in raw_data.items():
                col = self.collection(col_name)
                for doc_id, doc_record in docs_dict.items():
                    data = dict(doc_record)
                    subcols = data.pop("_subcollections", {})
                    col._docs[doc_id] = data
                    doc_ref = col.document(doc_id)
                    for sub_name, sub_docs_dict in subcols.items():
                        sub_col = doc_ref.collection(sub_name)
                        for sub_id, sub_data in sub_docs_dict.items():
                            sub_col._docs[sub_id] = dict(sub_data)
                            sub_col.document(sub_id)
            logger.info(f"Loaded persistent local database from {self.db_file}")
        except Exception as e:
            logger.warning(f"Failed to load local database from {self.db_file}: {e}")

    def _save_to_disk(self):
        if not self.db_file:
            return
        try:
            with _db_lock:
                serialized: Dict[str, Any] = {}
                for col_name, col in self._collections.items():
                    serialized[col_name] = {}
                    for doc_id, data in col._docs.items():
                        doc_dict = dict(data)
                        doc_ref = col._doc_refs.get(doc_id)
                        if doc_ref and doc_ref._subcollections:
                            sub_dict: Dict[str, Any] = {}
                            for sub_name, sub_col in doc_ref._subcollections.items():
                                sub_dict[sub_name] = dict(sub_col._docs)
                            doc_dict["_subcollections"] = sub_dict
                        serialized[col_name][doc_id] = doc_dict

                dir_name = os.path.dirname(self.db_file)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)

                temp_file = f"{self.db_file}.tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(serialized, f, indent=2)

                if os.path.exists(self.db_file):
                    os.replace(temp_file, self.db_file)
                else:
                    os.rename(temp_file, self.db_file)
        except Exception as e:
            logger.error(f"Error persisting database to disk: {e}")


def get_firestore_client():
    """
    Initializes and returns the Firestore client.
    Attempts to initialize live Firebase Admin SDK with credentials.
    Falls back gracefully to a disk-persistent local client if cloud credentials are not configured,
    ensuring that patient and assessment data persists safely across server restarts.
    """
    global _firestore_client, _is_mock_client
    if _firestore_client is not None:
        return _firestore_client

    force_mock = os.getenv("MOCK_FIREBASE", "false").lower() in ("true", "1", "yes")
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if not force_mock and (os.path.exists(cred_path) or cred_json):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                if cred_json:
                    cred_dict = json.loads(cred_json)
                    cred = credentials.Certificate(cred_dict)
                else:
                    cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)

            _firestore_client = firestore.client()
            _is_mock_client = False
            logger.info("Successfully connected to Google Cloud Firestore.")
            return _firestore_client
        except Exception as e:
            logger.warning(f"Could not initialize live Firebase Firestore: {e}. Falling back to persistent local store.")

    logger.info("Using persistent local Firestore client on disk.")
    _firestore_client = InMemoryFirestoreClient()
    _is_mock_client = True
    return _firestore_client


def is_mock_store() -> bool:
    return _is_mock_client
