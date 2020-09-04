# CITAM

Covid-19 Indoor Transmission Agent-based Modeling platform.

CITAM works by creating a "virtual" facility analagous to the real facility
of interest. Therefore, the primary requirement is to have a map of each floor of each facility in SVG format for ingestion. Another requirement is to have metadata available for each space in each floorplan in a CSV file. The example folder contains some example SVG and CSV files for your review. For a list of supported metadata information, please visit the input requirements section of the documentation.

Please note that no actual tracking of visitors, employees or
other people take place. CITAM actually provides an alternative to that
approach by allowing a simulation to be used to understand the implications of
various mitigation policies. At its core, CITAM is an agent-based
modeling platform. However, CITAM implements special features that make it
possible to mimic daily activities in various indoor environments.

The code is divided into multiple components:
+ **Engine**: the core simulation engine to manage facilities and run simulations
+ **CLI**: The Command-Line Interface is currently the primary way of interacting with CITAM.
+ **API** and **Dahboard**: These two go together but are 2 seperate components. The API is used to process simulation results and serves data locally over http and the dashboard is the frontend component to visualize and analyze results.

### Pre-requisites
* Python 3.x
* NodeJS (to use the dasboard)


## To Install

> Consider creating a new virtual environment to install and run CITAM.

### From GitHub

`$ git clone https://github.com/corning-incorporated/citam.git`

> For the latest usable version, please cd to the citam directory and checkout the "alpha" branch as follows:
`$ git checkout alpha`

After successful cloning, follow these steps to install:
1. Install the engine and CLI

   `$ python setup.py install`

   > Note: In case matplotlib gives an error, please try uninstalling and reinstalling as follow:

      `$ pip uninstall matplotlib`

      `$ pip install matplotlib`

   With the engine and CLI installed, you are ready to run simulations. To check that the installation was successful please run:

   `$ citam -h`

   For details on how to add your facilities and run simulations, go to the getting started section and consult the documentation. If you want to visualize simulation results, you need to install the dashboard Node dependencies by following the step below.

2. Install the dashboard dependencies and setup local development environemnt:
   - If you don't already have it, eownload and install [NodeJS 12](https://nodejs.org/en/download/)
   - Run ``python setup.py install -e``
   > This will install both Python and NPM dependencies required to run the application, and compile the javascript into the installed python package.
   - Run the dashboard with the command `$ citam dash`

   > During javascript development, it is useful to have a live-compiler
      set up, so you can test changes without recompiling the app.
      To run a live-compiler instance, open the `citamjs` directory and run
      `npm run serve`

### Using Anaconda

   Coming soon

### Using PIP

   Coming soon

## Getting Started


How to Add Facilities
----------------------

Currently, the primary way to use CITAM is through the CLI. To get a list of commands, do:

  `$citam --help`

Before running a simulation, at least one facility must be added. Each facility
will have a name and ingested floorplan data on a per-floor basis. To add a new
facility follow the following steps for each floor.

**1. Ingest Floor Data**

Before you can ingest a floorplan, you need a map file in SVG format and a CSV
file describing each space. For example such files, go to the examples directory.
Assuming you have those 2 files available, use the following command to ingest your floorplan data:

  `$citam engine ingest FACILITY_NAME FLOOR_NAME --csv CSV_FILE --map SVG_FILE`

During the ingestion process, CITAM will attempt to add doors to spaces that do not have any and
remove walls that are between hallways.


**2. Validate Ingested Data**

 You can export the ingested floorplan as an SVG file for visualization as follow:

  `$citam engine export-floorplan FACILITY_NAME FLOOR_NAME -o OUTPUT_FILE`

This will export the ingested floorplan in SVG format saved as OUTPUT_FILE.
Use your favorite SVG viewer to open it (most web browsers can show SVG files).
If you don't have a dedicated SVG viewer/editor installed, we recommend installing
the free and open-source INKSCAPE software in case you need to update the ingested floorplan.

If you notice errors in the ingested floorplan, please correct them using your
favorite SVG editor and then use the following command to update.

   `$citam engine update-floorplan FACILITY_NAME FLOOR_NAME --map EDITED_SVG_FILE`

**3. Build Navigation Network**

Once a floorplan has been ingested, the next step is to generate the Navigation
Network (navnet) using the following command.

   `$citam engine build-network FACILITY_NAME FLOOR_NAME`

**4. Validate Navigation Network**

The network can also be exported as an SVG file to be visualized and updated manually.
To export as an SVG file, run the following command:

   `$citam export-nav-network FACILITY_NAME FLOOR_NAME -o OUTPUT_SVG_FILE`

The svg file can then be visualized using any SVG viewer.

This process can be repeated for as many facilities as needed. But it is only done once for each facility.

How to Run Simulations
------------------------

Assuming at least one facility was successfully added and validated, any number
of simulations can be run on that facility using the following command where INPUT_FILE
is a JSON input file:

   `$citam engine run INPUT_FILE`

Example input files can be found in the citam/examples directory.

## Contributing


## License
