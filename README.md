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
* [NodeJS](https://nodejs.org/en/download/) (to use the dashboard)

You may already have Python and NodeJS installed. Check their version to make sure all pre-requisites are satisfied:

```shell script
$ python --version    # must be 3.x
$ node --version      # should be 12 or above
$ npm --version       # should be 6 or above 
```

## To Install

> Consider creating a new [virtual environment](https://docs.python.org/3/library/venv.html) to install and run CITAM.

### From GitHub

`$ git clone https://github.com/corning-incorporated/citam.git`

> For the latest usable version, please change directory to the citam directory and checkout the "alpha" branch as follows:

```
$ cd citam
$ git checkout alpha
```

After successful cloning, install CITAM as follows:

  `$ pip install -e .`

   With the engine and CLI installed, you are ready to run simulations. To check that the installation was successful please run:

   `$ citam -h`
   
 > Note: In case matplotlib gives an error, please try uninstalling and reinstalling as follow:
```
   $ pip uninstall matplotlib  # uninstall the package

   $ pip install matplotlib   # reinstall it
```      
   For details on how to add your facilities and run simulations, go to the [getting started](#getting-started) section and consult the documentation. If you want to visualize simulation results, you need to install the dashboard Node dependencies by following the step below.

   

### Using Anaconda

   Coming soon

### Using PIP

   Coming soon

## Getting Started


### How to Add Facilities

Currently, the primary way to use CITAM is through the CLI. To get a list of commands, do:

  `$citam --help`

Before running a simulation, at least one facility must be added. Each facility
will have a name and ingested floorplan data on a per-floor basis. To add a new
facility follow the following steps for each floor.

> Verbose option is available for all `citam` commands with option `-v`. Log level degug infomration can be obtained with stacking option `-v -v`

**1. Ingest Floor Data**

Before you can ingest a floorplan, you need a map file in SVG format and a CSV
file describing each space. For example such files, go to the examples directory.
Assuming you have those 2 files available, use the following command to ingest your floorplan data:

  `$citam engine ingest foo_facility foo_floor --csv /examples/basic_example/TF1.csv --map /examples/basic_example/TF1.svg`

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
favorite SVG editor and then use the following command to update. (e.g. foo_edited.svg is edited svg file)

   `$citam engine update-floorplan foo_facility foo_floor --map foo_edited.svg`

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
of simulations can be run on that facility using the following command where INPUT_FILE
is a JSON input file:

Example input files can be found in the citam/examples directory. It is recommended to create seperate folders for each simulation with their own input file.
To run a simulation copy `example_sim_inputs.json` file to a new directory. Change directory to this new folder and execute:

   `$citam engine run example_sim_inputs.json`



### How to Visualize Results

Dashboard provides contact details and visual representation of all simulations that were part of previous steps. 
Dashboard can be accessed at [http://localhost:8081](http://localhost:8081). 

You can check all simulation runs along with floor level information in tabular format on the first 
page. By clicking on `View Details`; you would be taken to details page with following informations listed:

 - Overall Total Contact Duration 
 - Average Number of Contacts Per Agent
 - Average Contact Duration Per Agent
 - Average Number of People Per Agent
 
 On this page you would find charts for:
 
 - Per Agent Total Contact and Average Contact Duration scatterplot
 - Total Contact per Agent histogram
 - Average Contact Duration (minutes) histogram
 - Contact heatmap
 
 
 You can access interactive visual map of floors and agenet movement by clicking on `Visualization` tab on this page. 

## Local Dev Setup

> During javascript development, it is useful to have a live-compiler
      set up, so you can test changes without recompiling the app.
      To run a live-compiler instance, change directory to `citamjs` and run
      `npm run serve`
      
> Local back-end setup can be run via `citam dash --results .` It should be accessible at localhost:8000

## Contributing

## License

CITAM is made available to the public under GPLv3.

