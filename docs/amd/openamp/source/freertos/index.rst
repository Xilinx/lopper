.. _openamp-freertos-workflow:

OpenAMP FreeRTOS Workflow
=========================

FreeRTOS device and firmware projects rely on the same OpenAMP configuration
steps described in :doc:`../index`. Once the Domain YAML and system tree expose
the OpenAMP relations, export the shared channel header that the FreeRTOS
application consumes.

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

- Confirm that ``amd_platform_info.h`` lists the vrings, carve-outs, and mailbox
  endpoints expected by the FreeRTOS channel configuration.
- When multiple channels exist, repeat the export with the appropriate domain
  selections and verify each header lines up with the firmware project.

Related Material
----------------

- Shared OpenAMP prerequisites: :doc:`../index`.
- Linux host workflow: :doc:`../linux/index`.
- Zephyr remote workflow: :doc:`../zephyr/index`.
- Baremetal workflow: :doc:`../baremetal/index`.
