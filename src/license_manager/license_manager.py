#!/usr/bin/env python3
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Static, Button, Label, Input, TabbedContent
from widgets.signing_authority import SigningAuthorityPane
from widgets.license_table import LicenseTablePane

class RightHandLicenseManager(App):
    
    CSS_PATH = "style.tcss"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            yield LicenseTablePane(title="Licenses")
            yield SigningAuthorityPane(title="Signing Authority")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "RightHand License Manager"

if __name__ == "__main__":
    RightHandLicenseManager().run()
