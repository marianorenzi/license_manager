from textual import on
from textual.app import ComposeResult
from textual.events import Key
from textual.screen import ModalScreen
from textual.containers import HorizontalGroup, VerticalGroup, Grid
from textual.widgets import Button, Input, Static, Label
from textual.validation import Function
from textual_timepiece.pickers import DatePicker, DateInput
from license_manager.widgets.signing_authority import SigningAuthority, SigningAuthorityPane
from datetime import date
import json

DateInput.PATTERN = "0000-b0-00"

class LicenseDataFormModal(ModalScreen[dict]):
    def __init__(self, **kargs) -> None:
        super().__init__(**kargs)
        self.signer: SigningAuthority|None = self.app.query_one(SigningAuthorityPane).signing_authority

    def do_sign(self) -> None:
        if not self.signer:
            self.notify("No signing authority available", severity="warning")
            return
        
        expires_at = self.query_one("#expires_at", DatePicker).value
        if expires_at is not None:
            expires_at = expires_at.format_common_iso()
        else:
            expires_at = ""
            
        data = {
            "customer": self.query_one("#customer", Input).value,
            "product": self.query_one("#product", Input).value,
            "issued_at": date.today().strftime("%Y-%m-%d"),
            "expires_at": expires_at,
            "features": self.query_one("#features", Input).value,
            "hwid": self.query_one("#hwid", Input).value
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        signature = self.signer.sign(canonical)
        data["signature"] = signature
        data["canonical"] = canonical

        # return the signed data to the caller
        self.dismiss(data)

    def compose(self) -> ComposeResult:
        with Grid():
            with VerticalGroup(id="body"):
                with HorizontalGroup():
                    yield Static("Customer", classes="option_label")
                    yield Input(type="text", id="customer", classes="option_input")
                with HorizontalGroup():
                    yield Static("Product", classes="option_label")
                    yield Input(type="text", id="product", classes="option_input")
                with HorizontalGroup():
                    yield Static("Expiration Date", classes="option_label")
                    yield DatePicker(id="expires_at", classes="-invalid")
                with HorizontalGroup():
                    yield Static("Features (CSV)", classes="option_label")
                    yield Input(type="text", id="features", classes="option_input")
                with HorizontalGroup():
                    yield Static("Hardware ID", classes="option_label")
                    yield Input(type="text", id="hwid", classes="option_input", valid_empty=False, validate_on=["submitted","changed","blur"], validators=Function(is_not_empty, "Hardware ID cannot be empty"))
                with VerticalGroup(id="error_container"):
                    yield Label("", id="errors", classes="error")
                with HorizontalGroup(id="buttons"):
                    yield Button("Cancel", variant="error", id="cancel")
                    yield Button("Sign", variant="primary", id="accept")

    def on_mount(self) -> None:
        self._validate()

    @on(Input.Submitted)
    def on_any_input_submitted(self) -> None:
        self._submit()

    @on(Input.Changed)
    @on(DatePicker.Changed)
    @on(DateInput.Updated)
    def on_any_input_change(self):
        self._validate()

    def on_key(self, event: Key):
        if event.key == "escape":
            event.stop()
            self.app.pop_screen()
        if event.key == "enter":
            event.stop()
            self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "accept":
            self._submit()
        else: self.app.pop_screen()

    def _validate(self) -> bool:
        valid = True
        errors = ""
        for input in self.query(Input):
            r = input.validate(input.value)
            if r and not r.is_valid: 
                valid = False
                for description in r.failure_descriptions:
                    errors += "- " + description + "\n"

        self.query_one("#errors", Label).update(errors.strip())
        return valid

    def _submit(self) -> None:
        if self._validate():
            self.do_sign()

def is_not_empty(value: str):
    if not value: return False
    else: return True