from textual import on, work
from textual.app import ComposeResult
from textual.widgets import TabPane, Button, Static, Label, Input
from textual.containers import Horizontal, Container
from textual_fspicker import FileOpen, FileSave
from nacl import signing, encoding
from pathlib import Path
import os
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
                yield Button("Generate Keys", id="generate")
                yield Button("Open Keys", id="open")
                yield Button("Save Keys", id="save")
            with Horizontal():
                yield Static("Current Key:", classes="option_label")
                yield Input("", disabled=True, id="current_key", classes="crypto_key")
            with Horizontal():
                yield Static("Signing Key:", classes="option_label")
                yield Input("", disabled=True, id="signing_key", classes="crypto_key")
            with Horizontal():
                yield Static("Verification Key:", classes="option_label")
                yield Input("", disabled=True, id="verification_key", classes="crypto_key")
                yield Button("Copy", id="copy_verification_key")
        yield Container()

    def on_mount(self) -> None:
        last_key = self.app.ctx["last_key"]
        if (last_key): self._load_key(last_key)
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "generate":
            self.signing_authority = SigningAuthority()
            self.query_one("#signing_key", Input).value = self.signing_authority.get_signing_key()
            self.query_one("#verification_key", Input).value = self.signing_authority.get_verification_key()
            self.query_one("#current_key", Input).value = ""
        elif event.button.id == "copy_verification_key":
            if self.signing_authority:
                pyperclip.copy(self.signing_authority.get_verification_key())
                self.app.notify("Verification key copied to clipboard", severity="information")
            else:
                self.app.notify("No signing authority loaded", severity="warning")

    @on(Button.Pressed, "#open")
    @work
    async def open_key(self) -> None:
        if open_key := await self.app.push_screen_wait(FileOpen(title="Open Signing Key File", location=self._key_folder())):
            self._load_key(str(open_key))
            self.app.ctx["last_key"] = str(open_key)

    @on(Button.Pressed, "#save")
    @work
    async def save_key(self) -> None:
        if self.signing_authority is None:
            self.app.notify("No signing authority to save", severity="warning")
            return
        if save_key := await self.app.push_screen_wait(FileSave(title="Save Signing Key File", location=self._key_folder())):
            self._save_key(str(save_key))

    def _load_key(self, key_file: str) -> None:
        self.signing_authority = SigningAuthority(signing_key_file=key_file)
        self.query_one("#signing_key", Input).value = self.signing_authority.get_signing_key()
        self.query_one("#verification_key", Input).value = self.signing_authority.get_verification_key()
        self.query_one("#current_key", Input).value = key_file

    def _save_key(self, key_file: str) -> None:
        if self.signing_authority is None: return

        with open(key_file, "w") as f:
            f.write(self.signing_authority.get_signing_key())

        self.app.ctx["last_key"] = key_file
        self.query_one("#current_key", Input).value = key_file

    def _key_folder(self) -> Path:
        if self.app.ctx["last_key"] is not None: key_folder = os.path.dirname(os.path.realpath(self.app.ctx["last_key"]))
        else: key_folder = "."
        return Path(key_folder)