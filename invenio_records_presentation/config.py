# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Default configuration."""

from __future__ import absolute_import, print_function

WORKFLOWS_OBJECT_CLASS = 'invenio_records_presentation.api.PresentationWorkflowObject'
""" Class to be passed into records presentation tasks """

INVENIO_RECORDS_PRESENTATION_SCRATCH_LOCATION = None
""" Location of temporary files created by presentation tasks. Defaults to: /tmp/ """

INVENIO_RECORDS_PRESENTATION_TYPES = dict(
    # presentation_id: {
    #   tasks: [
    #       module1:task1,
    #       module2:task2,
    #       ...
    #   ]
    #   permissions: [
    #       module1:action_read_permission,
    #       ...
    #   ]
    # }
    example=dict(
        tasks=['invenio_records_presentation.workflows.presentation:get_filename'],
        permissions=[]
    )
)
""" Define a tasks to be called for a certain record presentation
    and permissions to be checked before the presentation tasks are executed in a pipeline.
"""
