# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" Permissions for Invenio Records Presentation."""
from flask_login import current_user

from invenio_records_presentation.errors import WorkflowsPermissionError, WorkflowsNotAuthenticated


def check_permission(permission):
    """Check if permission is allowed.

    :param permission: The permission to check before running workflow.
    """
    if permission is not None and not permission.can():
        if current_user.is_authenticated:
            raise WorkflowsPermissionError(
                  'You do not have a permission to run the workflow')
        raise WorkflowsNotAuthenticated(
            'You do must be authenticated to run the workflow')
