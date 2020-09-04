=========
Tutorial
=========

**Contents**
    + Introduction
    + Adding a facility
    + Generating the navigation network
    + Running a simulation
    + Visualizing results
    + Exploring policies

Introduction
--------------

This is a brief tutorial on how to use CITAM.

CITAM can assist in the management of large indoor facilities in the context of
an airborne pandemic like COVID-19 and help make policy decisions to mitigate
indoor transmission risks within their facilities.

This tutorial assumes that you have already downloaded and installed CTIAM. To verify
that CITAM has been installed properly, you can run the followin command:

.. code-block:: console

    $ citam -h


Adding a facility
------------------

To determine the number of agents and the paths those agents can navigate in an indoor
facility, both the SVG and CSV files of floor plans of the facility are needed.
Both files must be ingested into CITAM.

For this tutorial, we will use example files provided with CITAM in the examples/
directory. Please download those files from GitHub if you don't have them.

The examples that we will use can be found in the **examples** and **basic_example**
folders  located inside the main citam folder. They are named **TFI.csv** and **TFI.svg**

Before ingesting, let's take a look at the contents of TFI.svg. Use a text editor
to open the file and inspect it's contents. You can also visualize the floorplan
using your favorite SVG viewer. An image is shown below for your reference.


To ingest examples floors plans TFI.svg and TFI.csv into TF1 folder, use the citam command below:

.. code-block:: console

    $ citam engine ingest TF1 --csv ../examples/basic_examples/TFI.csv --map ../examples/basic_example/TFI.svg -v


The -v argument in the command above will give users detailed explanation of any command process.

After ingesting, the ingested floor plan of Fig. 1 will have been rendered by citam and it will look as shown in Fig. 2.


After successfully ingesting, ingested floorplans must be exported into another named file. Suppose ingested floorplans is to be exported into a file named **FirstOutputFile**, then use the citam **export-floorplan** command below:

.. code-block:: console

    $ citam engine export-floorplan TF1 –outputfile ../../FirstOutputFile.svg -v

The exported floor plan must be edited to include important features that are missing on the floorplan. Examples of such features can be a wall or an aisle. For the example shown in Fig. 2, Inkscape or any other app that can be used to edit svg files can be used to edit ingested svg files in spaces shown in Fig. 3. In Fig. 3, example of a missing feature is a wall that must exist between office segments.


An example of the floor plan after using Inkscape to include wall features is as shown in Fig. 4.



A video of how Inkscape is used to insert the wall features can be found at:

In Fig. 4, a door is inserted between the wall feature inserted after office segment 1 and office segment 2. The door is called 'Aisle 213'.

Another created file can be used to store edited floor plan. Suppose the floorplan will be updated into another file named **FirstOutputFileEdited**; then use the citam command below:

.. code-block:: console

    $ citam engine update-floorplan TF1 -m ../../FirstOutputFileEdtied.svg -v


Generating the Navigation Network
------------------------------------


The edited floorplan can then be used to build floorplan networks. Floorplan networks can be built into the TF1 folder using:

.. code-block:: console

    $ citam engine build-navnet TF1 0

Please note that you only have to go through this process (ingestion and navnet
only once per facility per floor)

Running a simulation
---------------------

After generating the navigation network, users can then simulate and test
 different scenarios for their particular facility.

Before running a simulation, users must create an input file in JSON format. Please
create a new folder to run the simulation. We will refer to this folder as
SIMULATION_FOLDER. Now open your favorite text editor and create a new file called
sim_inputs.json inside SIMULATION_FOLDER.

Below is an example input file.

::

    {
        "meetings_file": "meetings.json",
        "scheduling_policy_file": "scheduling_policy.json",
        "facility_name" : "TF1",
        "simulation_name" : "test_run_1",
        "floors" : ["0"],
        "entrances" : [ {"name":"AISLE213", "floor": 0}],
        "daylength" : 1800,
        "buffer" : 100,
        "n_agents" : 20,
        "occupancy_rate" : null,
        "floorplan_scale": 0.08333333333,
        "contact_distance": 6,
        "shifts": [{"name":"1", "start_time": 0, "percent_workforce": 1.0}]
    }

Copy and paste the contents above in your input file, then save and close the file.

Now navigate to your SIMULATION_FOLDER and start a new simulation using:

.. code-block:: console

    $ citam engine run sim_inputs.json

Visualizing Results
---------------------


Exploring Policies
--------------------

