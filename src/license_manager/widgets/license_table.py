from textual import on, work
from textual.app import ComposeResult
from textual.widgets import TabPane, DataTable, Button, Input
from textual.containers import Horizontal
from textual_fspicker import FileSave, FileOpen, Filters
from license_manager.modals.license_form import LicenseDataFormModal
from pathlib import Path
from typing import List, Dict, Optional, Any
import sqlite3
import json
import os

class LicenseTablePane(TabPane):
    COLUMNS = ("Id", "Customer", "Product", "Issued At", "Expires At", "Features", "Hwid")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            with Horizontal(classes="license_actions"):
                yield Button("New", id="new_license")
                yield Button("Delete", id="delete_license")
                yield Button("Export", id="export_license")
                yield Button("Load", id="load_licenses")
            with Horizontal(classes="search_container"):
                yield Input("", id="search_input", placeholder="Search on all columns")
                yield Button("Search", id="add_license")
        yield DataTable(fixed_columns=1, zebra_stripes=True, id="license_table", cursor_type="row")

    def on_mount(self) -> None:
        self.license_db_path: str = self.app.ctx["license_db"]
        self.license_db = LicenseDB(self.license_db_path)
        self.query_one(DataTable).add_columns(*self.COLUMNS)
        self._load_licenses()

    def add_license(self, license_data: dict) -> None:
        license_key = self.license_db.add_license(license_data)
        if license_key:
            license_data["id"] = license_key
            self._table_add_license(license_data)

    @on(Button.Pressed, "#new_license")
    def on_new_license(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.push_screen(LicenseDataFormModal(), self._event_new_license)

    @on(Button.Pressed, "#delete_license")
    def on_delete_license(self, event: Button.Pressed) -> None:
        event.stop()
        license_data = self._get_selected_license()
        if not license_data:
            self.app.notify(f"No license selected", severity="warning")
            return
        
        if self.license_db.delete_license(int(license_data["id"])):
            self._table_remove_license(license_data["id"])

    @work
    @on(Button.Pressed, "#export_license")
    async def on_export_license(self, event: Button.Pressed) -> None:
        event.stop()
        
        license_data = self._get_selected_license()
        if not license_data:
            self.app.notify(f"No license selected", severity="warning")
            return

        license_file = await self.app.push_screen_wait(
            FileSave(title="Save License File",
                     filters=Filters(
                        ("License", lambda p: p.suffix.lower() == ".lic"),
                        ("All", lambda _: True)
                     ),
                     location=self._db_folder(),
                     default_file=Path(license_data["hwid"] + ".lic")))
        if not license_file: return
        
        del license_data["id"]
        del license_data["canonical"]
        with open(license_file, 'w') as f:
            json.dump(license_data, f, indent=4)
        self.app.notify(f"License saved to {license_file}", severity="information")

    @work
    @on(Button.Pressed, "#load_licenses")
    async def on_load_licenses(self, event: Button.Pressed) -> None:
        event.stop()
        license_db_file = await self.app.push_screen_wait(
            FileOpen(title="Open License Database", 
                     must_exist=False,
                     filters=Filters(
                        ("Sqlite3", lambda p: p.suffix.lower() == ".db"),
                        ("All", lambda _: True)
                     ),
                     location=self._db_folder()))
        self._change_db(license_db_file)

    def _event_new_license(self, result: dict|None) -> None:
        if result:
            self.add_license(result)

    def _load_licenses(self) -> None:
        licenses = self.license_db.list_licenses()
        if not licenses: return
        for license in licenses:
            self._table_add_license(license)

    def _change_db(self, db_file: Path|None) -> None:
        if db_file:
            self.app.ctx["license_db"] = str(db_file)
            self.license_db_path = str(db_file)
            self.license_db.change_db(db_file)
            self._table_clear_licenses()
            self._load_licenses()

    def _db_folder(self) -> Path:
        if self.license_db_path is not None: license_db_folder = os.path.dirname(os.path.realpath(self.license_db_path))
        else: license_db_folder = "."
        return Path(license_db_folder)

    def _table_add_license(self, license_data: dict) -> None:
        table = self.query_one(DataTable)
        key = table.add_row(
            license_data.get("id", ""),
            license_data.get("customer", ""),
            license_data.get("product", ""),
            license_data.get("issued_at", ""),
            license_data.get("expires_at", ""),
            license_data.get("features", ""),
            license_data.get("hwid", ""),
            key=str(license_data["id"])
        )

    def _table_remove_license(self, license_key: str) -> None:
        table = self.query_one(DataTable)
        table.remove_row(str(license_key))

    def _table_clear_licenses(self) -> None:
        table = self.query_one(DataTable)
        table.clear()

    def _get_selected_license(self) -> dict|None:
        table = self.query_one(DataTable)
        row_data = table.get_row_at(table.cursor_coordinate.row)
        license_data = self.license_db.get_license(row_data[0])
        return license_data

class LicenseDB:
    def __init__(self, db_path: str) -> None:
        """Initialize connection to a SQLite3 database."""
        self.conn = None
        if db_path and len(db_path):
            self.db_path = db_path
            self.conn: Optional[sqlite3.Connection] = None
            self._connect()
            self._init_schema()

    def connected(self) -> bool:
        return self.conn is not None

    def change_db(self, new_path: Path) -> None:
        """Switch to a different database file."""
        self.db_path = new_path
        self._connect()
        self._init_schema()

    def add_license(self, license_data: dict) -> int|None:
        if not self.conn: return

        with self.conn:
            cur = self.conn.execute(
                """
                INSERT INTO licenses (customer, product, issued_at, expires_at, features, hwid, signature, canonical)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (license_data.get("customer", ""),
                 license_data.get("product", ""), 
                 license_data.get("issued_at", ""), 
                 license_data.get("expires_at", ""), 
                 license_data.get("features", ""), 
                 license_data.get("hwid", ""),
                 license_data.get("signature", ""),
                 license_data.get("canonical", ""))
            )

            return cur.lastrowid

    def get_license(self, license_id: int) -> Optional[Dict[str, Any]]:
        if not self.conn: return
        """Retrieve a license by its ID."""
        cur = self.conn.execute("SELECT * FROM licenses WHERE id = ?", (license_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def list_licenses(self) -> Optional[List[Dict[str, Any]]]:
        if not self.conn: return None
        """Retrieve all licenses."""
        cur = self.conn.execute("SELECT * FROM licenses")
        return [dict(row) for row in cur.fetchall()]

    def delete_license(self, license_id: int) -> bool:
        if not self.conn: return False
        """Delete a license. Returns True if deleted."""
        with self.conn:
            cur = self.conn.execute("DELETE FROM licenses WHERE id = ?", (license_id,))
            return cur.rowcount > 0

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def _connect(self) -> None:
        if self.conn:
            self.conn.close()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # results as dict-like rows

    def _init_schema(self) -> None:
        if not self.conn: return
        """Ensure the licenses table exists."""
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer TEXT,
                    product TEXT,
                    issued_at TEXT,
                    expires_at TEXT,
                    features TEXT,
                    hwid TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    canonical TEXT NOT NULL
                )
                """
            )