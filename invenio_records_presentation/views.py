# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Blueprint definitions."""

from __future__ import absolute_import, print_function

from flask import Blueprint, jsonify, abort
from invenio_workflows import workflows

from invenio_records_presentation.api import Presentation
from invenio_records_presentation.proxies import current_records_presentation

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
    except AttributeError:
        abort(400)

    w = p.workflow()
    return jsonify(dict(workflows))


@blueprint.route("/status/<string:task_id>/")
def status(task_id: str):
    return jsonify(dict(workflows))


@blueprint.route("/download/<string:task_id>/")
def download(task_id):
    return jsonify({})
