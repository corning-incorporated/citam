=========================
API Developer Reference
=========================

-------------------
Running the backend
-------------------

.. note::
   In order to run the backend, you need to get credentials for the results
   storage server.  Contact soperc@corning.com for more info

1. Create a new virtualenv, and activate it
#. Run :code:`pip install -e .` to install the project and all dependencies
   into the virtualenv
#. Start the server with :code:`python -m citam`

.. note::
    To use local results instead of the result storage server,
    set the environment variable ``USE_LOCAL_RESULTS=True`` when running
    gunicorn.


.. _running_frontend:

--------------------
Running the frontend
--------------------

1. Open the ``visualizations`` directory in a terminal
#. Run :code:`npm install` to install all dependencies for the frontend.
#. Run :code:`npm run serve` to start the development server, which allows
   viewing and developing on the frontend.

--------------------------------------
Compiling the frontend to static files
--------------------------------------

.. note::
   this assumes you have a frontend development environment configured, see
   running_frontend_ for instructions.

1. Run :code:`npm run build`.  This will compile javascript files to the
   ``dist`` directory

