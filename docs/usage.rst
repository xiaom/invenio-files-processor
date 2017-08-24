..
    This file is part of Invenio.
    Copyright (C) 2017 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.


Usage
=====

.. automodule:: invenio_files_processor

Currently, the module comes with the following processors.

- `pdfmetadata`: a pdf metadata extractor


Using the `pdfmetadata` processor
---------------------------------

External services
~~~~~~~~~~~~~~~~~

In the `pdfmetadata` processor, we use two external services `Grobid`_ and `OpenAIRE mining service`_.

To access a Grobid_ service, we may use docker to run it as a container.

.. code-block:: console

   $ docker run -t --rm -p 8080:8080 lfoppiano/grobid:0.4.1


To access the `OpenAIRE mining service`_, make sure the endpoint is available.


POST request
~~~~~~~~~~~~

We can use the processor to process a file by sending a ``POST`` request
to the URL endpoint ``/filesprocessor/pdfmetadata/{version_id}``, where ``version_id`` is the version id of the file.

We can also post a configuration to the processor.
The configuration controls whether to use the `Grobid`_ service or
the `OpenAIRE mining service`_.
An example configuration is as follows.

.. code-block:: python

    {
        'grobid': True,             # using grobid service
        'openaire': {               # using OpenAIRE mining service
            'datacitations': 'on',  # turn on the dataciations option
            'classification': 'on'  # turn on the classification option
        }
    }


A sample response is as follows.

.. code-block:: json

    {
    "creators": [
        { "affiliation": "BioSense Institute", "name": "Georgios Niarchos" },
        { "affiliation": "BioSense Institute", "name": "Georges Dubourg" }
    ],
    "description": "paper description",
    "keywords": [
        "humidity passivation", "disposable sensors"
    ],
    "project_info": {
        "classification_info": [
        {
            "class": "[\"Science\",\"Physics\"]",
            "confidence": 0.714,
            "taxonomy": "DDClasses"
        },
        {
            "class": "[\"Technology\",\"Engineering\"]",
            "confidence": 0.688,
            "taxonomy": "DDClasses"
        }
        ],
        "datacitation_info": [],
        "funding_info": [
        {
            "EGI-related": false,
            "acronym": "INNOSENSE",
            "confidence": 1.64,
            "fund": "FP7",
            "grantid": "316191"
        }
        ]
    },
    "title": "Humidity Sensing Properties"
    }


.. _Grobid: https://grobid.readthedocs.io/en/latest/
.. _OpenAIRE mining service: http://mining.openaire.eu/openaireplus/analyze


Write your own files-processor
------------------------------

To implement a files-processor, we only need to implement two methods and declare the entry point.
We give an example on how to write your a Zip-file processor that returns the list of directory/files in the Zip-file.


Implement the API of filesprocessor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, create a file named ``zipmetadata.py`` under the directory ``invenio_files_processor/processors`` and implement the following two functions.

- ``can_process(object_version)`` returns a boolean value indicating whether the processor can process the given files.
  The ``object_version`` parameter is a :py:class:`invenio_files_rest.models.ObjectVersion` object and holds all information for accessing the files.
- ``process(object_version, setting={})`` returns a dictionary of extracted metadata. The optional ``setting`` parameter comes from the data associated with the POST request.

For the ``can_process(object_version)`` function, we only check the MIME type of the given file.

.. code-block:: python

    def can_process(object_version):
        return object_version.mimetype == 'application/zip'

For the ``process(object_version, setting={})`` function, we

.. code-block:: python

    def process(object_version, setting={}):
        file_instance = FileInstance.get(object_version.file_id)
        zip_info = None
        with ZipFile(file_instance.uri, 'r') as f:
            namelist = f.namelist()
            if setting.get('sorted'):
                return dict(filenames=sorted(namelist))
            return dict(filenames=namelist)


Register the processor
~~~~~~~~~~~~~~~~~~~~~~

Next, register the processor in the `entry_point` in `setup.py` and run ``python setup.py develop``.

.. code-block:: python

    entry_point={
        ...
        'invenio_files_processor.processors': [
            'pdfmetadata = invenio_files_processor.processors.pdfmetadata',
            'zipmetadata = invenio_files_processor.processors.zipmetadata'
        ]
        ...
    }

Test the processor
~~~~~~~~~~~~~~~~~~

Finally, we are ready to use the processor using the endpoint ``/filesprocessor/zipmetadata/{version_id}``.


Assume that we log in a local Zenodo instance (with the cookie session  of ``${SESSION_ID}``).
We upload a sample `zip file <https://zenodo.org/record/848817>`_ and post the request as follows.

.. code-block:: console

    $ export SESSION_ID='dc883331f06c7a20_59a0a1cc.hLROjrOY5RiuqWmB065TYDKFgRQ'
    $ export VERSION_ID='c3b50b2f-d10f-4db1-bae5-52fe17350c97'
    $ curl -d '{"sorted":true}' \
    -H "Content-Type: application/json" \
    -H "Cookie: session=${SESSION_ID}" \
    -X POST \
    http://127.0.0.1:5000/filesprocessor/zipmetadata/${VERSION_ID}

The reponse of the request is as follows.

.. code-block:: python

    {
        "filenames": [
            "__MACOSX/",
            "__MACOSX/iRF_analyses/",
            "__MACOSX/iRF_analyses/data/",
            "__MACOSX/iRF_analyses/data/._rfSampleSplitNoise.Rdata",
            "iRF_analyses/",
            "iRF_analyses/.Rhistory",
            "iRF_analyses/README.md",
            "iRF_analyses/data/",
            "iRF_analyses/data/enhancer.Rdata",
            "iRF_analyses/data/rfSampleSplitNoise.Rdata",
            "iRF_analyses/data/splicing.Rdata",
            "iRF_analyses/enhancer.R",
            "iRF_analyses/simulations/",
            "iRF_analyses/simulations/booleanSimulations.R",
            "iRF_analyses/simulations/booleanUtilities.R",
            "iRF_analyses/simulations/enhancerSimulations.R",
            "iRF_analyses/simulations/makeMat.R",
            "iRF_analyses/splicing.R"
        ]
    }


