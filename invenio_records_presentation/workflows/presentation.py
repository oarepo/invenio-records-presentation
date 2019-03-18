# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CESNET.
#
# Invenio Records Presentation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

""" Example Presentation workflow."""
from invenio_workflows import WorkflowEngine

from invenio_records_presentation.api import PresentationOutputFile
from invenio_records_presentation.workflows import presentation_workflow_factory


def print_extra_data(obj, eng: WorkflowEngine):
    print(obj.extra_data)
    return obj


def print_data(obj, eng: WorkflowEngine):
    print(obj.data)
    return obj


def create_example_file(obj, eng: WorkflowEngine):
    # creates an example input file and passes a path to it
    input = obj.scratch.create_file(task_name='example_input')
    with open(input, 'w') as tf:
        tf.write("example file\n")

    obj.data = input
    return obj


def transform_example_file(obj, eng: WorkflowEngine):
    input_data = ''
    try:
        with open(obj.data, 'r') as input:
            input_data = input.read()
    except OSError:
        eng.abort()  # Cannot read input data, abort workflow execution

    output = obj.scratch.create_file(task_name='example_output')
    with open(output, 'w') as tf:
        tf.write(input_data.title())

    obj.data = output
    return obj


def output_example_file(obj, eng: WorkflowEngine):
    obj.data = PresentationOutputFile(path=obj.data,
                                      mimetype='text/plain',
                                      filename='example.txt')
    return obj


example = presentation_workflow_factory(task_list=[
    print_extra_data,
    create_example_file,
    print_data,
    transform_example_file,
    output_example_file,
])
