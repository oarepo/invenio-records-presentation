# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" API for Invenio Records Presentation."""
from typing import Optional

from invenio_accounts.models import User
from invenio_db import db
from invenio_records_files.api import Record
from invenio_workflows import workflows, WorkflowObject
from invenio_workflows.errors import WorkflowsMissingData
from sqlalchemy.orm.exc import NoResultFound

from invenio_records_presentation.errors import WorkflowsRecordNotFound
from invenio_records_presentation.permissions import needs_permission
from invenio_records_presentation.workflows import PresentationWorkflow
from .utils import obj_or_import_string, ScratchDirectory


class PresentationWorkflowObject(WorkflowObject):
    """Main entity for the presentation workflow module."""

    def __init__(self, model=None):
        """Instantiate class."""
        super(PresentationWorkflowObject, self).__init__(model)

    @needs_permission()
    def start_workflow(self, workflow_name, delayed=False, permissions=None,
                       record_uuid=None, user=None, request_headers=dict, **kwargs):
        """Run the workflow specified on the object.
           :param workflow_name: name of workflow to run
           :type workflow_name: str

           :param delayed: should the workflow run asynchronously?
           :type delayed: bool

           :param record_uuid: UUID of a Record to be presented
           :param user: dict containing user metadata
           :param request_headers: headers dict of a calling request

           :return: UUID of WorkflowEngine (or AsyncResult).
        """
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

        from invenio_workflows.tasks import start

        self.save()
        db.session.commit()

        if delayed:
            return start.delay(workflow_name, object_id=self.id, **kwargs)
        else:
            return start(workflow_name, data=[self], **kwargs)

    @property
    def extra_data(self):
        return self.model.extra_data

    @property
    def record(self) -> Optional[Record]:
        try:
            return Record.get_record(self.model.extra_data['_record'])
        except NoResultFound:
            raise WorkflowsRecordNotFound('No Record for id: {}'
                                          .format(self.model.extra_data['_record']))

    @property
    def user(self):
        return User.query.get(self.model.extra_data['_user']['id'])

    @property
    def scratch(self) -> ScratchDirectory:
        if self.model.extra_data.get('_scratch', None):
            return ScratchDirectory.from_path(self.model.extra_data['_scratch'])

        return ScratchDirectory()


class Presentation(object):

    def __init__(self, name: str, permissions: list):
        self.name = name
        self.permissions = []
        self.init_permissions(permissions)
        self.initialized = True

    def init_permissions(self, permission_list: list):
        """ Initialize permissions needed for presentation tasks execution """
        for perm, args in permission_list:
            perm_obj = obj_or_import_string(perm)
            if not perm_obj:
                raise AttributeError('Permission "{}" could not be initialized'.format(perm))

            self.permissions.append(perm_obj(args))

    @property
    def workflow(self) -> Optional[PresentationWorkflow]:
        return workflows.get(self.name, None)

    def prepare(self, record_uuid, user, request_headers=dict) -> str:
        """ Prepare Presentation of a given record

            :param record_uuid: UUID of a Record to be presented
            :param user: dict containing user metadata
            :param request_headers: headers dict of a calling request

            :returns eng_uuid: running workflow engine UUID
        """
        assert self.initialized

        presentation_obj = PresentationWorkflowObject().create(data='/tmp')
        return presentation_obj.start_workflow(self.name, delayed=False,
                                               permissions=self.permissions,
                                               record_uuid=record_uuid, user=user,
                                               request_headers=request_headers)
