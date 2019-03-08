# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" Presentation workflow."""

from .presentation import PresentationWorkflow


def presentation_workflow_factory(task_list: list) -> PresentationWorkflow:
    return PresentationWorkflow(task_list=task_list)


__all__ = ('PresentationWorkflow', 'presentation_workflow_factory')
