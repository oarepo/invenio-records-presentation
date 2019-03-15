# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Blueprint definitions."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import Blueprint, jsonify, abort, request
from flask_login import current_user, login_required
from invenio_pidstore.models import PersistentIdentifier
from invenio_userprofiles import UserProfile
from invenio_workflows import WorkflowEngine, ObjectStatus
from workflow.errors import WorkflowDefinitionError

from invenio_records_presentation.permissions import check_engine_owner
from .api import Presentation
from .errors import PresentationNotFound, WorkflowsPermissionError
from .proxies import current_records_presentation

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


def pass_engine(f):
    """Decorate to retrieve a workflow engine."""

    @wraps(f)
    def decorate(*args, **kwargs):
        eng_uuid = kwargs.pop('eng_uuid')
        engine = WorkflowEngine.from_uuid(eng_uuid)
        if not engine:
            abort(404, 'Presentation job does not exist.')
        try:
            check_engine_owner(engine)
        except WorkflowsPermissionError:
            # Do not expose that the job actually exists,
            # just for a different user.
            abort(404, 'Presentation job does not exist.')

        return f(engine=engine, *args, **kwargs)

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
#@with_presentations
@pass_presentation
def pid_prepare(pid_type: str, pid: str, presentation: Presentation):
    pid_record = PersistentIdentifier.query.filter_by(pid_type=pid_type, pid_value=pid).one_or_none()
    if pid_record:
        return prepare(pid_record.object_uuid, presentation_id=presentation.name)
    else:
        abort(404, 'Record with PID {}:{} not found'.format(pid_type, pid_type))


@blueprint.route('/prepare/<string:record_uuid>/<string:presentation_id>/', methods=('POST',))
@with_presentations
@pass_presentation
#@login_required
def prepare(record_uuid: str, presentation: Presentation):
    p = None

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
        'current_login_ip': str(current_user.current_login_ip),
        'roles': [{'id': role.id, 'name': role.name} for role in current_user.roles]
    }
    user_meta.update(profile_meta)
    headers = {k: v for k, v in request.headers}

    try:
        eng_uuid = p.prepare(record_uuid, user_meta, headers)
        return jsonify({'job_id': eng_uuid})
    except WorkflowsPermissionError as e:
        abort(403, e)
    except WorkflowDefinitionError:
        abort(400, 'There was an error in the {} workflow definition'.format(p.name))


@blueprint.route('/status/<string:eng_uuid>/')
@with_presentations
@pass_engine
@login_required
def status(engine: WorkflowEngine):
    object = engine.objects[-1]
    return jsonify({'status_id': object.status.value,
                    'status': ObjectStatus.labels[object.status.value],
                    'created': object.created,
                    'modified': object.modified})


@blueprint.route('/download/<string:eng_uuid>/')
@with_presentations
@pass_engine
@login_required
def download(engine: WorkflowEngine):
    object = engine.objects[-1]
    return jsonify({'location': object.data})
