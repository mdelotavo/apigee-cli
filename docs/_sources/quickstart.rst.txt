Quickstart
==========

.. _`Getting Started`:

---------------
Getting Started
---------------

Before using apigee-cli, you need to tell it about your Apigee Edge credentials. You
can do this in three ways:

* Environment variables
* Config file
* Command-line arguments

The quickest way to get started is to run the ``apigee configure`` command::

    $ apigee configure
    Apigee username (email) []: MY_EMAIL
    Apigee password []: MY_PASS
    Apigee MFA key (optional) []: MY_KEY
    Identity zone name (to support SAML authentication) []:
    Use OAuth, no MFA (optional)? [y/N]: n
    Default Apigee organization (recommended) []: MY_ORG
    Default team/resource prefix (optional) []:

You may not need to input anything for some of these prompts. In these cases, simply press ``enter`` to skip.

You can also do the same thing using command-line arguments::

    $ apigee configure -P default -u MY_EMAIL -p MY_PASS -o MY_ORG -mfa '' -z '' --no-token --prefix ''

You may need to specify empty strings as above. Also note the ``--prefix`` option. This option
will filter the output of some commands, such as the ``list`` type commands, by the prefix which may be useful to some people,
but if you want to avoid confusion just keep this value empty. You can also explicitly specify the ``--prefix``
for those commands if you need it on the fly.


To use environment variables, do the following::

    $ export APIGEE_USERNAME=MY_EMAIL
    $ export APIGEE_PASSWORD=MY_PASS
    $ export APIGEE_MFA_SECRET=MY_KEY
    $ export APIGEE_ZONENAME=MY_ZONENAME
    $ export APIGEE_IS_TOKEN=BOOL
    $ export APIGEE_ORG=MY_ORG
    $ export APIGEE_CLI_PREFIX=MY_PREFIX


To use the configuration file, create an INI formatted file like this::

    [default]
    username = MY_EMAIL
    org = MY_ORG
    mfa_secret = MY_KEY
    prefix = MY_PREFIX
    password = MY_PASS

    [produser]
    org = MY_ORG
    username = MY_EMAIL
    password = MY_PASS
    mfa_secret = MY_KEY

and place it in ``~/.apigee/credentials``.

As you can see, you can have multiple ``profiles`` defined in the configuration file. You can then specify which
profile to use by using the ``-P/--profile`` option. If no profile is specified
the ``default`` profile is used.

^^^^^^^^^^^^^^^^^^^^^^^^^
Using SAML authentication
^^^^^^^^^^^^^^^^^^^^^^^^^
If you specified an ``Identity zone name (to support SAML authentication)`` during setup,
the CLI will automatically use SAML authentication.
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

-------------------------------
Using SAML with automated tasks
-------------------------------
The CLI also supports machine users as described in `Using SAML with automated tasks`_ when SAML is enabled
to support automation for common development tasks, such as test automation or Continuous Integration/Continuous Deployment (CI/CD).

To tell the CLI that the current user ``--profile`` is a machine user and thus to not redirect you to an identity provider,
you can set the following environment variable like so::

    $ export APIGEE_CLI_IS_MACHINE_USER=true

To continue using an ordinary user, you will need to unset this variable or set it to ``false``.

Refer to the official Apigee documentation to learn more about identity zones: `SAML Overview`_.

------------------------
Deploy API Proxy bundles
------------------------
You can also deploy API proxy bundles to Apigee.

This command is an enhanced version of the Apigee API Proxy Deploy Tool.

It supports a bunch of useful features such as MFA, SAML, seamless deployments and automatic handling of ``missing`` and broken deployments.

.. code-block:: text

    $ apigee apis deploy -n API_NAME -e ENVIRONMENT -d DIRECTORY_WITH_APIPROXY

Some notable options::

    Deployment options: [mutually_exclusive]
                                    The deployment options
      -i, --import-only / -I, --no-import-only
                                    import only and not deploy
      -s, --seamless-deploy / -S, --no-seamless-deploy
                                    seamless deploy the bundle

--------------------------------
Cleaning up undeployed revisions
--------------------------------
If deploying via CI/CD you may end up with a lot of undeployed revisions. In this case, you can
make use of the ``clean`` command to delete all undeployed revisions.

.. code-block:: text

    $ apigee apis clean -n API_NAME

You can also specify to keep the last few revisions::

    $ apigee apis clean -n API_NAME --save-last INTEGER

To only show which revisions will be deleted but not actually delete anything, use the following option::

      --dry-run / --no-dry-run  show revisions to be deleted but do not delete

-------------
Push commands
-------------
Some commands support the ``push`` subcommand which combines API calls to manage the creation, update and sometimes deletion of resources using a single command.

Push commands read JSON from a file and can be invoked like so::

    $ apigee keyvaluemaps push -e ENVIRONMENT -f FILENAME

This will create the KVM if it does not exist, and update it if it does.


.. _`Apigee Product Documentation`: https://apidocs.apigee.com/management/apis
.. _`Permissions reference`: https://docs.apigee.com/api-platform/system-administration/permissions
.. _`Add permissions to testing role`: https://docs.apigee.com/api-platform/system-administration/managing-roles-api#addpermissionstotestingrole
.. _pip: http://www.pip-installer.org/en/latest/
.. _`Access the Edge API with SAML`: https://docs.apigee.com/api-platform/system-administration/using-saml
.. _`public plugins repository`: https://github.com/mdelotavo/apigee-cli-plugins
.. _`SAML Overview`: https://docs.apigee.com/api-platform/system-administration/saml-overview
.. _`Using SAML with automated tasks`: https://docs.apigee.com/private-cloud/v4.17.09/using-saml-automated-tasks
