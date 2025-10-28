.. _openamp-zephyr-remote-workflow:

OpenAMP Remote Firmware Workflow
================================

After the shared prerequisites in ``docs/amd/openamp/source/index.rst`` are in
place, generate the Zephyr remote domain by running ``gen_domain_dts`` for the
target processor.

Example Command
---------------

The snippet below targets a Zephyr build for ``cortexr52_0`` (supported on
Versal 2VE and 2VM devices). Update processor identifiers and paths to match
your platform.

.. code-block:: bash

   lopper -f --enhanced -O ./output \
     -i domain/openamp-domain.yaml \
     -i lopper/lops/lop-xlate-yaml.dts \
     system-top.dts \
     ./output/system-remote.dts \
     -- gen_domain_dts cortexr52_0 zephyr_dt

The resulting DTS captures the remote (RPU) view of the OpenAMP channel and is
ready for Zephyr board integration.

Additional Steps
----------------

- Confirm the generated DTS contains the expected ``reserved-memory`` entries and mailbox endpoints for each OpenAMP channel.
- For bare-metal usage, follow ``docs/amd/baremetal/source/index.rst`` after generating the remote DTS.
- For FreeRTOS builds, consult ``docs/amd/freertos/source/index.rst``.
