"""Memory storage for ai-shell."""

import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


class MemoryStore:
    """
    Hybrid memory: in-memory for session, SQLite for persistence.

    Manages:
    - Conversation history (in-memory)
    - Session variables ($last, $summary, etc.)
    - Command history (persistent)
    - Saved sessions (persistent)
    """

    def __init__(self, db_path: str = None):
        """
        Initialize memory store.

        Args:
            db_path: Path to SQLite database (default: ~/.ai_shell/history.db)
        """
        # In-memory state
        self.conversation_history: List[Dict] = []
        self.variables: Dict[str, any] = {}
        self.current_session_id = datetime.now().isoformat()

        # Persistent storage
        if db_path is None:
            db_path = os.path.expanduser("~/.ai_shell/history.db")

        self.db_path = db_path

        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Command history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                command TEXT NOT NULL,
                output TEXT,
                session_id TEXT
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                state TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def add_message(self, role: str, content: str):
        """
        Add message to conversation history.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def add_command(self, command: str, output: str = None):
        """
        Add command to persistent history.

        Args:
            command: Command that was executed
            output: Command output (optional)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO history (timestamp, command, output, session_id)
            VALUES (?, ?, ?, ?)
        """, (datetime.now().isoformat(), command, output, self.current_session_id))

        conn.commit()
        conn.close()

    def get_recent_history(self, n: int = 10) -> List[Dict]:
        """
        Get recent conversation messages.

        Args:
            n: Number of messages to retrieve

        Returns:
            List of recent messages
        """
        return self.conversation_history[-n:]

    def search_history(self, query: str, limit: int = 10) -> List[str]:
        """
        Search command history.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching commands
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT command, timestamp FROM history
            WHERE command LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"%{query}%", limit))

        results = cursor.fetchall()
        conn.close()

        return [row[0] for row in results]

    def get_all_commands(self, limit: int = 100) -> List[Dict]:
        """
        Get all commands from history.

        Args:
            limit: Maximum number of commands

        Returns:
            List of command dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, timestamp, command, output FROM history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        results = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "command": row[2],
                "output": row[3]
            }
            for row in results
        ]

    def set_variable(self, name: str, value: any):
        """
        Set session variable ($last, $summary, etc.).

        Args:
            name: Variable name (e.g., "$last")
            value: Variable value
        """
        self.variables[name] = value

    def get_variable(self, name: str) -> Optional[any]:
        """
        Get session variable.

        Args:
            name: Variable name

        Returns:
            Variable value or None
        """
        return self.variables.get(name)

    def save_session(self):
        """Save current session state to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        state = {
            "conversation_history": self.conversation_history,
            "variables": self.variables
        }

        cursor.execute("""
            INSERT OR REPLACE INTO sessions (session_id, timestamp, state)
            VALUES (?, ?, ?)
        """, (self.current_session_id, datetime.now().isoformat(), json.dumps(state)))

        conn.commit()
        conn.close()

    def load_session(self, session_id: str):
        """
        Load saved session.

        Args:
            session_id: Session ID to load
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT state FROM sessions WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            state = json.loads(row[0])
            self.conversation_history = state.get("conversation_history", [])
            self.variables = state.get("variables", {})
            self.current_session_id = session_id

    def list_sessions(self) -> List[Dict]:
        """
        List all saved sessions.

        Returns:
            List of session metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id, timestamp FROM sessions
            ORDER BY timestamp DESC
        """)

        results = cursor.fetchall()
        conn.close()

        return [
            {"session_id": row[0], "timestamp": row[1]}
            for row in results
        ]

    def clear(self):
        """Clear session state (not persistent history)."""
        self.conversation_history = []
        self.variables = {}
