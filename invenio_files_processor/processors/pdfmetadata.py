# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Implementations of different file processors."""

from __future__ import absolute_import, print_function

from io import open

import requests
import textract
from flask import abort, current_app
from invenio_files_rest.models import FileInstance
from invenio_grobid.api import process_pdf_stream
from invenio_grobid.errors import GrobidRequestError
from invenio_grobid.mapping import tei_to_dict


def can_process(object_version):
    """Check if given file can be processed by the processor.

    :param object_version: A ObjectVersion object representing the files
    :type object_version: invenio_files_rest.models.ObjectVersion
    """
    # For now, we only check the filetype
    return object_version.mimetype == 'application/pdf'


OpenAIRE_MINING_URL = 'http://mining.openaire.eu/openaireplus/analyze'


def _extract_project_info(fulltext, setting):
    """Extract the project information using the OpenAIRE mining service.

    :param fulltext: The fulltext string
    :type fulltext: str
    :param setting: The setting of the mining service.
    :type setting: dict

    The `setting` parameter is a dictionary with two fields.

    - `datacitations`: 'on' or 'off' (default: 'off')
    - `classification`: 'on' or 'off' (default: 'off')

    See http://mining.openaire.eu/openaireplus/analyze for details.
    """
    try:
        resp = requests.post(OpenAIRE_MINING_URL, data=[
                             ('document', fulltext),
                             ('datacitations', 'on' if setting.get(
                                 'datacitations') else 'off'),
                             ('classification', 'on' if setting.get(
                                 'classification') else 'off')
                             ])
        return resp.json()
    except ConnectionError:
        current_app.logger.warning(
            'Cannot connect to OpenAIRE mining service',
            exc_info=True
        )
        abort(500)


def process(object_version, setting={}):
    """Process the file with Grobid.

    :param object_version: A ObjectVersion object representing the files
    :type object_version: invenio_files_rest.models.ObjectVersion
    :param setting: The processor configuration.
    :type setting: dict

    An example of ``setting`` is as follows.

    .. code-block:: python

       {
           'grobid': True,
           'openaire': {
               'datacitations': 'on',
               'classification': 'on'
           }
       }
    """
    file_instance = FileInstance.get(object_version.file_id)
    xml = None
    if setting.get('grobid'):
        with open(file_instance.uri, 'rb') as pdf_file:
            try:
                xml = process_pdf_stream(pdf_file)
            except GrobidRequestError:
                current_app.logger.warning(
                    'grobid request fails when processing the file {}.'.format(
                        object_version.version_id),
                    exc_info=True
                )
                abort(500)
        r = tei_to_dict(xml)

    project_info = None
    if 'openaire' in setting:
        fulltext = textract.process(file_instance.uri, extension='pdf')
        project_info = _extract_project_info(fulltext, setting['openaire'])

    # showing the JSON for debugging
    metadata = dict(
        title=r.get('title'),
        description=r.get('abstract'),
        keywords=[it['value']
                  for it in r['keywords']] if 'keywords' in r else None,
        creators=[dict(
            name=it['name'],
            affiliation=it['affiliations'][0]['value']
            if len(it['affiliations']) else None
        ) for it in r['authors']] if 'authors' in r else None,
        project_info=project_info
    )

    return metadata
