from textual.app import ComposeResult
from textual.widgets import TabPane, Button, Static, Label, Input
from textual.containers import Horizontal, Container
from nacl import signing, encoding
import base64
import pyperclip

class SigningAuthority():
    def __init__(self, signing_key: signing.SigningKey|None= None, signing_key_str: str|None = None, signing_key_file: str|None = None) -> None:
        if signing_key:
            self.signing_key = signing_key
        elif signing_key_str:
            self.signing_key = signing.SigningKey(signing_key_str.encode('utf-8'), encoder=encoding.URLSafeBase64Encoder)
        elif signing_key_file:
            with open(signing_key_file, 'r') as f:
                key_data = f.read().strip()
            self.signing_key = signing.SigningKey(key_data.encode('utf-8'), encoder=encoding.URLSafeBase64Encoder)
        else:
            self.signing_key = signing.SigningKey.generate()

    def get_signing_key(self) -> str:
        return self.signing_key.encode(encoder=encoding.URLSafeBase64Encoder).decode('utf-8')

    def get_verification_key(self) -> str:
        return self.signing_key.verify_key.encode(encoder=encoding.URLSafeBase64Encoder).decode('utf-8')

    def sign(self, data: str) -> str:
        signed = self.signing_key.sign(data.encode('utf-8')).signature
        return base64.urlsafe_b64encode(signed).decode('utf-8')
    
class SigningAuthorityPane(TabPane):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.signing_authority: SigningAuthority|None = None

    def compose(self) -> ComposeResult:
        with Container(id="signing_authority_container"):
            with Horizontal():
                yield Input("/home/manoplin/licenses/signkey", id="signing_key_file_input", placeholder="Path to signing key file")
                yield Button("Load Keys", id="load")
                yield Button("Create Keys", id="create")
            with Horizontal():
                yield Static("Signing Key: ", classes="option_label")
                yield Input("", disabled=True, id="signing_key", classes="crypto_key")
                # yield Label("", id="signing_key", classes="crypto_key option_label")
            with Horizontal():
                yield Static("Verification Key: ", classes="option_label")
                yield Input("", disabled=True, id="verification_key", classes="crypto_key")
                yield Button("Copy", id="copy_verification_key")
                # yield Label("", id="verification_key", classes="crypto_key option_label")
        yield Container()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "load":
            self.signing_authority = SigningAuthority(signing_key_file=self.query_one("#signing_key_file_input", Input).value)
            self.query_one("#signing_key", Input).value = self.signing_authority.get_signing_key()
            self.query_one("#verification_key", Input).value = self.signing_authority.get_verification_key()
            # self.query_one("#signing_key", Label).update(self.signing_authority.get_signing_key())
            # self.query_one("#verification_key", Label).update(self.signing_authority.get_verification_key())
        elif event.button.id == "create":
            self.signing_authority = SigningAuthority()
            self.query_one("#signing_key", Input).value = self.signing_authority.get_signing_key()
            self.query_one("#verification_key", Input).value = self.signing_authority.get_verification_key()
            # self.query_one("#signing_key", Label).update(self.signing_authority.get_signing_key())
            # self.query_one("#verification_key", Label).update(self.signing_authority.get_verification_key())
            with open(self.query_one("#signing_key_file_input", Input).value, "w") as f:
                f.write(self.signing_authority.get_signing_key())
        elif event.button.id == "copy_verification_key":
            if self.signing_authority:
                pyperclip.copy(self.signing_authority.get_verification_key())
                self.app.notify("Verification key copied to clipboard", severity="information")
            else:
                self.app.notify("No signing authority loaded", severity="warning")