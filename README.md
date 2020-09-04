# CITAM

## Developers

### Pre-requisites
* NodeJS
* Python 3.x

### Install process
To setup a local development environment
1. run ``python setup.py install -e``.  This will install the Python and
   NPM dependencies required to run the application, and compiles the
   javascript into the installed python package.

2. Run the server with the command `citam dash`

3. During javascript development, it is useful to have a live-compiler
   set up, so you can test changes without recompiling the app.
   To run a live-compiler instance, open the `citamjs` directory and run
   `npm run serve`

4. **TODO: Create a new command `citam develop` which combines `citam dash` and `npm run serve`

