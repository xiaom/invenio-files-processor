# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio module that adds more fun to the platform."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function
from io import open
from flask import Blueprint, request, jsonify, current_app
from invenio_db import db
from invenio_files_rest.models import ObjectVersion, FileInstance
from .proxies import current_processor

blueprint = Blueprint(
    'invenio_files_processor',
    __name__,
    url_prefix='/fileprocessor',
    template_folder='templates',
    static_folder='static',
)

@blueprint.route("/<filetype>/<version_id>", methods=['POST'])
def extract_pdf_metadata(filetype=None, version_id=None):
    file_id = ObjectVersion.query.filter_by(version_id=version_id).one().file_id
    file_instance = FileInstance.get(file_id)

    for plugin in current_processor.iter_processors():
        if plugin.can_process(filetype):
            try:
                with open(file_instance.uri,'rb') as f:
                    metadata = plugin.process(f)
                return jsonify(metadata)
            except Exception:
                # TODO: handle different types of exceptions
                current_app.logger.warning(
                    ('File processor failed for {uri}'.format(uri=file_instance.uri)),
                    exc_info=True
                )
    return jsonify(None)
