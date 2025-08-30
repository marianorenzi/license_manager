from textual.app import ComposeResult
from textual.widgets import TabPane, DataTable, Button, Input
from textual.containers import Horizontal
from modals.license_form import LicenseDataFormModal
from pathlib import Path
from typing import Tuple
import json

class LicenseTablePane(TabPane):
    COLUMNS = ("Customer", "Product", "Hwid", "Features", "Issued At", "Expires At", "Signature")
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input("/home/manoplin/licenses", id="license_folder_input", placeholder="Path to license storage folder")
            yield Button("Select License Folder", id="select_folder")
        yield Button("New License", id="add_license")
        yield DataTable(fixed_columns=1, zebra_stripes=True, id="license_table")

    def on_mount(self) -> None:
        self.query_one(DataTable).add_columns(*self.COLUMNS)

    def add_license(self, license_data: dict) -> None:
        table = self.query_one(DataTable)
        table.add_row(
            license_data.get("customer", ""),
            license_data.get("product", ""),
            license_data.get("hwid", ""),
            license_data.get("features", ""),
            license_data.get("issued_at", ""),
            license_data.get("expires_at", ""),
            license_data.get("signature", "")
        )

    def clear_licenses(self) -> None:
        table = self.query_one(DataTable)
        table.clear()

    def load_licenses_from_folder(self, folder: str) -> None:
        self.clear_licenses()
        for license_file in Path(folder).glob("*.lic"):
            try:
                with open(license_file, 'r') as f:
                    license_data = json.load(f)
                self.add_license(license_data)
            except Exception as e:
                self.app.notify(f"Failed to load license from {license_file}: {e}", severity="error")

    def create_license_file(self, license_data: dict, folder: str, canonical: str|None = None) -> None:
        filename = license_data.get("hwid", "unknown_hwid")
        filepath = Path(folder) / filename
        with open(Path(folder) / (filename + ".lic"), 'w') as f:
            json.dump(license_data, f, indent=4)
        if canonical:
            with open(Path(folder) / (filename + ".canonical"), 'w') as f:
                f.write(canonical)
        self.app.notify(f"License saved to {filepath}", severity="information")

    def event_new_license(self, result: Tuple[dict,str]|None) -> None:
        if not result: return
        license_data, canonical = result
        self.create_license_file(license_data, self.query_one("#license_folder_input", Input).value, canonical)
        self.add_license(license_data)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "add_license":
            self.app.push_screen(LicenseDataFormModal(), self.event_new_license)
        elif event.button.id == "select_folder":
            folder = self.query_one("#license_folder_input", Input).value
            self.load_licenses_from_folder(folder)