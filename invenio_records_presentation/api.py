# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" API for Invenio Records Presentation."""
from invenio_records import Record
from invenio_workflows import workflows

from invenio_records_presentation.workflows import PresentationWorkflow, presentation_workflow_factory
from .utils import obj_or_import_string


class Presentation(object):

    def __init__(self, name: str, tasks: list, permissions: list):
        self.name = name
        self.tasks = []
        self.permissions = []
        self.init_tasks(tasks)
        self.init_permissions(permissions)

    def init_tasks(self, task_list: list):
        """ Initialize tasks for a workflow pipeline"""
        for task in task_list:
            task_obj = obj_or_import_string(task)
            if not task_obj:
                raise AttributeError('Task "{}" could not be loaded'.format(task))

            self.tasks.append(task)

    def init_permissions(self, permission_list: list):
        """ Initialize permissions needed for presentation tasks execution """
        for perm in permission_list:
            perm_obj = obj_or_import_string(perm)
            if not perm_obj:
                raise AttributeError('Permission "{}" could not be initialized'.format(perm))

            self.permissions.append(perm)

    def workflow(self) -> PresentationWorkflow:
        workflow: PresentationWorkflow = workflows.get(self.name, None)
        if not workflow:
            workflow = presentation_workflow_factory(task_list=self.tasks)
            workflows[self.name] = workflow

        return workflow

class RecordsPresentation(object):

    def __init__(self, app, record: Record, presentation: Presentation):
        self.app = app
        self.record = record
        self.presentation = presentation

__all__ = ('RecordsPresentation', 'Presentation')

