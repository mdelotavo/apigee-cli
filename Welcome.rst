==========
apigee-cli
==========

.. warning::

   This tool is no longer actively maintained.

------------------
Maintenance Status
------------------
**This tool is no longer actively maintained.**

It remains usable, but no new features or fixes are planned.

If you encounter any broken versions, please report them via the `Forked`_ repository, thanks.


------------------------------
Authentication Support Notice
------------------------------
We exclusively use **SSO**.

**Basic** and **MFA** authentication may still work, but they are **no longer tested or guaranteed**.


--------
Overview
--------
The Apigee Edge command-line interface is an **unofficial Python CLI** built to simplify and automate Apigee API usage.

- Originally built for **Darumatic clients**
- Designed for **Apigee Edge**
- Supports common API management workflows


-----------
Deprecation
-----------
This tool was designed for **Apigee Edge**, which is being phased out in favor of **Apigee X (ApigeeX)**.

No major enhancements for ApigeeX compatibility are planned


--------------
Recommendation
--------------
For new implementations, consider:

- Official Google Cloud / Apigee tooling
- Direct ApigeeX API usage
- Modern CI/CD integrations

This CLI is best suited for:

- Legacy automation
- Transitional environments
- Existing scripts that depend on it


----------
Disclaimer
----------

This tool is not affiliated with Apigee or Google and is highly experimental.

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
.. _`Forked`: https://github.com/mdelotavo/apigee-cli
.. _`Apigee CI/CD Docker releases`: https://hub.docker.com/r/darumatic/apigee-cicd