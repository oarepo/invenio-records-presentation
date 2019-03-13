# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" Permissions for Invenio Records Presentation."""
from functools import partial, wraps

from flask_login import current_user
from invenio_access import ParameterizedActionNeed, Permission
from invenio_workflows import WorkflowEngine

from invenio_records_presentation.errors import WorkflowsPermissionError, WorkflowsNotAuthenticated


WorkflowStart = partial(
    ParameterizedActionNeed, 'records-presentation-workflow-start')
"""Action needed: Workflow start."""


def check_engine_owner(engine: WorkflowEngine):
    """ Check if the engine belongs to a logged in user """
    if engine.id_user != current_user.id:
        raise WorkflowsPermissionError('You do not have a permission to access the workflow')

def need_permissions(object_getter, action, hidden=True):
    """ Get permission for Workflow execution or abort.
    """
    def decorator_builder(f):
        @wraps(f)
        def decorate(*args, **kwargs):
            check_permission(permission_factory(
                object_getter(*args, **kwargs)))
            return f(*args, **kwargs)
        return decorate
    return decorator_builder


def check_permissions(permissions, record_uuid=None, user=None,
                               request_headers=dict, **kwargs):
    """ Check that all required permissions are
        met before a workflow is started.

        :param record_uuid: UUID of a Record to be presented
        :param user: dict containing user metadata
        :param request_headers: headers dict of a calling request
    """
    pass

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
            'You do must be authenticated to run the workflow')


def permission_factory(obj):
    """Get default permission factory.

        :param obj: An instance of :class:`invenio_records_presentation.api.PresentationWorkflowObject`

        :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    return Permission(WorkflowStart(obj.id))
