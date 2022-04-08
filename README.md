![pull request workflow](https://github.com/corning-incorporated/citam/actions/workflows/pull_request_and_push.yaml/badge.svg) [![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/corning-incorporated/citam/issues) ![code style](https://img.shields.io/badge/code%20style-black-black) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# CITAM

Covid-19 Indoor Transmission Agent-based Modeling platform.

CITAM is a Python agent-based modeling framework for indoor environments. It can be used to create virtual analogs of real facilities to run different types of simulations that can benefit from the use of real floor plans.

The primary use case is to simulate the movement of individuals while keeping track of time and location of contact events to predict outbreaks in indoor environments. The influence of various parameters such as number of people, number of shifts, scheduling rules, etc. can be explored to find the best mitigation strategy to limit the spread of contact-based transmissible diseases within facilities. CITAM can be used as an alternative or a complement to real-time tracking of facility users to assess and understand the implications of various mitigation policies, before their implementation.

In addition to its core functionalities, CITAM comes with:

- A CLI app to process facility maps and run simulations
- A frontend app to visualize simulation results

Moreover, CITAM can be used as extendable library to create more complex simulations.

## Install

CITAM requires Python 3.7 or above. You can install CITAM from a release wheel or from source (direct install from pip and conda will be supported soon).

### From Python-Wheel (Recommended)

1. Download the python-wheel zip file from the latest release tag [here](https://github.com/corning-incorporated/citam/releases).
2. Extract the compressed file locally and change directory to the extracted folder.
3. Run `pip install <citam wheel>` where citam_wheel is the extracted `.whl` file.

### From Source

Make sure you have node v12 or above and npm v6 or above.

```
git clone https://github.com/corning-incorporated/citam.git
cd citam
pip install .
python setup.py build_js
```

> Note: If you plan on making changes to the code, use the -e option in your pip command as follows:

```
pip install -e .
```

## Run the CITAM visualizer

From the main CITAM directory, run the following command which will start the CITAM server and allow you to visualize an example simulation results included in this repository.

```
citam dash --results examples/basic_example
```

Open a web browser and navigate to localhost:8000.

## Run CITAM Simulations

To run your own simulations, create a new folder (outside of the CITAM source code folder, if you installed from source). Let's call it citam-test.

You will need an input file and a facility directory which contains a map and a navigation network for each floor. We include an example input file and facility directory in the examples/basic_example folder. Copy the example facility folder and input file into citam-test then run your simulation as follows.

```
cp -r citam/citam/examples/basic_example/foo_facility citam-test/.
cp citam/citam/examples/basic_example/example_sim_inputs.json citam-test /.
cd citam-test
citam engine run example_sim_inputs.json -v
```

## Resources

To learn how to ingest your own facility maps and what inputs CITAM supports, follow the tutorial included in our documentation.

We also include an example Jupyter notebook that shows how to manage facilities from a notebook: [/examples/visualize_floorplan.ipynb](https://github.com/corning-incorporated/citam/blob/ui-redesign/examples/visualize_floorplan.ipynb)

## Contributing

We encourage and welcome your contributions to any or all of the components of this code. We also welcome bug reports and feature requests (but we make no guarantee that new feature requests will be implemented any time soon). For detailed instructions, please refer to the "[How to Contribute](CONTRIBUTING.md)" document.

## License

CITAM is made available to the public under GPLv3 and may only be used in accordance with the identified license(s).

Copyright 2020-2021. Corning Incorporated. All rights reserved.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
