# CITAM

Covid-19 Indoor Transmission Agent-based Modeling platform.

When you use CITAM to model your facility (e.g. a school, a manufacturing facility, an office building, etc.), it creates a "virtual" version of that facility and simulates the movement of individuals while keeping track of time and location of contact events as well as the individuals involved. You can vary different input parameters such as number of people, number of shifts and traffic patterns and compare the contact statistics to find the best mitigation strategy to limit transmission within your facility.

As a simulation platform, CITAM does not implement nor does it support real-world tracking of visitors, employees or other people within the facilities of interest. CITAM actually provides an alternative to that approach by allowing a simulation to be used to assess and understand the implications of
various mitigation policies. At its core, CITAM is an agent-based
modeling platform. However, CITAM implements special features that make it
possible to mimic daily activities in various indoor environments.

The primary requirement to use CITAM is to have a map of each floor of each facility in SVG format for ingestion as well as some metadata about each space in each floorplan. For a list of required metadata, please visit the input requirements section of the documentation. Example input files are also available in the [examples](examples/) folder in this git repository.

Floorplans must be imported into CITAM before any simulation can be performed with them. This  process is done in four easy steps (2 are required and 2 are optional) described below (example usage is provided in the [How to add facilities](#how-to-add-facilities) section):
1. **Ingestion** (required): in this step, CITAM reads your SVG and CSV files, automatically adds doors to spaces where missing, removes map artifacts that are deemed unnecessary for the simulation, and stores the resulting data in your local cache for future retrieval.
2. **Validation** (optional): In this step, you get to inspect results from the ingestion step and make any necessary changes. This step is optional but highly recommended to ensure valid simulation results.
3. **Navigation Network Creation** (required): When you are happy with the quality of the ingested data, you use a simple command to build the navigation network (or navnet) for your facility. The navnet is used for intelligent navigation of individuals in your facility within the simulation (to know how to go from their office to a cafeteria for example).
4. **Navigation Network Validation** (optional): You can also verify and edit the navigation network to make sure everything looks good and ensure valid simulation results.

These steps are done only once for each floor of each facility.

Once a facility is successfully ingested into CITAM, any number of simulations can be performed with it. The parameters for each simulation are provided in an input file and include the number of individuals, the duration of the simulation, the contact distance, any one-way traffic, the number and characteristics of each shift if there are several, etc.

CITAM is built as a cross-platform software compatible with all major operating systems. The primary way of using CITAM is currently through the command-line. CITAM is also shipped with a web-based dashboard to visualize simulation results.

## Getting Started
--------------
## Install CITAM

### Pre-requisite: Python 3.x

Check your Python version as follows:

```shell script
$python --version    # must be 3.x
```

> Consider creating a new [virtual environment](https://docs.python.org/3/library/venv.html) to install and run CITAM.

Below are the different ways to install CITAM.

### From Python-Wheel (Recommended)

1. Download the python-wheel [here](https://github.com/corning-incorporated/citam/actions/runs/292437599) (TODO: Update link to a release tag).
2. Extract the compressed file locally, 
3. change directory to the extracted python-wheel folder.  Do not rename this file.
4. run `pip install <citam wheel>` where citam_wheel is the extracted .whl file

### From Source

[NodeJS](https://nodejs.org/en/download/) and Git are additional pre-requisites to install from source. Use the following to make sure all additional pre-requisites are satisfied:

```shell script
$git --version
$node --version      # should be 12 or above
$npm --version       # should be 6 or above
```

If all pre-requisites are satisfied, download the source code as follow:

```
$git clone https://github.com/corning-incorporated/citam.git
```

> For the latest usable version, please change directory to the citam directory and checkout the "alpha" branch as follows:

```
$cd citam
$git checkout alpha
```

After successful cloning, install CITAM as follows:

Build the dashboard one of the following ways:
1. Running the command `python setup.py build_js`
2. Building manually by doing the following
    2a. `cd citamjs`
    2b. `npm install`
    2c. `npm run build`
    2d. `cp -r dist/ ../citam/api/static/dash`
    2e. `cd ..`

Then install the pip package using the command
  ```
  $pip install .
  ```

> Note: If you plan on making changes to the code, we recommend installing as follows instead:
  ```
  $pip install -e .
  ```

After a successful installation, you are ready to ingest your facilities and run simulations for them. To check that the installation was successful, please run:

```
$citam -h
```

 > Note: In case matplotlib gives an error, these steps have been found to solve the problem:
```
   $pip uninstall matplotlib  # uninstall the package

   $pip install matplotlib   # reinstall it
```
   For a walkthrough example of how to add your facilities and run simulations, go to the [getting started](#getting-started) section and consult the documentation.

## Add Facilities

Currently, the primary way to use CITAM is through the CLI. To get a list of commands, do:

  ```
  $citam --help
  ```

Help is also available for each subcommand. For example, for the engine subcommand do:

```
$citam engine --help
```

Before running a simulation, at least one facility must be added. Each facility
will have a name and per-floor data (i.e. floorplan) ingested from SVG and CSV files. To add a new
facility with one floor, follow the steps below.

> Verbose option is available for all `citam` commands with option `-v`. Log level debug information can be obtained with stacking option `-v -v`

**1. Ingest Floor Data**

Before you can ingest a floorplan, you need a map file in SVG format and a CSV
file describing each space. To see examples of floorplan SVG and CSV files, go to the examples subdirectory. Use the following command to ingest floorplan data from the [citam/examples/basic_example/](examples/basic_example/) subdirectory:

  ```
  $citam engine ingest foo_facility foo_floor --csv examples/basic_example/TF1.csv --svg examples/basic_example/TF1.svg -v
  ```

During the ingestion process, CITAM will attempt to add doors to spaces that do not have any and
remove walls that are between hallways.


**2. Validate Ingested Data**

 You can export the ingested floorplan as an SVG file for visualization as follow:

  ```
  $citam engine export-floorplan foo_facility foo_floor -o foo_ouput.svg -v
  ```

This will export the ingested floorplan in SVG format saved as OUTPUT_FILE.
Use your favorite SVG viewer to open it (most web browsers can show SVG files).
If you don't have a dedicated SVG viewer/editor installed, we recommend installing
the free and open-source INKSCAPE software in case you need to update the ingested floorplan.

If you notice errors in the ingested floorplan, please correct them using your
favorite SVG editor, save the edited file with a new name (e.g. foo_edited.svg) and use the following command to update the floorplan:

   ```
   $citam engine update-floorplan foo_facility foo_floor --svg foo_edited.svg -v
   ```

**3. Build Navigation Network**

Once a floorplan has been ingested, the next step is to generate the Navigation
Network (navnet) using the following command.

   ```
   $citam engine build-navnet foo_facility foo_floor -v
   ```

**4. Validate Navigation Network**

The network can also be exported as an SVG file to be visualized and updated manually.
To export as an SVG file, run the following command:

   ```
   $citam engine export-navnet foo_facility foo_floor -o foo_navnet_output.svg -v
   ```

The svg file can then be visualized using any SVG viewer.

This process can be repeated for as many facilities as needed. But it is only done once for each facility.


## Run Simulations

Assuming at least one facility was successfully added and validated, any number of simulations can be run on that facility. Example input files can also be found in the [citam/examples](examples/) directory. It is recommended to create separate folders for each simulation with their own input file.

To run a test simulation, copy [example_sim_inputs.json](examples/basic_example/example_sim_inputs.json) file to a new directory (let's call it `citam_simulation`). If you are on a UNIX system, you can do:

   ```
   $mkdir citam_simulation
   $cp citam/examples/basic_example/example_sim_inputs.json citam_simulation/.
   ```

To run the simulation:

   ```
   $cd citam_simulation
   $citam engine run example_sim_inputs.json -v
   ```

Wait for your simulation to complete successfully before moving to the next section.


## Visualize Results

The dashboard provides contact details and visual representation of simulation results and can be accessed at [http://localhost:8000](http://localhost:8000) after firing
the server using.

```
$citam dash --results .
```

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

## Contributing
-----
The code is divided into multiple components:
+ **Engine**: the core simulation engine to manage facilities and run simulations (written in Python).
+ **CLI**: The Command-Line Interface, currently the primary way of interacting with CITAM (written in Python).
+ **API**: used to read and expose simulation results that are served locally over http (written in Python)
+ **Dashboard**: The dashboard is the frontend component to visualize and analyze results (written in JavaScript).

We welcome your contributions to any or all of these components. We also welcome bug reports and feature requests. For detailed instructions, please refer to the "[How to Contribute](contributing.md)" document.

## License
------------
CITAM is made available to the public under GPLv3.

