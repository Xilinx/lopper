.. _openamp-baremetal-workflow:

OpenAMP Baremetal Workflow
==========================

OpenAMP header and carve-out generation for bare-metal projects relies on the
shared prerequisites described in :doc:`../index`. Once the Domain YAML and
system tree contain the OpenAMP relations, run the following sequence to export
the firmware header that pairs with the generated device trees.

Header Export
-------------

Set ``ESW_MACHINE`` to the target processor (for example, ``psv_cortexr5_0`` for
Versal Gen 1 or ``psu_cortexr5_0`` for ZynqMP) and invoke the OpenAMP assist in
header-only mode:

.. code-block:: bash

   ESW_MACHINE=psv_cortexr5_0
   lopper -O -f -v --enhanced --permissive \
     -O . ${CONFIG_DTFILE} -- openamp --openamp_header_only \
     --openamp_output_filename=amd_platform_info.h \
     --openamp_remote=${ESW_MACHINE}

Validation
----------

- Confirm that ``amd_platform_info.h`` lists the expected vring, carve-out, and
  mailbox definitions from the Domain YAML.
- When multiple channels exist, repeat the header export with the relevant
  domain selections and ensure each header matches the domain topology.

Related Material
----------------

- Shared OpenAMP prerequisites: :doc:`../index`.
- Linux host workflow: :doc:`../linux/index`.
- Zephyr remote workflow: :doc:`../zephyr/index`.
- FreeRTOS workflow: :doc:`../freertos/index`.
