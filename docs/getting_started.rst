.. _getting_started:

================
Getting Started
================

Covid-19 Indoor Transmission Agent-based Modeling platform.

When you use CITAM to model your facility (e.g. a school, a manufacturing facility, an office building, etc.), it creates a "virtual" version of that facility and simulates the movement of individuals while keeping track of time and location of contact events as well as the individuals involved. You can vary different input parameters such as number of people, number of shifts and traffic patterns and compare the contact statistics to find the best mitigation strategy to limit transmission within your facility.

As a simulation platform, CITAM does not implement nor does it support real-world tracking of visitors, employees or other people within the facilities of interest. CITAM actually provides an alternative to that approach by allowing a simulation to be used to assess and understand the implications of
various mitigation policies. At its core, CITAM is an agent-based
modeling platform. However, CITAM implements special features that make it
possible to mimic daily activities in various indoor environments.

The primary requirement to use CITAM is to have a map of each floor of each facility in SVG
format for ingestion as well as some metadata about each space in each floorplan. For a list
of required metadata, please visit the :ref:`input_requirements` section of the documentation.
Example input files are also available in the `examples folder <https://www.github.com/corning-incorporated/citam/examples/>`_ of the git repository.

Floorplans must be imported into CITAM before any simulation can be performed with them. This  process is done in four easy steps (2 are required and 2 are optional) described below (example usage is provided in the [How to add facilities](#how-to-add-facilities) section):

1. Ingestion (required): In this step, CITAM reads your SVG and CSV files, automatically adds doors to spaces where missing, removes map artifacts that are deemed unnecessary for the simulation, and stores the resulting data in your local cache for future retrieval.
2. Validation (optional): In this step, you get to inspect results from the ingestion step and make any necessary changes. This step is optional but highly recommended to ensure valid simulation results.
3. Navigation Network Creation (required): When you are happy with the quality of the ingested data, you use a simple command to build the navigation network (or navnet) for your facility. The navnet is used for intelligent navigation of individuals in your facility within the simulation (to know how to go from their office to a cafeteria for example).
4. Navigation Network Validation (optional): You can also verify and edit the navigation network to make sure everything looks good and ensure valid simulation results.

These steps are done only once for each floor of each facility.

Once a facility is successfully ingested into CITAM, any number of simulations can be performed with it. The parameters for each simulation are provided in an input file and include the number of individuals, the duration of the simulation, the contact distance, any one-way traffic, the number and characteristics of each shift if there are several, etc.

CITAM is built as a cross-platform software compatible with all major operating systems. The primary way of using CITAM is currently through the command-line. CITAM is also shipped with a web-based dashboard to visualize simulation results.


CITAM is available on `GitHub <https://www.github.com/corning-incorporated/citam/>`_.

Below you will find a quickstart guide. We also recommend going through the :ref:`tutorial` for more in-depth explanation.

-----------------
Quickstart Guide
-----------------

Install
--------

Please refer to this `Installation Guide <https://github.com/corning-incorporated/citam/tree/alpha#install-citam>`_.

View List of Commands
-----------------

A reference guide for all the CLI commands is available in this document: :ref:`cli_commands`.

Add Example Facility
----------------------

Detailed instructions are available `here <https://github.com/corning-incorporated/citam/tree/alpha#add-facilities>`_.

**TL;DR**

.. code-block:: console

  $cd citam
  $citam engine ingest foo_facility foo_floor --csv examples/basic_example/TF1.csv --svg examples/basic_example/TF1.svg -v
  $citam engine export-floorplan foo_facility foo_floor -o foo_output.svg -v

Use your favorite SVG viewer to open and inspect the exported `foo_output.svg` file. Make necessary changes and update as follows:

.. code-block:: console

  $citam engine update-floorplan foo_facility foo_floor --svg foo_edited.svg -v

Build and validate navigation network:

.. code-block:: console

  $citam engine build-navnet foo_facility foo_floor -v
  $citam engine export-navnet foo_facility foo_floor -o foo_navnet_output.svg -v


Run your First Simulation
---------------------------

Create simulation folder and copy example input file:

.. code-block:: console

  $mkdir citam_simulation
  $cp citam/examples/basic_example/example_sim_inputs.json citam_simulation/.


Start simulation:

.. code-block:: console

    $cd citam_simulation
    $citam engine run example_sim_inputs.json

Congrats you've run your first simulation!

Read the Tutorial
------------------

We recommend going through the tutorial for a more in-depth guide on how to use CITAM: :ref:`tutorial`


