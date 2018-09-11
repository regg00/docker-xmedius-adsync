Module:   AD Sync Tool

=============================
= Installation Instructions =
=============================

First Installation/Configuration
--------------------------------
See the dedicated Article "Synchronizing Users from Active Directory".
(https://support.xmedius.com/hc/en-us/articles/203824596)

Upgrade
-------
  1. Backup all configuration files (located in <adsync_home>/config) to a temporary folder.
  2. If you previously customized the file <addync_home>/libs/http/attributes_modifier.py,
     Backup this file as well to a temporary folder.
  3. Decompress the zip file to the <adsync_home> folder, overwrite all the files.
  4. Restore the configuration files copied in step 1.
  5. Restore the attributes_modifier.py file copied in step 2.

If you need to perform further configurations after the upgrade, see the article referenced above.

===========
= History =
===========

1.0.4   The AD Sync Tool can be configured to disable automatic sending of password setup emails to
        newly created users (TT#21728).

1.0.1   Initial Public Release