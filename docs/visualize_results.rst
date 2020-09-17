.. _visualize:

==================
Visualize Results
==================

Simulation results can be visualized using the dashboard. To start the dashboard:

.. code-block:: console

    $citam dash

Please note that if the **CITAM_RESULT_PATH** environment variable is not set, the
--result option must be provided to use the dashboard.

To visualize more than 1 simulation result with the dashboard, set the **CITAM_RESULT_PATH**
as a parent directory from which all results subdirectories are accessible.

To set your environment varialbe, a quick web search should provide instructions
on how to dot it. For more customization options, please see the global configuration page.

----------------------
The Main Results Page
----------------------

The dashboard displays a list all of the simulations found in the specified results location.
To view data for a given simulation, click on "view details".

----------------------
The Details Page
----------------------

This details page has two tabs: Statistics and Visualizer.

The Statistics Tab
"""""""""""""""""""

The statistics tab show key statistical information about the simulation results and
a few plots showing contact statistics.

It also show a floorplan-based heatmap showing where most contact events take place.

The Visualizer Tab
"""""""""""""""""""

The visualiation offers an interactive way to explore the time-dependent contact
data and trajectories of each agent.