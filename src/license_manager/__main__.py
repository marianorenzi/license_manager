#!/usr/bin/env python3
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Static, Button, Label, Input, TabbedContent
from license_manager.widgets.signing_authority import SigningAuthorityPane
from license_manager.widgets.license_table import LicenseTablePane
from license_manager.utils.app_context import AppContext

class RightHandLicenseManager(App):
    
    CSS_PATH = "style.tcss"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ctx = AppContext("rhlm")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            yield LicenseTablePane(title="Licenses")
            yield SigningAuthorityPane(title="Signing Authority")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "RightHand License Manager"

def main():
    RightHandLicenseManager().run()

if __name__ == "__main__":
    main()
