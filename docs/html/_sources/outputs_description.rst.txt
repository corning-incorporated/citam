.. _outputs:

===================
Output Description
===================

Outputs from a CITAM simulation are as follows.

::

    SIMULATION_FOLDER
    ├── floor_0
    │   ├── contact_dist_per_coord.csv
    │   |── contacts.txt
    |   |── map.svg
    │   └── heatmap.svg
    ├── agents.ids
    ├── citam.log
    ├── contact_dist_per_agent.csv
    ├── manifest.json
    ├── meetings.txt
    ├── office_assignment.json
    ├── pair_contacts.csv
    |── raw_contact_data.ccd
    ├── schedules.txt
    ├── statistics.json
    |── timing.txt
    └── trajectory.txt


Please note that the structure of these files should be preserved for the dashboard to
successfully load and display information on the GUI.

Floor-Based Results
--------------------

Each floor has its own subfolder which contains data about each contact event that occurred on that floor. Here is
a description of each result file:

* contact_dist_per_coord.csv
    The number of contacts that take place in each x, y location on this floor.

* contacts.txt
    A time-based non-cumulative list of positions where contacts take place. Notice that this does not take into account how many contacts
    take place in each location. This file is used in the dashboard visualizer to plot contact locations as a function of time on this floor.

* heatmap.svg
    A heatmap highlighting the locations and cumulative number of contacts that take place on this floor. This of visual representation of contact_dist_per_coord.csv.

* map.svg
    A bare map of this floor for use by the dashboard visualizer to display time-based data.


Overall Results
----------------

CITAM also includes results that pertain to the entire facility. Here is a description of each file:

* agents_ids.txt
    List of IDs used for each agent in this simulation. This file is subject to removal in subsequent version of CITAM.

* citam.log
    This is the log file with all the details of the simulation. This is particularly useful for debugging. 

* contact_dist_per_agent.csv
    Each line contains the cumulative contact duration (or steps) for each agent. 

* inputs.json
    Input parameters for this simulation as provided by the user.

* manifest.json
    A description of the key information related to this simulation for use by the GUI.

* meetings.txt
    List of meetings automatically scheduled in this simulation. Each meeting has a location, list of attendees, start and end time.

* office_assignment.json
    List of agents and the work space automatically assigned to them in this simulation. This file can be provided as input in case
    the same simulation is to be repeated.

* pair_contacts.csv
    This is one of the primary outputs from CITAM simulations. This file records the number of individual contact events and the total duration of contact
    between every pair of agents (for simplicity, pairs of agents that did not make contact during the simulation are not listed).

* raw_contact_data.ccd
    A dictionary of dictionaries with raw contact data information. It's there in case users want to dive deeper into the data.

* statistics.json
    Key summary data (e.g. total contact duration) from this simulation. Used by the dashboard to show key statistics.

* timing.txt
    How long it took to run this simulation.

* trajectory.txt
    This file contains the time-based x, y, f positions of all the agents for the entire duration of the simulation (f is the floor number).
    This can be used to generate a "video" of the simulation as implemented in the dashboard visualizer.
