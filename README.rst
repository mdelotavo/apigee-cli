==========
apigee-cli
==========

|Python version| |Downloads| |License|


**TL;DR**
--------
For a more stable experience, install version **0.53.11 or earlier**:

::

   pip install apigeecli==0.53.11


Versions **0.54 and above** are **maintenance-only releases** (refactoring and ad-hoc fixes).  
See the `Mirror`_ repository for the current maintained source code.


Maintenance Status
------------------
**This tool is no longer actively maintained.**

It remains usable, but no new features or fixes are planned.


Authentication Support Notice
------------------------------
We primarily use and test with **SSO**.

**Basic** and **MFA** authentication may still work, but they are **no longer tested or guaranteed**.


Overview
--------
The Apigee Edge command-line interface is an **unofficial Python CLI** built to simplify and automate Apigee API usage.

- Originally built for **Darumatic clients**
- Designed for **Apigee Edge**, now being used during transition toward **Apigee X (ApigeeX)**
- Supports common API management workflows via CLI


Recently Tested (Post-Refactor / Pre-Deprecation)
------------------------------------------------
The following commands and features were validated during final updates and refactoring:


Authentication

- SSO login flow (primary supported method)
- Basic auth (not actively tested)
- MFA auth (not actively tested)


Core Functionality

- Organization and environment targeting
- API proxy deployments
- API proxy undeployments
- Revision listing and management
- Product and app queries (read operations)


CLI Behavior

- Argument parsing and command structure
- Error handling for common API failures
- Config/environment switching


Deprecation
-----------
This tool was designed for **Apigee Edge**, which is being phased out in favor of **Apigee X (ApigeeX)**.

- No major enhancements for ApigeeX compatibility are planned
- Some commands may not fully align with ApigeeX APIs
- Long-term usage is **not recommended for new projects**


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

------------
Installation
------------

The easiest way to install apigee-cli is to use `pip`_ in a ``virtualenv``::

    $ pip install apigeecli

or, if you are not installing in a ``virtualenv``, to install globally::

    $ sudo pip install apigeecli

or for your user::

    $ pip install --user apigeecli

If you have the apigee-cli installed and want to upgrade to the latest version you can run::

    $ pip install --upgrade apigeecli

---------------
Getting Started
---------------

Before using apigee-cli, you need to tell it about your Apigee Edge credentials. You can do this in three ways:

* Environment variables
* Config file
* Command-line arguments

The steps below show how to use command-line arguments to configure your Apigee Edge credentials.

^^^^^^^^^^^^^^^^^^^^
Basic authentication
^^^^^^^^^^^^^^^^^^^^

::

    $ apigee configure -P default -u MY_EMAIL -p MY_PASS -o MY_ORG -mfa '' -z '' --no-token --prefix ''

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Multi-factor authentication (MFA)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    $ apigee configure -P default -u MY_EMAIL -p MY_PASS -o MY_ORG -mfa MY_KEY -z '' --no-token --prefix ''

^^^^^^^^^^^^^^^^^^
SSO authentication
^^^^^^^^^^^^^^^^^^

::

    $ apigee configure -P default -u MY_EMAIL -p none -o MY_ORG -mfa '' -z MY_ZONENAME --no-token --prefix ''

If you are not currently signed in by your identity provider, you will be prompted to sign in::

    $ apigee apis list
    SSO authorization page has automatically been opened in your default browser.
    Follow the instructions in the browser to complete this authorization request.

    If your browser did not automatically open, go to the following URL and sign in:

    https://{zoneName}.login.apigee.com/passcode

    then copy the Temporary Authentication Code.

    Please enter the Temporary Authentication Code:

``zoneName`` will be the ``Identity zone name`` you previously configured.

Refer to the official Apigee documentation to learn more about how to `Access the Edge API with SAML`_.

^^^^^^^^^^^^^^^^^^^^^^^^
Testing your credentials
^^^^^^^^^^^^^^^^^^^^^^^^

Run the following command to get a list of API proxies in your ``default`` Apigee organization::

    $ apigee apis list
    ["helloworld", "oauth"]

^^^^^^^^^^^^^^^
Troubleshooting
^^^^^^^^^^^^^^^

If you encounter issues with commands, check the log file for detailed debug information and error messages::

    ~/.apigee/exceptions.log

This file can help diagnose installation problems, missing dependencies, or errors related to Apigee Edge.

You can also use the verbose flags ``-v`` or ``-vv`` with commands to see more detailed request information.

.. -------------
.. Running Tests
.. -------------

.. This project uses `unittest` for testing its codebase. In order to run the tests, you will need to install the `coverage.py` tool. You can install it using pip:

.. .. code-block:: bash

..    pip3 install coverage

.. Once `coverage.py` is installed, you can run the tests using the `runtests` script:

.. .. code-block:: bash

..    ./runtests

.. This script will run all the tests in the `tests` directory and generate a coverage report.

Code Formatting
---------------

You can use the following helper alias to format the codebase using ``yapf``:

::

   alias fmt='python -m yapf -ir --style="{based_on_style: pep8, column_limit: 160, continuation_indent_width: 2, split_before_first_argument: false, split_arguments_when_comma_terminated: false, split_before_logical_operator: false, allow_split_before_dict_value: false, coalesce_brackets: true, dedent_closing_brackets: true, blank_lines_around_top_level_definition: 2}"'

Then run:

::

   fmt apigee/

------------
Getting Help
------------

* `Apigee Product Documentation`_

----------
More Links
----------

* `GitHub`_
* `Mirror`_
* `Python Package Index (PyPI)`_

For further questions, feel free to contact us at hello@darumatic.com.

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

.. |Python version| image:: https://img.shields.io/pypi/pyversions/apigeecli
   :target: https://pypi.org/project/apigeecli/

.. |PyPI Version| image:: https://badge.fury.io/py/apigeecli.svg
   :target: https://badge.fury.io/py/apigeecli

.. |Downloads| image:: https://pepy.tech/badge/apigeecli
   :target: https://pepy.tech/project/apigeecli

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
