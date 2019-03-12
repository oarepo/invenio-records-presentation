# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" Errors for Invenio Records Presentation workflows."""
from invenio_workflows.errors import WorkflowsError


class WorkflowsPermissionError(WorkflowsError):
    """ Not enough Permissions to run a workflow."""

class WorkflowsRecordNotFound(WorkflowsError):
    """ Record from a Workflow context could not be found."""

class WorkflowsNotAuthenticated(WorkflowsError):
    """ Unauthenticated user tries to run a workflow """

class WorkflowAccessOutsideScratch(WorkflowsError):
    """ Accessing a file outside the scratch directory """

class PresentationNotFound(Exception):
    """ Presentation for a given name not found """
