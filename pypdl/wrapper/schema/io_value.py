import os
import json
import logging
import tempfile
import shutil
from copy import deepcopy

from pypdl.util import DotAccessDict


class IOValue(unicode):
    meta = None

    def __new__(cls, value=None):
        if isinstance(value, list):
            value = value[0] if value else ''
        value = os.path.abspath(value) if value else value
        obj = unicode.__new__(cls) if not value else unicode.__new__(cls, value)
        obj.meta = DotAccessDict()
        return obj

    file = property(lambda self: self)

    def _load_meta(self):
        metadata_file = self + '.meta'
        if not os.path.exists(metadata_file):
            logging.warning('No metadata file found: %s', metadata_file)
            self.meta = DotAccessDict()
            return
        logging.debug('Loading metadata from %s', metadata_file)
        with open(metadata_file) as f:
            content = json.load(f)
        if not isinstance(content, dict):
            logging.error('Metadata not a dict: %s', content)
            self.meta = DotAccessDict()
        else:
            self.meta = DotAccessDict(**content)

    def _save_meta(self):
        if not self.file:
            return
        metadata_file = self.file + '.meta'
        logging.debug('Saving metadata to %s', metadata_file)
        if not isinstance(self.meta, dict):
            logging.error('Metadata not a dict: %s', self.meta)
            self.meta = {}
        if not os.path.exists(metadata_file):
            with open(metadata_file, 'w') as f:
                json.dump(self.meta or {}, f)
            return
        tmp = tempfile.mktemp()
        with open(tmp, 'w') as f:
            json.dump(self.meta or {}, f)
        shutil.move(tmp, metadata_file)

    def _abspath(self):
        self.file = os.path.normpath(os.path.abspath(self.file))

    @property
    def size(self):
        return os.stat(self).st_size if os.path.exists(self) else 0

    def make_metadata(self, **kwargs):
        result = deepcopy(self.meta)
        result.update(**kwargs)
        return result
