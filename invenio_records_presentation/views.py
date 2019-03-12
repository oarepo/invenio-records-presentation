# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Blueprint definitions."""

from __future__ import absolute_import, print_function

from flask import Blueprint, jsonify, abort, request, Response
from flask_login import current_user
from invenio_workflows import WorkflowEngine

from .api import Presentation
from .errors import PresentationNotFound
from .proxies import current_records_presentation

blueprint = Blueprint(
    'invenio_records_presentation',
    __name__,
    url_prefix='/presentation'
)
"""Blueprint used for loading templates and static assets

The sole purpose of this blueprint is to ensure that Invenio can find the
templates and static files located in the folders of the same names next to
this file.
"""

@blueprint.route("/record/<string:record_uuid>/<string:presentation_id>/")
def prepare(record_uuid: str, presentation_id: str):
    try:
        p: Presentation = current_records_presentation.get_presentation(presentation_id)
        user_meta = {
            'id': current_user.id,
            'email': current_user.email,
            'current_login_ip': str(current_user.current_login_ip)
        }
        headers = {k: v for k, v in request.headers }
        async_result = p.prepare(record_uuid, user_meta, headers)
        return jsonify({'jobid': async_result.id})
    except PresentationNotFound:
        abort(400)

@blueprint.route("/status/<string:eng_uuid>/")
def status(eng_uuid: str):
    engine = WorkflowEngine.from_uuid(eng_uuid)
    return jsonify(engine.objects[0].status)


@blueprint.route("/download/<string:eng_uuid>/")
def download(eng_uuid):
    engine = WorkflowEngine.from_uuid(eng_uuid)
    return Response(engine.objects[0].data)
