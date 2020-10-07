# Developing for CITAM

Before you start coding, remember to let us know what you are working on by [submitting a new issue](https://github.com/corning-incorporated/citam/issues/new/choose) or commenting on an [existing one](https://github.com/corning-incorporated/citam/issues) to avoid duplicate efforts.

As mentioned in the README, The code is divided into the following components:
+ **Engine**: the core simulation engine to manage facilities and run simulations written in (Python).
+ **CLI**: The Command-Line Interface is currently the primary way of interacting with CITAM written (Python).
+ **API**: used to read and expose simulation results that are served locally over http (Python)
+ **Dashboard**: The dashboard is the frontend component to visualize and analyze results (JavaScript).

We recommend going through the documentation of the component of interest to understand the code structure before you start writing your own code.

### Contents
* [Environment Setup](#environment-setup)
* [Running Tests](#running-tests)
* [Coding Rules](#coding-rules)
* [Linting and Styling Rules](#linting-and-styling-rules)
* [Writing Documentation](#writing-documentation)


## Environment Setup

During javascript development, it is useful to have a live-compiler
      set up, so you can test changes without recompiling the app.
      To run a live-compiler instance, change directory to `citamjs` and run
      `npm run serve`