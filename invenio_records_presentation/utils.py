# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" Utils for Invenio Records Presentation."""
from six import string_types
from werkzeug.utils import import_string


def obj_or_import_string(value, default=None):
    """Import string or return object."""
    if isinstance(value, string_types):
        return import_string(value)
    elif value:
        return value
    return default
