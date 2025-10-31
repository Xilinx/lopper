.. _openamp-linux-host-workflow:

OpenAMP Linux Host Workflow
===========================

This chapter focuses on producing the Linux APU view of an OpenAMP-capable
system. Review the shared prerequisites in :doc:`../index` before running the
Linux-specific commands to ensure the Domain YAML, translation LOPs, and
carve-out definitions are already in place.

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

- Shared OpenAMP prerequisites: :doc:`../index`.
- Remote firmware workflow: :doc:`../zephyr/index`.
- Bare-metal header export workflow: :doc:`../baremetal/index`.
- FreeRTOS workflow: :doc:`../freertos/index`.
