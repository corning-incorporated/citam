# CITAM

Covid-19 Indoor Transmission Agent-based Modeling platform.

 CITAM is a Python agent-based modeling framework for indoor environments. It can be used to create virtual analogs of real facilities to run different types of simulations that can benefit from the use of real floor plans. 
 
 The primary use case is to simulate the movement of individuals while keeping track of time and location of contact events to predict outbreaks in indoor environments. The influence of various parameters such as number of people, number of shifts, scheduling rules, etc. can be explored to find the best mitigation strategy to limit the spread of contact-based transmissible diseases within facilities. CITAM can be used as an alternative or a complement to real-time tracking of facility users to assess and understand the implications of various mitigation policies, before their implementation. 


## Contents  

  - [Install CITAM](#install-citam)
    - [From Python-Wheel (Recommended)](#from-python-wheel-recommended)
    - [From Source](#from-source)
  - [Add Facilities](#add-facilities)
  - [Run Simulations](#run-simulations)
  - [Visualize Results](#visualize-results)
  - [Contributing](#-contributing)
  - [License](#-license)


## Install

> Pre-requisite: Python 3.x

Check your Python version as follows:

```shell script
$python --version    # must be 3.x
```

> Consider creating a new [virtual environment](https://docs.python.org/3/library/venv.html) to install and run CITAM.

Below are the different ways to install CITAM.

### From Python-Wheel (Recommended)

1. Download the python-wheel zip file from the latest release tag [here](https://github.com/corning-incorporated/citam/releases).
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
  $citam engine export-floorplan foo_facility foo_floor -o foo_output.svg -v
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

CITAM comes with a rudimentary and very limited GUI that provides some details on contact statistics and a visual representation of simulation results (we stress that the GUI is very early stage!)

If you installed via python-wheel, the GUI should already be available for your use. Otherwise, to build the GUI from source, use one of the following methods:
1. Running the command `python setup.py build_js`
2. Building manually by doing the following
    2a. `cd citamjs`
    2b. `npm install`
    2c. `npm run build`
    2d. `cp -r dist/ ../citam/api/static/dash`
    2e. `cd ..`

Once the GUI is built, and assuming the current directory has the simulation results to visualize, the server can be started using:

```
$citam dash --results .
```

The GUI can then be accessed at [http://localhost:8000](http://localhost:8000) after 

> *Note: CITAM will recursively scan the results directory for simulation results. For example, if you
start the dashboard with the results directory pointing to the citam source code, it will show sample
results that are used for unit testing.*

You can also set the `CITAM_RESULT_PATH` environment variable to the top level directory
where you expect all your simulation results to be. If you have the `CITAM_RESULT_PATH` environment variable set, you can run `citam dash` (without the --results flag) to start the dashboard/GUI.


## Contributing
-----

We encourage and welcome your contributions to any or all of the components of this code. We also welcome bug reports and feature requests (but we make no guarantee that new feature requests will be implemented any time soon). For detailed instructions, please refer to the "[How to Contribute](contributing.md)" document.

## License
------------
CITAM is made available to the public under GPLv3 and may only be used in accordance with the identified license(s).

Copyright 2020. Corning Incorporated. All rights reserved.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.