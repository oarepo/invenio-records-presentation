# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" Permissions for Invenio Records Presentation."""
from functools import wraps

from flask_login import current_user
from invenio_access import Permission, action_factory
from invenio_workflows import WorkflowEngine

from invenio_records_presentation.errors import WorkflowsPermissionError, WorkflowsNotAuthenticated


PresentationWorkflowStart = action_factory(
     'presentation-workflow-start', parameter=True)
"""Action: Presentation Workflow start."""

presentation_workflow_start_all = PresentationWorkflowStart(None)


def needs_permission():
    """ Get permission for Workflow execution or abort. """
    def decorator_builder(f):
        @wraps(f)
        def decorate(*args, **kwargs):
            permissions = kwargs.get('permissions', [])
            if permissions:
                check_permission(Permission(*permissions))
            return f(*args, **kwargs)
        return decorate
    return decorator_builder


def check_permission(permission):
    """Check for a given permission.

    :param permission: The permission to check before running workflow.

    :raises WorkflowsPermissionError|WorkflowsNotAuthenticated
    """
    if permission is not None and not permission.can():
        if current_user.is_authenticated:
            raise WorkflowsPermissionError(
                  'You do not have a permission to run the workflow')
        raise WorkflowsNotAuthenticated(
            'You must be authenticated to run the workflow')
