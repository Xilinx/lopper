.. _openamp-linux-host-workflow:

OpenAMP Linux Host Workflow
===========================

This chapter focuses on producing the Linux APU view of an OpenAMP-capable
system. Review the shared prerequisites in ``docs/amd/openamp/source/index.rst``
before running the Linux-specific commands to ensure the Domain YAML,
translation LOPs, and carve-out definitions are already in place.

Generating the Linux Host View
------------------------------

Use the following command to create a Linux-focused device tree that includes
the OpenAMP host channel. Substitute processor identifiers and paths as needed.

.. code-block:: bash

   lopper -f --enhanced -O ./output \
     -i domain/openamp-domain.yaml \
     -i lopper/lops/lop-xlate-yaml.dts \
     -i lopper/lops/lop-a53-imux.dts \
     system-top.dts \
     ./output/system-linux.dts \
     -- gen_domain_dts psu_cortexa53_0 linux_dt

Key results:

- ``system-linux.dts`` retains nodes mapped to the Linux host domain and
  includes OpenAMP carve-outs, mailboxes, and ``remoteproc`` metadata.
- The generated DTS acts as the Linux-facing view that pairs with firmware
  running on the remote processor.

Related Material
----------------

- General OpenAMP prerequisites: ``docs/amd/openamp/source/index.rst``.
- Remote firmware workflow: ``docs/amd/zephyr/source/openamp_remote_workflow.rst``.
- Bare-metal header export workflow: ``docs/amd/baremetal/source/index.rst``.
- FreeRTOS workflow: ``docs/amd/freertos/source/index.rst``.
