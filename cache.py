import json
import os
from datetime import datetime, timedelta

class CompanyCache:
    def __init__(self, cache_file='company_cache.json', cache_duration_days=30):
        self.cache_file = cache_file
        self.cache_duration = timedelta(days=cache_duration_days)
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)

    def get(self, company_name):
        if company_name in self.cache:
            cache_entry = self.cache[company_name]
            cache_time = datetime.fromisoformat(cache_entry['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return cache_entry['data']
        return None

    def set(self, company_name, data):
        self.cache[company_name] = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self._save_cache()

    def clear_expired(self):
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - datetime.fromisoformat(entry['timestamp']) > self.cache_duration
        ]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            self._save_cache() 