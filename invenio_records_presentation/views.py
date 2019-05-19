# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Blueprint definitions."""

from __future__ import absolute_import, print_function

import traceback
from functools import wraps
import logging
from uuid import UUID

from celery._state import app_or_default
from celery.result import AsyncResult, result_from_tuple
from flask import Blueprint, jsonify, abort, request, Response, current_app
from flask_login import current_user
from invenio_pidstore.models import PersistentIdentifier
from invenio_userprofiles import UserProfile
from invenio_workflows import WorkflowEngine
from workflow.errors import WorkflowDefinitionError

from .api import Presentation, PresentationWorkflowObject
from .errors import PresentationNotFound, WorkflowsPermissionError
from .proxies import current_records_presentation

logger = logging.getLogger(__name__)

blueprint = Blueprint(
    'invenio_records_presentation',
    __name__,
    url_prefix='/presentation/1.0'
)
"""Blueprint used for loading templates and static assets

The sole purpose of this blueprint is to ensure that Invenio can find the
templates and static files located in the folders of the same names next to
this file.
"""


def pass_result(f):
    """Decorate to provide an AsyncResult instance of the job."""

    @wraps(f)
    def decorate(*args, **kwargs):
        job_uuid = kwargs.pop('job_uuid')
        Result = app_or_default(None).AsyncResult
        result = Result(job_uuid, parent=None)
        # result: AsyncResult = result_from_tuple([[job_uuid, None], None])
        # if result is None:
        #     abort(400, 'Invalid job UUID')

        return f(result=result, *args, **kwargs)

    return decorate


def pass_presentation(f):
    """Decorate to provide a presentation instance."""

    @wraps(f)
    def decorate(*args, **kwargs):
        presid = kwargs.pop('presentation_id')
        try:
            presentation = current_records_presentation.get_presentation(presid)
            return f(presentation=presentation, *args, **kwargs)
        except PresentationNotFound:
            abort(400, 'Invalid presentation type')

    return decorate


def with_presentations(f):
    """ Init all presentation objects """

    @wraps(f)
    def decorate(*args, **kwargs):
        current_records_presentation.init_presentations()
        return f(*args, **kwargs)

    return decorate


@blueprint.route("/")
@with_presentations
def index():
    return 'presentation loaded successfully'


@blueprint.route('/prepare/<string:pid_type>/<string:pid>/<string:presentation_id>/', methods=('POST',))
@with_presentations
def pid_prepare(pid_type: str, pid: str, presentation_id: str):
    pid_record = PersistentIdentifier.query.filter_by(pid_type=pid_type, pid_value=pid).one_or_none()
    if pid_record:
        return prepare(str(pid_record.object_uuid), presentation_id=presentation_id)
    else:
        abort(404, 'Record with PID {}:{} not found'.format(pid_type, pid_type))


@blueprint.route('/prepare/<string:record_uuid>/<string:presentation_id>/', methods=('POST',))
@with_presentations
@pass_presentation
def prepare(record_uuid: str, presentation: Presentation):
    if current_user.is_anonymous:
        user_meta = {
            'id': None,
            'email': None,
            'login_ip': None,
            'current_ip': str(request.remote_addr),
            'roles': [],
            'full_name': 'Anonymous',
            'username': None
        }
    else:
        profile_meta = {}
        profile: UserProfile = UserProfile.get_by_userid(current_user.id)
        if profile:
            profile_meta = {
                'full_name': profile.full_name,
                'username': profile.username,
            }
        user_meta = {
            'id': current_user.id,
            'email': current_user.email,
            'current_ip': str(request.remote_addr),
            'login_ip': str(current_user.current_login_ip),
            'roles': [{'id': role.id, 'name': role.name} for role in current_user.roles]
        }
        user_meta.update(profile_meta)
    headers = {k: v for k, v in request.headers}

    try:
        result = presentation.prepare(record_uuid, user_meta, headers, delayed=True)
        if isinstance(result, AsyncResult):
            return jsonify({'job_id': result.task_id})
        else:
            return jsonify({'job_id': result})
    except WorkflowsPermissionError as e:
        logger.exception('Exception detected in prepare')
        abort(403, e)
    except WorkflowDefinitionError:
        logger.exception('Exception detected in prepare')
        abort(400, 'There was an error in the {} workflow definition'.format(presentation.name))


@blueprint.route('/status/<string:job_uuid>/')
@pass_result
def status(result: AsyncResult):
    if result.state == 'FAILURE':
        print(result.traceback)
    try:
        eng_uuid = str(UUID(result.info, version=4))
        engine = WorkflowEngine.from_uuid(eng_uuid)
        object = engine.objects[-1]
        info = {'current_data': object.data,
                'created': object.created,
                'modified': object.modified}

    except Exception:
        logger.exception('Exception detected in status')
        info = str(result.info)

    return jsonify({'status': result.state, 'info': info})


import unicodedata
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')


@blueprint.route('/download/<string:job_uuid>/')
@pass_result
def download(result: AsyncResult):
    eng_uuid = result.get()  # Will wait until task has completed
    engine = WorkflowEngine.from_uuid(eng_uuid)
    object = PresentationWorkflowObject(engine.objects[-1])

    data_path = object.scratch.full_path(object.data['path'])

    def serve():
        with open(data_path, 'rb') as f:
            while True:
                buf = f.read(128000)
                if not buf:
                    break
                yield buf

    return Response(serve(), mimetype=object.data['mimetype'], headers={
        'Content-disposition': 'inline; filename=\"{}\"'.format(strip_accents(object.data['filename'])),
        'Content-Security-Policy': "object-src 'self';"
    })
