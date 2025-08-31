from platformdirs import user_config_dir
import json, os, tempfile

class AppContext:
    def __init__(self, app_name: str) -> None:
        self.app_name = app_name
        self.config_dir = user_config_dir(app_name)
        os.makedirs(self.config_dir, exist_ok=True)
        self._clean_temp_files()
        self.state_file = os.path.join(self.config_dir, "context.json")
        self.context: dict = self._load()

    def get(self, key, default=None):
        return self.context.get(key, default)
    
    def set(self, key, value):
        self.context[key] = value
        self._save()

    def update(self, **kwargs):
        self.context.update(kwargs)
        self._save()

    def __getitem__(self, key):
        return self.context.get(key)

    def __setitem__(self, key, value):
        self.context[key] = value
        self._save()

    def _load(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                # corrupted or unreadable → start fresh
                return {}
        return {}

    def _save(self):
        # Write atomically using tempfile
        fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=self.config_dir)
        try:
            with os.fdopen(fd, "w") as tmp_file:
                json.dump(self.context, tmp_file)
            os.replace(tmp_path, self.state_file)  # atomic replace
        except Exception:
            os.remove(tmp_path)  # cleanup on failure
            raise

    def _clean_temp_files(self):
        for fname in os.listdir(self.config_dir):
            if fname.endswith(".tmp"):
                try:
                    os.remove(os.path.join(self.config_dir, fname))
                except OSError:
                    pass  # ignore files that can't be removed