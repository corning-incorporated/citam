# CITAM

Covid-19 Indoor Transmission Agent-based Modeling platform.

When you use CITAM to model your facility (e.g. a school, a manufacturing facility, an office building, etc.), it creates a "virtual" version of that facility and simulates the movement of individuals while keeping track of time and location of contact events as well as the individuals involved.

As a simulation platform, CITAM does not implement nor does it support real-world tracking of visitors, employees or other people within the facilities of interest. CITAM actually provides an alternative to that approach by allowing a simulation to be used to assess and understand the implications of
various mitigation policies. At its core, CITAM is an agent-based
modeling platform. However, CITAM implements special features that make it
possible to mimic daily activities in various indoor environments.

The primary requirement to use CITAM is to have a map of each floor of each facility in SVG format for ingestion as well as some metadata about each space in each floorplan. For a list of required metadata, please visit the input requirements section of the documentation. Example input files are also available in the `examples` folder in this git repository. Floorplans must be ingested into CITAM before any simulation can be performed with them. This ingestion process is done in four easy steps described in the [How to add facilities](#how-to-add-facilities) section.

Once a facility is successfully ingested into CITAM, any number of simulations can be performed with it. The parameters for each simulation are provided in an input file and include the number of individuals, the duration of the simulation, the contact distance, any one-way traffic, the number and characteristics of each shift if there are several, etc.

CITAM is built as a cross-platform software compatible with all major operating systems. The primary way of using CITAM is currently through the command-line. CITAM is also shipped with a web-based dashboard to visualize simulation results.

### Pre-requisites
* Python 3.x
* [NodeJS](https://nodejs.org/en/download/) (to use the dashboard)

You may already have Python and NodeJS installed. Check their version to make sure all pre-requisites are satisfied:

```shell script
$python --version    # must be 3.x
$node --version      # should be 12 or above
$npm --version       # should be 6 or above
```

## To Install

> Consider creating a new [virtual environment](https://docs.python.org/3/library/venv.html) to install and run CITAM.

### From GitHub

`$git clone https://github.com/corning-incorporated/citam.git`

> For the latest usable version, please change directory to the citam directory and checkout the "alpha" branch as follows:

```
$cd citam
$git checkout alpha
```

After successful cloning, install CITAM as follows:

  `$pip install .`

> Note: If you plan on making changes to the code, we recommend installing as follows instead:
  `$pip install -e .`

After a successful installation, you are ready to ingest your facilities and run simulations for them. To check that the installation was successful, please run:

`$citam -h`

 > Note: In case matplotlib gives an error, please try uninstalling and reinstalling as follow:
```
   $pip uninstall matplotlib  # uninstall the package

   $pip install matplotlib   # reinstall it
```
   For details on how to add your facilities and run simulations, go to the [getting started](#getting-started) section and consult the documentation.

### Using Anaconda

   Coming soon

### Using PIP

   Coming soon

## Getting Started


### How to Add Facilities

Currently, the primary way to use CITAM is through the CLI. To get a list of commands, do:

  `$citam --help`

Before running a simulation, at least one facility must be added. Each facility
will have a name and per-floor data (i.e. floorplan) ingested from SVG and CSV files. To add a new
facility with one floor, follow the steps below.

> Verbose option is available for all `citam` commands with option `-v`. Log level debug infomration can be obtained with stacking option `-v -v`

**1. Ingest Floor Data**

Before you can ingest a floorplan, you need a map file in SVG format and a CSV
file describing each space. To see examples of floorplan SVG and CSV files, go to the examples subdirectory. Use the following command to ingest floorplan data from the `citam/examples/basic_example/` subdirectory:

  `$citam engine ingest foo_facility foo_floor --csv citam/examples/basic_example/TF1.csv --svg citam/examples/basic_example/TF1.svg -v`

During the ingestion process, CITAM will attempt to add doors to spaces that do not have any and
remove walls that are between hallways.


**2. Validate Ingested Data**

 You can export the ingested floorplan as an SVG file for visualization as follow:

  `$citam engine export-floorplan foo_facility foo_floor -o foo_ouput.svg`

This will export the ingested floorplan in SVG format saved as OUTPUT_FILE.
Use your favorite SVG viewer to open it (most web browsers can show SVG files).
If you don't have a dedicated SVG viewer/editor installed, we recommend installing
the free and open-source INKSCAPE software in case you need to update the ingested floorplan.

If you notice errors in the ingested floorplan, please correct them using your
favorite SVG editor, save the edited file with a new name (e.g. foo_edited.svg) and use the following command to update the floorplan:

   `$citam engine update-floorplan foo_facility foo_floor --svg foo_edited.svg`

**3. Build Navigation Network**

Once a floorplan has been ingested, the next step is to generate the Navigation
Network (navnet) using the following command.

   `$citam engine build-navnet foo_facility foo_floor`

**4. Validate Navigation Network**

The network can also be exported as an SVG file to be visualized and updated manually.
To export as an SVG file, run the following command:

   `$citam engine export-navnet foo_facility foo_floor -o foo_navnet_output.svg`

The svg file can then be visualized using any SVG viewer.

This process can be repeated for as many facilities as needed. But it is only done once for each facility.


### How to Run Simulations

Assuming at least one facility was successfully added and validated, any number
of simulations can be run on that facility using the `citam engine run INPUT_FILE` command where INPUT_FILE is a JSON input file:

Example input files can also be found in the `citam/examples` directory. It is recommended to create seperate folders for each simulation with their own input file.

To run a test simulation, copy `example_sim_inputs.json` file to a new directory (let's call it `citam_simulation`). If you are on a UNIX system, you can do:

   `$mkdir citam_simulation`

   `$cp citam/examples/basic_example/example_sim_inputs.json citam_simulation/.`

To run the simulation, change directory to the new folder `citam_simulation` and invoke `citam engin run` as follows:

   `$cd citam_simulation`

   `$citam engine run example_sim_inputs.json -v`

Wait for your simulation to complete successfully before moving to the next section.


### How to Visualize Results


The dashboard provides contact details and visual representation of simulation results and can be accessed at [http://localhost:8000](http://localhost:8000) after firing
the server using.

`$citam dash --results .`

> *Note: CITAM will recursively scan the results directory for simulation results. For example, if you
start the dashboard with the results directory pointing to the citam source code, it will show sample
results that are used for unit testing.*

You can also set the `CITAM_RESULT_PATH` environment variable to the top level directory
where you expect all your simulation results to be. If you have the `CITAM_RESULT_PATH` environment variable set, you can run `citam dash` (without the --results flag) to start the dashboard.

You can check all simulation runs along with facility-level information in tabular format on the first
page. By clicking on `View Details`; you will be taken to a screen with detailed information such as:

 - Overall Total Contact Duration
 - Average Number of Contacts Per Agent
 - Average Contact Duration Per Agent
 - Average Number of People Per Agent

 On this page you will also find charts for:

 - Per Agent Total Contact and Average Contact Duration scatterplot
 - Total Contact per Agent histogram
 - Average Contact Duration (minutes) histogram
 - Contact heatmap

 You can also access interactive visual map of floors and time-based individuals movement by clicking on the `Visualization` tab.

## Local Dev Setup

During javascript development, it is useful to have a live-compiler
      set up, so you can test changes without recompiling the app.
      To run a live-compiler instance, change directory to `citamjs` and run
      `npm run serve`

## Contributing

The code is divided into multiple components:
+ **Engine**: the core simulation engine to manage facilities and run simulations written in (Python).
+ **CLI**: The Command-Line Interface is currently the primary way of interacting with CITAM written (Python).
+ **API**: used to read and expose simulation results that are served locally over http (Python)
+ **Dashboard**: The dashboard is the frontend component to visualize and analyze results (JavaScript).

We welcome your contributions to any or all of these components.

## License

CITAM is made available to the public under GPLv3.

