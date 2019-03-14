# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" Utils for Invenio Records Presentation."""
import os
import tempfile

from six import string_types
from werkzeug.utils import import_string

from invenio_records_presentation.errors import WorkflowAccessOutsideScratch


def obj_or_import_string(value, default=None):
    """Import string or return object."""
    if isinstance(value, string_types):
        return import_string(value)
    elif value:
        return value
    return default


class ScratchDirectory:

    id = 0

    def __init__(self, scratch_dir=None):
        from .proxies import current_records_presentation

        self.scratch_root = current_records_presentation.scratch_location

        if scratch_dir:
            self.scratch_dir = scratch_dir
            self.validate_dir(scratch_dir)
            for _, _, files in os.walk(self.scratch_dir):
                for file in files:
                    fileid = int(file.split('_', 1)[0])
                    if fileid >= self.id:
                        self.id = fileid + 1
        else:
            self.scratch_dir = tempfile.mkdtemp(prefix='invenio_presentation_',
                                                dir=self.scratch_root)
            self.id = 0

    def validate_dir(self, path):
        real_path = os.path.realpath(path)
        if not (real_path.startswith(self.scratch_root)
                and real_path.startswith(self.scratch_dir)):
            raise WorkflowAccessOutsideScratch(
                'Path {} is outside of scratch root {}'
                                 .format(path, self.scratch_dir))

    def _next(self):
        base = '%06d_' % self.id
        self.id += 1
        return base

    @property
    def dir_path(self):
        return self.scratch_dir

    def full_path(self, name):
        return os.path.join(self.scratch_dir, name)

    @staticmethod
    def from_path(path):
        return ScratchDirectory(scratch_dir=path)

    def create_file(self, task_name=None, pass_fh=False):
        fd, path = tempfile.mkstemp(dir=self.dir_path, prefix='{}{}'
                                .format(self._next(), task_name))
        if pass_fh:
            return os.fdopen(fd, "wb"), path
        else:
            os.close(fd)
            return path

    def create_directory(self):
        return self._next()
