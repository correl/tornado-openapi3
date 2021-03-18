.. Tornado OpenAPI 3 documentation master file, created by
   sphinx-quickstart on Thu Feb 25 23:03:16 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tornado OpenAPI 3
=================

.. image:: https://travis-ci.com/correl/tornado-openapi3.svg?branch=master
    :target: https://travis-ci.com/correl/tornado-openapi3
.. image:: https://codecov.io/gh/correl/tornado-openapi3/branch/master/graph/badge.svg?token=CTYWWDXTL9
    :target: https://codecov.io/gh/correl/tornado-openapi3
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


Tornado OpenAPI 3 request and response validation library.

Provides integration between the `Tornado`_ web framework and `Openapi-core`_
library for validating request and response objects against an `OpenAPI 3`_
specification.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation

.. toctree::
   :maxdepth: 2
   :caption: Usage

   handling_incoming_requests
   testing_api_responses

.. toctree::
   :maxdepth: 2
   :caption: Modules

   handler
   testing
   requests
   responses
   types


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _OpenAPI 3: https://swagger.io/specification/
.. _Openapi-core: https://github.com/p1c2u/openapi-core
.. _Tornado: https://www.tornadoweb.org/
