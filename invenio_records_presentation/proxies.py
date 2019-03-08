# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" API for Invenio Records Presentation."""

from flask import current_app
from werkzeug.local import LocalProxy

from invenio_records_presentation.ext import _RecordsPresentationState

current_records_presentation: _RecordsPresentationState = LocalProxy(lambda:
                                                                     current_app.extensions['invenio-records-presentation'])
