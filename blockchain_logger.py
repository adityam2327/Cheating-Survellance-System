import hashlib
import json
import time
import os
import threading
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64
import uuid
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CheatingEvent:
    event_id: str
    timestamp: float
    event_type: str
    severity: str
    description: str
    confidence_score: float
    screenshot_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    def __post_init__(self):
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())

@dataclass
class Block:
    index: int
    timestamp: float
    events: List[CheatingEvent]
    previous_hash: str
    merkle_root: str
    nonce: int = 0
    def calculate_hash(self) -> str:
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'events': [asdict(event) for event in self.events],
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'nonce': self.nonce
        }, sort_keys=True, default=str)
        return hashlib.sha256(block_string.encode()).hexdigest()

class MerkleTree:
    def __init__(self, events: List[CheatingEvent]):
        self.events = events
        self.root = self._build_tree()
    def _build_tree(self) -> str:
        if not self.events:
            return hashlib.sha256("empty".encode()).hexdigest()
        event_hashes = [self._hash_event(event) for event in self.events]
        while len(event_hashes) > 1:
            if len(event_hashes) % 2 == 1:
                event_hashes.append(event_hashes[-1])
            new_level = []
            for i in range(0, len(event_hashes), 2):
                combined = event_hashes[i] + event_hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            event_hashes = new_level
        return event_hashes[0] if event_hashes else hashlib.sha256("empty".encode()).hexdigest()
    def _hash_event(self, event: CheatingEvent) -> str:
        event_string = json.dumps(asdict(event), sort_keys=True, default=str)
        return hashlib.sha256(event_string.encode()).hexdigest()

