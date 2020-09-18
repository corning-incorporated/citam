.. _getting_started:

================
Getting Started
================

CITAM works by creating a "virtual" facility analagous to the real facility
of interest. Therefore, the primary requirement is to have a map of each floor of each
facility of interest for ingestion (referred to as floorplan). Another requirement is to have metadata
available for each space in each floorplan. The example folder contains some example files for your review.
For a list of supported metadata information, please visit the input requirements section.

Please note that no actual tracking of visitors, employees or
other people take place. CITAM actually provides an alternative to that
approach allowing a simulation to be used to understand the implicatiosn of
various mitigation policy options. At its core, CITAM is an agent-based
modeling platform. However, CITAM implements special features that make it
possible to mimic daily activities in various indoor environments.

CITAM is available on GitHub.

---------------
Pre-requisites
---------------

* Python 3.x
* `NodeJS <(https://nodejs.org/en/download/>`_ (to use the dashboard)

You may already have Python and NodeJS installed. Check their version to make sure all pre-requisites are satisfied:

.. code-block:: console

  $ python --version    # must be 3.x
  $ node --version      # should be 12 or above
  $ npm --version       # should be 6 or above

---------------
How to Install
---------------

Clone from GitHub and install as follow:

.. code-block:: console

  $git clone https://github.com/corning-incorporated/citam.git
  $cd citam
  $pip install .

NOTE: if you plan on making changes to the source code, use the following instead:

.. code-block:: console

  $pip install -e .

To check that the installation was successful please run:

.. code-block:: console

   `$ citam -h`

----------------------
How to Add Facilities
----------------------

Currently, the primary way to use CITAM is through the CLI. To get a list of commands, do:

.. code-block:: console

  $citam --help

Before running a simulation, at least one facility must be added. Each facility
will have a name and ingested floorplan data on a per-floor basis. To add a new
facility follow the following steps for each floor.

**1. Ingest Floor Data**

Before you can ingest a floorplan, you need a map file in SVG format and a CSV
file describing each space. For example such files, go to the examples directory.
Assuming you have those 2 files available, use the following command to ingest your floorplan data:

.. code-block:: console

  $citam engine ingest foo_facility foo_floor --csv /examples/basic_example/TF1.csv --svg /examples/basic_example/TF1.svg

Use the help flag as follow for the most up to date information on your system.

.. code-block:: console

  $citam engine ingest -h

During the ingestion process, CITAM will attempt to add doors to spaces that do not have any and
remove walls that are between hallways.


**2. Validate Ingested Data**

 You can export the ingested floorplan as an SVG file for visualization as follow:

.. code-block:: console

  $citam engine export-floorplan foo_facility foo_floor -o foo_ouput.svg

This will export the ingested floorplan in SVG format saved as OUTPUT_FILE.
Use your favorite SVG viewer to open it (most web browsers can show SVG files).
If you don't have a dedicated SVG viewer/editor installed, we recommend installing
the free and open-source INKSCAPE software in case you need to update the ingested floorplan.

If you notice errors in the ingested floorplan, please correct them using your
favorite SVG editor and then use the following command to update.

.. code-block:: console

    $citam engine update-floorplan foo_facility foo_floor --map foo_edited.svg

**3. Build Navigation Network**

Once a floorplan has been ingested, the next step is to generate the Navigation
Network (navnet) using the following command.

.. code-block:: console

    $citam engine build-network foo_facility foo_floor

**4. Validate Navigation Network**

The network can also be exported as an SVG file to be visualized and updated manually.
To export as an SVG file, run the following command:

.. code-block:: console

    $citam export-nav-network foo_facility foo_floor -o foo_navnet_output.svg

The svg file can then be visualized using any SVG viewer.

This process can be repeated for as many facilities as needed. But it is only done
once for each facility.

------------------------
How to Run Simulations
------------------------

Assuming at least one facility was successfully added and validated, any number
of simulations can be run on that facility using the following command where INPUT_FILE
is a JSON input file:

Example input files can be found in the citam/examples directory. It is recommended to create seperate folders for each simulation with their own input file.
To run a simulation copy `example_sim_inputs.json` file to a new directory (let's call it ``SIMULATION_DIR``). Change directory to this new folder and execute:

.. code-block:: console

    $cd SIMULATION_DIR
    $citam engine run example_sim_inputs.json

More example input files can be found in the examples directory.

We recommend going throug the tutorial for a more in-depth guide on how to use CITAM: :ref:`tutorial`

.. toctree::
   :maxdepth: 2
   :caption: To Learn More:
   :glob:

   input_requirements
   facility_data_requirement
   outputs_description
   visualize_results
