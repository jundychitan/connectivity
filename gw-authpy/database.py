import sqlite3
from typing import List, Dict

DATABASE_NAME = "gw-auth.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gateways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT NOT NULL,
            ssh_key TEXT NOT NULL UNIQUE,
            approved BOOLEAN DEFAULT FALSE,
            mac_address TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS port_forwarding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_port INTEGER NOT NULL UNIQUE,
            destination_port INTEGER NOT NULL UNIQUE
        )
    """)
    conn.commit()
    conn.close()

def add_gateway(hostname: str, ssh_key: str, mac_address: str, approved: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO gateways (hostname, ssh_key, approved, mac_address) VALUES (?, ?, ?, ?)",
        (hostname, ssh_key, approved, mac_address)
    )
    conn.commit()
    conn.close()

def get_gateway_by_id(gateway_id: int) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gateways WHERE id = ?", (gateway_id,))
    gateway = cursor.fetchone()
    conn.close()
    return dict(gateway) if gateway else None

def approve_gateway(gateway_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE gateways SET approved = 1 WHERE id = ?", (gateway_id,))
    conn.commit()
    conn.close()

def disapprove_gateway(gateway_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE gateways SET approved = 0 WHERE id = ?", (gateway_id,))
    conn.commit()
    conn.close()

def get_gateway_ssh_key(gateway_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ssh_key FROM gateways WHERE id = ?", (gateway_id,))
    row = cursor.fetchone()
    conn.close()
    
    return row["ssh_key"] if row else None

def get_all_gateways() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gateways")
    gateways = cursor.fetchall()
    conn.close()
    return [dict(gateway) for gateway in gateways]

def add_port_forwarding(origin_port: int, destination_port: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if either port already exists
    cursor.execute("""
        SELECT 1 FROM port_forwarding 
        WHERE origin_port = ? OR destination_port = ? 
           OR origin_port = ? OR destination_port = ?
    """, (origin_port, origin_port, destination_port, destination_port))
    exists = cursor.fetchone()
    
    if exists:
        conn.close()
        raise ValueError("One of the ports is already in use in port forwarding rules.")
    
    cursor.execute("""
        INSERT INTO port_forwarding (origin_port, destination_port)
        VALUES (?, ?)
    """, (origin_port, destination_port))
    
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return entry_id

def delete_port_forwarding(entry_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM port_forwarding WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

def get_all_port_forwardings() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM port_forwarding")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
