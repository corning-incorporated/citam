# Developing for CITAM

Before you start coding, remember to let us know what you are working on by [submitting a new issue](https://github.com/corning-incorporated/citam/issues/new/choose) or commenting on an [existing one](https://github.com/corning-incorporated/citam/issues) to avoid duplicate efforts.

The code is divided into the following components:
+ **Engine**: the core simulation engine to manage facilities and run simulations written in (Python).
+ **CLI**: The Command-Line Interface is currently the primary way of interacting with CITAM written (Python).
+ **API**: used to read and expose simulation results that are served locally over http (Python)
+ **GUI**: The GUI or dashboard is the frontend component to visualize and analyze results (JavaScript).

We recommend going through the documentation of the component of interest to understand the code structure before you start writing your own code.

### Contents
- [Developing for CITAM](#developing-for-citam)
    - [Contents](#contents)
  - [Environment Setup](#-environment-setup)
  - [Building and Writing Documentation](#-building-and-writing-documentation)
  - [Running Tests](#-running-tests)
  - [Coding Rules](#-coding-rules)


## Environment Setup
-------

Keep in mind that Git and NodeJS are required dependencies for developing CITAM:

* Git: The Github [Guide to Set up Git](https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/set-up-git) is a good source of information.
* NodeJS: The [dowload page]((https://nodejs.org/en/download/) ) is a good place to start.

Please start by following the [installation from source](readme.md#from-source) instructions in the readme.

For Python development, we also recommend installing the following additional libraries for testing and ensuring code quality: [pytest](https://www.pytest.org), [flake8](https://flake8.pycqa.org/) and [black](https://github.com/psf/black). Install them as follow:

```
pip install pytest flake8 black
```

We also recommend [building the documentation](#building-the-documentation) locally in case you need to make any updates.

During javascript development, it is useful to have a live-compiler
set up, so you can test changes without recompiling the app.
To run a live-compiler instance, change directory to `citamjs` and run
`npm run serve`

## Building and Writing Documentation
---------

CITAM's documentation is created with [Sphinx](https://www.sphinx-doc.org/). Before you can build the documentation locally, make sure you have sphinx installed as well as the requirements listed in [docs/requirements.txt](docs/requirements.txt):

```
cd docs
pip install sphinx
pip install -r requirements.txt
```

You are now ready to build the documentation using the following command:

```
make html
```

Html outputs form the build process are automatically copied to the [docs](docs/) folder where they are integrated with CITAM's landing page. To view the documentation, open the local copy of `docs/index.html` file with your web browser.

To edit the documentation, find the appropriate RST file in the docs folder and edit it as needed. Rebuild the documentation and visualize it locally to make sure everything looks good before submitting your work.

## Running Tests
----
We use pytest to run the tests. It is important that your changes to the code do not break any existing tests unless you really know what you are doing. As you progress through your work, periodically make sure that all the tests still by running pytest from the citam folder.

```
pytest
```

## Coding Rules
-----------
To make sure all current and future developers of CITAM deal with a uniformly formatted and consistent source code, we follow Python's official [styling rules](https://www.python.org/dev/peps/pep-0008/).

As mentioned before, flake8 is a linter that can help you discover and solve any of those issues. Flake8 is also a good linter to help you with basic code quality. Black is a great tool to use to automatically format you python code.

All new features and bug fixes must be covered by unit tests.

All functions must have appropriate docstrings in [RST format](https://www.python.org/dev/peps/pep-0287/)

All functions must have type hints for parameters and return values.

