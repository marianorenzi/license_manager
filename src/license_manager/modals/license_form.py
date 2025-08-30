from textual.app import ComposeResult
from textual.events import Key
from textual.screen import ModalScreen
from textual.containers import HorizontalGroup, VerticalGroup, Grid
from textual.widgets import Button, Input, Static
from textual_timepiece.pickers import DatePicker
from widgets.signing_authority import SigningAuthority, SigningAuthorityPane
from datetime import date, datetime
from whenever import Date
from typing import Tuple
import json

class LicenseDataFormModal(ModalScreen[Tuple[dict,str]]):
    def __init__(self, **kargs) -> None:
        super().__init__(**kargs)
        self.signer: SigningAuthority|None = self.app.query_one(SigningAuthorityPane).signing_authority

    def do_sign(self) -> None:
        if not self.signer:
            self.notify("No signing authority available", severity="warning")
            return
        
        data = {
            "customer": self.query_one("#customer", Input).value,
            "product": self.query_one("#product", Input).value,
            "issued_at": date.today().strftime("%Y-%m-%d"),
            "expires_at": self.query_one("#expires_at", DatePicker).value,
            "features": self.query_one("#features", Input).value,
            "hwid": self.query_one("#hwid", Input).value
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        signature = self.signer.sign(canonical)
        data["signature"] = signature

        # return the signed data to the caller
        self.dismiss((data,canonical))

    def compose(self) -> ComposeResult:
        with Grid():
            with VerticalGroup():
                with HorizontalGroup():
                    yield Static("Customer", classes="option_label")
                    yield Input(type="text", id="customer", classes="option_input")
                with HorizontalGroup():
                    yield Static("Product", classes="option_label")
                    yield Input(type="text", id="product", classes="option_input")
                with HorizontalGroup():
                    yield Static("Expiration Date", classes="option_label")
                    yield DatePicker(id="expires_at")
                with HorizontalGroup():
                    yield Static("Features (CSV)", classes="option_label")
                    yield Input(type="text", id="features", classes="option_input")
                with HorizontalGroup():
                    yield Static("Hardware ID", classes="option_label")
                    yield Input(type="text", id="hwid", classes="option_input")
            with HorizontalGroup():
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Sign", variant="primary", id="accept")

    def on_mount(self) -> None:
        self.query_one(VerticalGroup).styles.column_span = 2

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.do_sign()

    def on_key(self, event: Key):
        if event.key == "escape":
            event.stop()
            self.app.pop_screen()
        if event.key == "enter":
            event.stop()
            self.do_sign()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "accept":
            self.do_sign()
        else: self.app.pop_screen()