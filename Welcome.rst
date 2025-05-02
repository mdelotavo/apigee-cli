==========
apigee-cli
==========

.. warning::

   This tool is no longer actively maintained.

The Apigee Edge command-line interface is an unofficial Python command-line tool built to simplify and automate Apigee Edge API usage, with support for SSO, MFA, and basic authentication.

Initially developed for Darumatic clients, this project remains available as a working proof of concept, proven reliable in production CI/CD pipelines. The custom plugins feature will remain functional even if Apigee Edge APIs stop working.

I have created private forks for clients, where I continued to add features, fixes, and unit tests. However, I do not intend to maintain this public version. Feel free to explore and learn from the code.

If you’re up for a challenge, try updating the code to work with Apigee X (ง•_•)ง

.. note::

   **apigee-cli** is highly experimental and is not affiliated with Apigee or Google.

-----------------------------------------
Why use this instead of the official tool
-----------------------------------------

The `official Apigee CLI`_ is powerful and may suit your needs. However, I built this version to better support our CI/CD processes, self-service operations, and DevOps workflows that are difficult to manage with the official tool.

----------
Disclaimer
----------
This is not an officially supported Google product.


.. _`official Apigee CLI`: https://github.com/apigee/apigeetool-node

.. |Upload Python Package badge| image:: https://github.com/mdelotavo/apigee-cli/workflows/Upload%20Python%20Package/badge.svg
    :target: https://github.com/mdelotavo/apigee-cli/actions?query=workflow%3A%22Upload+Python+Package%22
.. |Python package badge| image:: https://github.com/mdelotavo/apigee-cli/workflows/Python%20package/badge.svg
    :target: https://github.com/mdelotavo/apigee-cli/actions?query=workflow%3A%22Python+package%22
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
.. |PyPI| image:: https://img.shields.io/pypi/v/apigeecli
    :target: https://pypi.org/project/apigeecli/
.. |License| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
.. _`Apigee Product Documentation`: https://apidocs.apigee.com/management/apis
.. _`Permissions reference`: https://docs.apigee.com/api-platform/system-administration/permissions
.. _`Add permissions to testing role`: https://docs.apigee.com/api-platform/system-administration/managing-roles-api#addpermissionstotestingrole
.. _pip: http://www.pip-installer.org/en/latest/
.. _`Universal Command Line Interface for Amazon Web Services`: https://github.com/aws/aws-cli
.. _`The Apigee Management API command-line interface documentation`: https://darumatic.github.io/apigee-cli/index.html
.. _`GitHub`: https://github.com/darumatic/apigee-cli
.. _`Python Package Index (PyPI)`: https://pypi.org/project/apigeecli/
.. _`Access the Edge API with SAML`: https://docs.apigee.com/api-platform/system-administration/using-saml

.. _`Commands cheatsheet`: https://github.com/mdelotavo/apigee-cli-docs
.. _`Using SAML with automated tasks`: https://github.com/mdelotavo/apigee-cli-docs
.. _`Tabulating deployments`: https://github.com/mdelotavo/apigee-cli-docs
.. _`Tabulating resource permissions`: https://github.com/mdelotavo/apigee-cli-docs
.. _`Troubleshooting`: https://github.com/mdelotavo/apigee-cli-docs
.. _`Mirror`: https://github.com/mdelotavo/apigee-cli

.. _`Apigee CI/CD Docker releases`: https://hub.docker.com/r/darumatic/apigee-cicd