class BlockchainLogger:
    def __init__(self, db_path: str = "blockchain_logs.db", 
                 private_key_path: str = "private_key.pem",
                 public_key_path: str = "public_key.pem",
                 difficulty: int = 4):
        self.db_path = db_path
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self.difficulty = difficulty
        self.target = "0" * difficulty
        self._init_database()
        self._init_cryptographic_keys()
        self.chain = self._load_chain()
        self.pending_events = []
        self.lock = threading.RLock()
        self.metrics = {
            'total_events': 0,
            'total_blocks': 0,
            'average_mining_time': 0.0,
            'last_mining_time': 0.0
        }
        logger.info("Blockchain Logger initialized successfully")
    def _init_database(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS blocks (
                        block_index INTEGER PRIMARY KEY,
                        timestamp REAL,
                        previous_hash TEXT,
                        merkle_root TEXT,
                        nonce INTEGER,
                        hash TEXT UNIQUE,
                        signature TEXT)''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS events (
                        event_id TEXT PRIMARY KEY,
                        block_index INTEGER,
                        timestamp REAL,
                        event_type TEXT,
                        severity TEXT,
                        description TEXT,
                        confidence_score REAL,
                        screenshot_path TEXT,
                        metadata TEXT,
                        session_id TEXT,
                        user_id TEXT,
                        FOREIGN KEY (block_index) REFERENCES blocks (block_index))''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_severity ON events (severity)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_session ON events (session_id)')
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    def _init_cryptographic_keys(self):
        try:
            if os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path):
                with open(self.private_key_path, 'rb') as f:
                    self.private_key = serialization.load_pem_private_key(f.read(), password=None)
                with open(self.public_key_path, 'rb') as f:
                    self.public_key = serialization.load_pem_public_key(f.read())
                logger.info("Cryptographic keys loaded successfully")
            else:
                self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                self.public_key = self.private_key.public_key()
                with open(self.private_key_path, 'wb') as f:
                    f.write(self.private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()))
                with open(self.public_key_path, 'wb') as f:
                    f.write(self.public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo))
                logger.info("New cryptographic keys generated and saved")
        except Exception as e:
            logger.error(f"Cryptographic key initialization failed: {e}")
            raise
    def _load_chain(self) -> List[Block]:
        chain = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT block_index, timestamp, previous_hash, merkle_root, nonce, hash FROM blocks ORDER BY block_index')
                blocks_data = cursor.fetchall()
                for block_data in blocks_data:
                    index, timestamp, previous_hash, merkle_root, nonce, block_hash = block_data
                    cursor.execute('SELECT * FROM events WHERE block_index = ? ORDER BY timestamp', (index,))
                    events_data = cursor.fetchall()
                    events = []
                    for event_data in events_data:
                        event = CheatingEvent(
                            event_id=event_data[0],
                            timestamp=event_data[2],
                            event_type=event_data[3],
                            severity=event_data[4],
                            description=event_data[5],
                            confidence_score=event_data[6],
                            screenshot_path=event_data[7],
                            metadata=json.loads(event_data[8]) if event_data[8] else {},
                            session_id=event_data[9],
                            user_id=event_data[10]
                        )
                        events.append(event)
                    block = Block(
                        index=index,
                        timestamp=timestamp,
                        events=events,
                        previous_hash=previous_hash,
                        merkle_root=merkle_root,
                        nonce=nonce
                    )
                    chain.append(block)
                logger.info(f"Loaded {len(chain)} blocks from database")
                return chain
        except Exception as e:
            logger.error(f"Failed to load chain from database: {e}")
            return []
    def log_event(self, event: CheatingEvent) -> bool:
        with self.lock:
            try:
                self.pending_events.append(event)
                self.metrics['total_events'] += 1
                if len(self.pending_events) >= 10:
                    self._mine_block()
                logger.info(f"Event logged: {event.event_type} - {event.description}")
                return True
            except Exception as e:
                logger.error(f"Failed to log event: {e}")
                return False
    def _mine_block(self):
        if not self.pending_events:
            return None
        start_time = time.time()
        merkle_tree = MerkleTree(self.pending_events)
        previous_hash = self.chain[-1].calculate_hash() if self.chain else "0" * 64
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            events=self.pending_events.copy(),
            previous_hash=previous_hash,
            merkle_root=merkle_tree.root
        )
        nonce = 0
        while True:
            new_block.nonce = nonce
            block_hash = new_block.calculate_hash()
            if block_hash.startswith(self.target):
                break
            nonce += 1
            if nonce > 1000000:
                logger.warning("Mining timeout reached, using current nonce")
                break
        block_data = json.dumps({
            'index': new_block.index,
            'timestamp': new_block.timestamp,
            'merkle_root': new_block.merkle_root,
            'previous_hash': new_block.previous_hash,
            'nonce': new_block.nonce
        }, sort_keys=True)
        signature = self.private_key.sign(
            block_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        self.chain.append(new_block)
        self._save_block_to_db(new_block, block_hash, base64.b64encode(signature).decode())
        self.pending_events.clear()
        mining_time = time.time() - start_time
        self.metrics['total_blocks'] += 1
        self.metrics['last_mining_time'] = mining_time
        self.metrics['average_mining_time'] = (
            (self.metrics['average_mining_time'] * (self.metrics['total_blocks'] - 1) + mining_time) 
            / self.metrics['total_blocks']
        )
        logger.info(f"Block {new_block.index} mined successfully in {mining_time:.2f}s")
        return new_block
    def _save_block_to_db(self, block: Block, block_hash: str, signature: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO blocks (block_index, timestamp, previous_hash, merkle_root, nonce, hash, signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''', (block.index, block.timestamp, block.previous_hash, 
                     block.merkle_root, block.nonce, block_hash, signature))
                for event in block.events:
                    cursor.execute('''INSERT INTO events (event_id, block_index, timestamp, event_type, severity, 
                                          description, confidence_score, screenshot_path, metadata, session_id, user_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (event.event_id, block.index, event.timestamp, event.event_type, 
                         event.severity, event.description, event.confidence_score, 
                         event.screenshot_path, json.dumps(event.metadata), 
                         event.session_id, event.user_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save block to database: {e}")
            raise
    def verify_chain(self) -> bool:
        try:
            for i in range(1, len(self.chain)):
                current_block = self.chain[i]
                previous_block = self.chain[i - 1]
                if current_block.previous_hash != previous_block.calculate_hash():
                    logger.error(f"Invalid previous hash at block {i}")
                    return False
                if not current_block.calculate_hash().startswith(self.target):
                    logger.error(f"Invalid proof-of-work at block {i}")
                    return False
                merkle_tree = MerkleTree(current_block.events)
                if current_block.merkle_root != merkle_tree.root:
                    logger.error(f"Invalid Merkle root at block {i}")
                    return False
            logger.info("Blockchain verification completed successfully")
            return True
        except Exception as e:
            logger.error(f"Blockchain verification failed: {e}")
            return False
    def get_events_by_type(self, event_type: str, limit: int = 100) -> List[CheatingEvent]:
        events = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if event_type == "all":
                    cursor.execute('SELECT * FROM events ORDER BY timestamp DESC LIMIT ?', (limit,))
                else:
                    cursor.execute('SELECT * FROM events WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?', (event_type, limit))
                for event_data in cursor.fetchall():
                    event = CheatingEvent(
                        event_id=event_data[0],
                        timestamp=event_data[2],
                        event_type=event_data[3],
                        severity=event_data[4],
                        description=event_data[5],
                        confidence_score=event_data[6],
                        screenshot_path=event_data[7],
                        metadata=json.loads(event_data[8]) if event_data[8] else {},
                        session_id=event_data[9],
                        user_id=event_data[10]
                    )
                    events.append(event)
        except Exception as e:
            logger.error(f"Failed to retrieve events by type: {e}")
        return events
    def get_events_by_severity(self, severity: str, limit: int = 100) -> List[CheatingEvent]:
        events = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM events WHERE severity = ? ORDER BY timestamp DESC LIMIT ?', (severity, limit))
                for event_data in cursor.fetchall():
                    event = CheatingEvent(
                        event_id=event_data[0],
                        timestamp=event_data[2],
                        event_type=event_data[3],
                        severity=event_data[4],
                        description=event_data[5],
                        confidence_score=event_data[6],
                        screenshot_path=event_data[7],
                        metadata=json.loads(event_data[8]) if event_data[8] else {},
                        session_id=event_data[9],
                        user_id=event_data[10]
                    )
                    events.append(event)
        except Exception as e:
            logger.error(f"Failed to retrieve events by severity: {e}")
        return events
    def get_statistics(self) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM events')
                total_events = cursor.fetchone()[0]
                cursor.execute('SELECT event_type, COUNT(*) FROM events GROUP BY event_type')
                events_by_type = dict(cursor.fetchall())
                cursor.execute('SELECT severity, COUNT(*) FROM events GROUP BY severity')
                events_by_severity = dict(cursor.fetchall())
                cursor.execute('SELECT COUNT(*) FROM events WHERE timestamp > ?', (time.time() - 86400,))
                recent_events = cursor.fetchone()[0]
                return {
                    'total_events': total_events,
                    'total_blocks': len(self.chain),
                    'events_by_type': events_by_type,
                    'events_by_severity': events_by_severity,
                    'recent_events_24h': recent_events,
                    'metrics': self.metrics,
                    'chain_verified': self.verify_chain()
                }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    def export_chain(self, filepath: str) -> bool:
        try:
            export_data = {
                'metadata': {
                    'export_timestamp': time.time(),
                    'total_blocks': len(self.chain),
                    'total_events': self.metrics['total_events'],
                    'difficulty': self.difficulty
                },
                'blocks': []
            }
            for block in self.chain:
                block_data = {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'previous_hash': block.previous_hash,
                    'merkle_root': block.merkle_root,
                    'nonce': block.nonce,
                    'hash': block.calculate_hash(),
                    'events': [asdict(event) for event in block.events]
                }
                export_data['blocks'].append(block_data)
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            logger.info(f"Blockchain exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export blockchain: {e}")
            return False
    def flush_pending_events(self):
        with self.lock:
            if self.pending_events:
                self._mine_block()
    def cleanup_old_screenshots(self, max_age_days: int = 30):
        try:
            cutoff_time = time.time() - (max_age_days * 86400)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT screenshot_path FROM events WHERE timestamp < ? AND screenshot_path IS NOT NULL', (cutoff_time,))
                old_screenshots = cursor.fetchall()
                for (screenshot_path,) in old_screenshots:
                    if screenshot_path and os.path.exists(screenshot_path):
                        try:
                            os.remove(screenshot_path)
                            logger.info(f"Removed old screenshot: {screenshot_path}")
                        except Exception as e:
                            logger.warning(f"Failed to remove screenshot {screenshot_path}: {e}")
            logger.info(f"Cleanup completed: {len(old_screenshots)} old screenshots processed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

blockchain_logger = None

def initialize_blockchain_logger(db_path: str = "blockchain_logs.db") -> BlockchainLogger:
    global blockchain_logger
    if blockchain_logger is None:
        blockchain_logger = BlockchainLogger(db_path)
    return blockchain_logger

def get_blockchain_logger() -> BlockchainLogger:
    if blockchain_logger is None:
        raise RuntimeError("Blockchain logger not initialized. Call initialize_blockchain_logger() first.")
    return blockchain_logger 