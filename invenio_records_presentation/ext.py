# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Flask extension for Invenio Records Presentation."""

from __future__ import absolute_import, print_function

import tempfile
from functools import lru_cache

from invenio_workflows import workflows
from werkzeug.utils import cached_property

from invenio_records_presentation.api import Presentation
from . import config


class _RecordsPresentationState(object):

    def __init__(self, app):
        self.app = app
        self.presentations = {}

    @lru_cache(maxsize=1)
    def init_presentations(self):
        for presid in self.presentation_types.keys():
            self.presentations[presid] = self.get_presentation(presid)

    @cached_property
    def presentation_types(self) -> dict:
        ret = {}
        for workflow_id in workflows.keys():
            ret[workflow_id] = {
                'permissions': self.app.config['INVENIO_RECORDS_PRESENTATION_PERMISSIONS'].get(workflow_id, [])
            }
        return ret

    @cached_property
    def scratch_location(self) -> str:
        location = self.app.config.get('INVENIO_RECORDS_PRESENTATION_SCRATCH_LOCATION', None)
        if not location:
            location = tempfile.gettempdir()

        return location

    def get_presentation(self, presentation_id: str) -> Presentation:
        """ Create presentation instance from app config """
        presentation = self.presentations.get(presentation_id, None)

        if not presentation:
            try:
                pres_conf = self.presentation_types[presentation_id]
                permissions = pres_conf['permissions']
            except KeyError:
                raise AttributeError('Invalid presentation type: {}'.format(presentation_id))
            presentation = Presentation(name=presentation_id, permissions=permissions)
            self.presentations[presentation_id] = presentation

        return presentation


class InvenioRecordsPresentation(object):
    """Invenio Records Presentation extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self._state = self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        state = _RecordsPresentationState(app)
        app.extensions['invenio-records-presentation'] = self

        return state

    def init_config(self, app):
        """Initialize configuration.

        Override configuration variables with the values in this package.
        """
        for k in dir(config):
            if k.startswith('INVENIO_RECORDS_PRESENTATION_'):
                app.config.setdefault(k, getattr(config, k))

    def __getattr__(self, name):
        """Proxy to state object."""
        return getattr(self._state, name, None)
