import os
import json
from datetime import datetime


class SaveManager:
    def __init__(self, saves_dir):
        self.saves_dir = saves_dir
        os.makedirs(self.saves_dir, exist_ok=True)

    def _path(self, filename):
        return os.path.join(self.saves_dir, filename)

    def save_game(self, state: dict, name: str = None, overwrite: bool = False):
        """Save state to a file. If name is None a timestamp name is used.

        If overwrite is False and target exists, raises FileExistsError.
        If overwrite is True, existing file will be replaced.
        Returns the filename used.
        """
        if name is None:
            name = f'save_{int(datetime.utcnow().timestamp())}'
        filename = f'{name}.json'
        path = self._path(filename)
        if os.path.exists(path) and not overwrite:
            raise FileExistsError(f"Save '{filename}' already exists")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return filename

    def list_saves(self):
        out = []
        for fn in sorted(os.listdir(self.saves_dir), reverse=True):
            if not fn.endswith('.json'):
                continue
            path = self._path(fn)
            try:
                mtime = datetime.utcfromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
            except Exception:
                mtime = ''
            out.append({'filename': fn, 'mtime': mtime, 'display': fn.replace('.json','')})
        return out

    def load_save(self, filename):
        path = self._path(filename)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_latest_save(self):
        saves = self.list_saves()
        return saves[0] if saves else None

    def delete_save(self, filename):
        path = self._path(filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def rename_save(self, old_filename, new_name_no_ext):
        old_path = self._path(old_filename)
        if not os.path.exists(old_path):
            raise FileNotFoundError('old save not found')
        new_filename = f"{new_name_no_ext}.json"
        new_path = self._path(new_filename)
        if os.path.exists(new_path):
            raise FileExistsError('target save name already exists')
        os.rename(old_path, new_path)
        return new_filename
