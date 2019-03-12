# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" API for Invenio Records Presentation."""
from typing import Optional

from invenio_db import db
from invenio_records import Record
from invenio_workflows import workflows, WorkflowObject
from invenio_workflows.errors import WorkflowsMissingData
from sqlalchemy.orm.exc import NoResultFound

from invenio_records_presentation.errors import WorkflowsRecordNotFound
from invenio_records_presentation.workflows import PresentationWorkflow, presentation_workflow_factory
from .utils import obj_or_import_string, ScratchDirectory


class PresentationWorkflowObject(WorkflowObject):
    """Main entity for the presentation workflow module."""

    def __init__(self, model=None):
        """Instantiate class."""
        super(PresentationWorkflowObject, self).__init__(model)

    def start_workflow(self, workflow_name, delayed=False, permissions=None,
                       record_uuid=None, user=None, request_headers=dict, **kwargs):

        if permissions is None:
            raise WorkflowsMissingData("Missing workflow permissions")

        if not user:
            raise WorkflowsMissingData("Missing user info")

        if not record_uuid:
            raise WorkflowsMissingData("Missing Record ID")

        self.model.extra_data['_record'] = record_uuid
        self.model.extra_data['_user'] = user
        self.model.extra_data['_request'] = request_headers
        self.model.extra_data['_scratch'] = self.scratch.dir_path

        return super(PresentationWorkflowObject, self).start_workflow(
            workflow_name, delayed, **kwargs)

    @property
    def record(self) -> Optional[Record]:
        try:
            return Record.get_record(self.model.extra_data['_record'])
        except NoResultFound:
            raise WorkflowsRecordNotFound('No Record for id: {}'
                                          .format(self.model.extra_data['_record']))

    @property
    def scratch(self) -> ScratchDirectory:
        if self.model.extra_data.get('_scratch', None):
            return ScratchDirectory.from_path(self.model.extra_data['_scratch'])

        return ScratchDirectory()


class Presentation(object):

    def __init__(self, name: str, tasks: list, permissions: list):
        self.name = name
        self.tasks = []
        self.permissions = []
        self.init_tasks(tasks)
        self.init_permissions(permissions)
        self.register_workflow()
        self.initialized = True

    def init_tasks(self, task_list: list):
        """ Initialize tasks for a workflow pipeline"""
        for task in task_list:
            task_obj = obj_or_import_string(task)
            if not task_obj:
                raise AttributeError('Task "{}" could not be loaded'.format(task))

            self.tasks.append(task_obj)

    def init_permissions(self, permission_list: list):
        """ Initialize permissions needed for presentation tasks execution """
        for perm in permission_list:
            perm_obj = obj_or_import_string(perm)
            if not perm_obj:
                raise AttributeError('Permission "{}" could not be initialized'.format(perm))

            self.permissions.append(perm)

    def register_workflow(self):
        """ Register itself by a name into invenio-workflows registry """
        workflow: PresentationWorkflow = workflows.get(self.name, None)
        if not workflow:
            workflow = presentation_workflow_factory(task_list=self.tasks)
            workflows[self.name] = workflow

    def prepare(self, record_uuid, user, request_headers=dict):
        """ Prepare Presentation of a given record

        :param record_uuid: UUID of a Record to be presented
        :param user: dict containing user metadata
        :param request_headers: headers dict of a calling request
        """
        assert self.initialized

        presentation_obj = PresentationWorkflowObject().create(data=record_uuid)
        return presentation_obj.start_workflow(self.name, delayed=True,
                                               permissions=self.permissions,
                                               record_uuid=record_uuid, user=user,
                                               request_headers=request_headers)
