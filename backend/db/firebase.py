import os
import json
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

logger = logging.getLogger("cardiorecourse.firebase")

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
    def __init__(self, collection: "InMemoryCollectionReference", doc_id: str):
        self.id = doc_id
        self._collection = collection
        self._subcollections: Dict[str, "InMemoryCollectionReference"] = {}

    def get(self) -> InMemoryDocumentSnapshot:
        data = self._collection._docs.get(self.id)
        return InMemoryDocumentSnapshot(self.id, data)

    def set(self, data: Dict[str, Any], merge: bool = False):
        if merge and self.id in self._collection._docs:
            self._collection._docs[self.id].update(data)
        else:
            self._collection._docs[self.id] = dict(data)
        return True

    def update(self, data: Dict[str, Any]):
        if self.id not in self._collection._docs:
            raise KeyError(f"Document {self.id} does not exist")
        self._collection._docs[self.id].update(data)
        return True

    def collection(self, name: str) -> "InMemoryCollectionReference":
        if name not in self._subcollections:
            self._subcollections[name] = InMemoryCollectionReference(name)
        return self._subcollections[name]


class InMemoryCollectionReference:
    def __init__(self, name: str):
        self.name = name
        self._docs: Dict[str, Dict[str, Any]] = {}
        self._doc_refs: Dict[str, InMemoryDocumentReference] = {}

    def document(self, doc_id: Optional[str] = None) -> InMemoryDocumentReference:
        if not doc_id:
            import uuid
            doc_id = str(uuid.uuid4())
        if doc_id not in self._doc_refs:
            self._doc_refs[doc_id] = InMemoryDocumentReference(self, doc_id)
        return self._doc_refs[doc_id]

    def where(self, field: str, op: str, value: Any) -> InMemoryQuery:
        return InMemoryQuery(self, [(field, op, value)])

    def stream(self):
        for doc_id, data in self._docs.items():
            yield InMemoryDocumentSnapshot(doc_id, data)


class InMemoryFirestoreClient:
    def __init__(self):
        self._collections: Dict[str, InMemoryCollectionReference] = {}

    def collection(self, name: str) -> InMemoryCollectionReference:
        if name not in self._collections:
            self._collections[name] = InMemoryCollectionReference(name)
        return self._collections[name]


def get_firestore_client():
    """
    Initializes and returns the Firestore client.
    Attempts to initialize live Firebase Admin SDK with credentials.
    Falls back gracefully to an in-memory client if credentials are not configured,
    allowing 100% offline development, testing, and CI/CD validation.
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
            logger.warning(f"Could not initialize live Firebase Firestore: {e}. Falling back to in-memory store.")

    # Fallback in-memory client
    logger.info("Using in-memory Firestore client (Offline / Testing mode).")
    _firestore_client = InMemoryFirestoreClient()
    _is_mock_client = True
    return _firestore_client


def is_mock_store() -> bool:
    return _is_mock_client
