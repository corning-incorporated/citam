==============================
Simulation Input Requirements
==============================

Simulation inputs are provided in JSON files. There is one required input file
which is the main simulation input file and two optional input files which are
the meetings and scheduling policies respectively.

-----------------------
Main Simulation Inputs
-----------------------

*Required Inputs*

:facility_name: (*string*), the name of the facility to run this simulation for. This must be
                a facility that's already been added.
:floors: (*Array<string>*) List of floors to simulate. Each floor is identified by its name.
        Example: ["0"]
:entrances: (*Array<object>*) Each entrance is identified by the space name where it is located
            as well as the floor name. The name has to match the unique name of the space as given
            in the CSV metadata file. Example: [ {"name":"AISLE213", "floor": "0"}]
:daylength: (*number*) How long to run the simulation in seconds. Example: 3600 (for 1 hour)
:entrance_time: (*number*) How many seconds after the simulation starts do most people enter
                the facility. Example: 300
:n_agents: (*number*) number of agents to simulate.

*Optional Inputs*

:floorplan_scale: (*number*) The scale of the floorplan in [ft]/[drawing unit].
                    Default: 1/12 [ft]/[drawing unit] (assuming the drawing is in inches)
:contact_distance: (*number*) The maximum distance within which a contact take place. Default: 6 [ft]
:upload_results: (*boolean*) Whether to upload the results to an S3 location. To
                 be able to upload data to an S3 bucket, the s3cmd program must
                 be available from the terminal process where citam is running. Default: true.
:upload_location: (*string*) Address of upload location. Example: s3://citam_results_storage.
                  No default value. Required if 'upload_results' is true.
:meetings_file: (*string*) Path to the JSON meetings policy file. Default: "meetings.json",
:scheduling_policy_file: (*string*) Path to the JSON scheduling policy file. Default: "scheduling_policy.json",
:shifts: (*Array<object>*) Each shift information has a user-defined name, a start_time and
        percent_workforce for that shift. Example: [{"name":"1", "start_time": 0, "percent_workforce": 1.0}],
:traffic_policy: (*Array<object>*) Each element of this array must have a floor name,
        the segment_id and direction of the traffic. To find the segment id use the CLI as
        shown below. Example: [{"floor": "0", "segment_id":"0", "direction": -1}]

.. code-block:: console

    citam engine export-potential-oneway-aisles -o OUTPUT_FILE


-------------------
Scheduling Policy
-------------------

The optional scheduling policy file contains parameters that describe where and when agents
move within the facility. The default values can be found in citam/egine/constants.py.

The sceduling policy is made of scheduling purposes where each purpose has a
name, a minimum duration, a maximum duration, a minimum instances and a maximum
instances.

Each agent's schedules (and associated itineraries) is created around existing meetings
by randomly selecting one of those purpose items, randomly choosing a location that match
the chosen purpose and randomly choosing a duration between the minimum and maximum
values (given in seconds). The number of instances of a given purpose item will be capped at the
maximum instances value. There is no guarantee that the minimum value will be
satisfied.

Here is the default scheduling rules for your reference.

DEFAULT_SCHEDULING_RULES = {

    OFFICE_WORK:     {
                      "purpose": OFFICE_WORK,
                      "min_duration": 600,
                      "max_duration": 7200,
                      "min_instances": 2,
                      "max_instances": 10
                      },
    RESTROOM_VISIT:  {
                      "purpose": RESTROOM_VISIT,
                      "min_duration": 300,
                      "max_duration": 900,
                      "min_instances": 1,
                      "max_instances": 4
                      },
    CAFETERIA_VISIT: {
                      "purpose": CAFETERIA_VISIT,
                      "min_duration": 900,
                      "max_duration": 3600,
                      "min_instances": 0,
                      "max_instances": 2},
    MEETING:         {
                      "purpose": MEETING,
                      "min_duration": 1200,
                      "max_duration": 7200,
                      "min_instances": 1,
                      "max_instances": 8
                      },
    LAB_WORK:        {
                      "purpose": LAB_WORK,
                      "min_duration": 1200,
                      "max_duration": 10800,
                      "min_instances": 1,
                      "max_instances": 4
                      }
}

----------------
Meetings Policy
----------------

The meetins policy file defines how many meetings take place as well as when, where they
happen and who participate.

