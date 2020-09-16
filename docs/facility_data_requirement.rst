.. _svg_requirements:

============================
Floorplan Data Requirements
============================

The CITAM platform requires a Simplified Vector Graphic (SVG) representation of the facility drawing you wish to use as input. The model has simple but specific requirements for the SVG format. Although the platform can act upon SVG’s produced by free online converters there are expectations about the format of the initial drawing that must be met in order for this to work. Free converters typically produce unnecessarily bloated files, which can cause performance issues within the platform. The model performs most efficiently against a lightweight representation of the SVG.

This document will explain what a lightweight SVG will need to consist of - and what it doesn’t. We recognize that there are many drawing formats that can be the starting point for producing an SVG file. The focus of this process document will be to represent the most stripped down components required within the SVG file used by the model. It will also describe what information is required within the SVG in order for the model to best simulate real life scenarios.

The general idea is to relay a clear understanding of what the converted end point should look like, regardless of a users starting point,. We will leave it up to the end user to determine the best method to arrive at this format. Producing such a representation of your drawing will likely require some custom scripting. We will provide an example of what this would look like in the form of a VBA script that is designed to convert an AutoDesk DWG file to the desired simplified SVG format.
Scripting to accommodate other drawing sources are in consideration for future releases. We also welcome community contributions.

---------------------------------
Primary Information Requirements
---------------------------------

The source drawing must represent indoor spaces only. The platform is not designed to simulate transmission points in outdoor spaces - even outdoor spaces that are part of facility, such as...

.. image:: images/example_floorplan_1.png
  :alt: Example floorplan.

Facilities
***********
    #. If the source facility is a large campus consisting of multiple connected buildings, the entirety of the campus must be represented for a single floor across buildings within the SVG so that the model can appropriately handle traffic flow between buildings on that floor. The name of the facility as well as the floor name can be embedded in the SVG file.
    #. If the source drawing represents a multi-floor building...

        * A separate drawing for each floor must be generated
        * Stairways and elevators must be included within the drawings so that model understands all the points within a facility that could serve as an entrance or exit for a floor. These should exist in separate layers within the drawing
        * Information in the SVG file must be grouped in layers

Layers
*******
All layers containing required features within the drawing must be labeled with the following key words. All other layers are ingnored.
* *spaces* - to represent stairways
* *doors* - represent elevators

Spaces
*******
    1. All inhabitable spaces within a source drawing must be defined by polylines (path elements)
    2. The space defining polylines should exist within a separate and distinct layer of the drawing
    3. Each polyline defining a space will require an identifier that is unique across the drawing.
    4. The polyline id should be embedded as a property of the polyline.

Space Attributes
-----------------
    1. Space Type: space types are defined below.
    2. Space Name: these can be completely custom labels used to reference a space by humans within a facility. Examples:

        * Arbitrary names such as: Chamber of Secrets, Jungle Room, etc.
        * Grid related identifiers unique to the facility such as:  *TF-B1-01-A1W06F*

    3. These attributes can be embedded as properties of the polylines within the drawing or can be maintaine

Supported Space Types
----------------------

* Buildings
* Floors of buildings
* Stairways
* Elevators
* Offices
* Classrooms
* Laboratories
* Production Floors
* Bathrooms
* Break rooms
* Cafeterias
* Hallways

Doors
******
1. Doors are represented by their own polylines and grouped together under the "Doors" layer.
2. Ideally, each space must contain at least one doorway or opening that indicates where a person would enter or leave a space.
3. We realize that not all spaces, such as cubicals, have designated doorways assigned in drawings, therefore, the platform is designed to autonomously assign doorways to spaces that don’t include them. The assignment is made using the following rules as they apply to your facility

    - Find a wall for this space that is shared with a hallway
    - Create a door at the end of the wall to represent the door.

4. in a tabular format (EXCEL or CSV) outside of the drawing, so long as each label is associated with a polyline identifier within the drawing

Below is a representation of the same space as above showing only the polylines along with the other critical components required by the model

.. image:: images/example_floorplan_2.png
  :alt: Example floorplan.


Please note that CITAM was originally designed to identify potential transmission points within buildings associated with a manufacturing or research facilities. Your inputs in how to
make it more general for your types of facilities are welcome.

--------------------
SVG Bare Essentials
--------------------

There are several segments within the simplified SVG that the model and platform visualizers require.
Ancillary segments included in an SVG that are not represented below do not negatively impact the accuracy of the simulation, however, they could cause the simulation to run slower, and are essentially ignored by the model. It is, therefore, recommended to exclude them if possible.


SVG tag - identifies the facility and floor and defines the view box perimeter

.. code-block:: xml

    <svg description='MyMap' id='SP-01' viewBox='-16325 -9000 22583 14101' xmlns='http://www.w3.org/2000/svg' xmlns:xlink="http://www.w3.org/1999/xlink">

Style Section - used by the platform visualizers

.. code-block:: xml

    <style type='text/css'>
    .spaces {stroke:red;  stroke-width:2;  fill: grey; fill-opacity: 0.1}
    .floors {stroke:blue; stroke-width:10; fill: none; fill-opacity: 0.1}
    .doors {stroke:green;  stroke-width:2;  fill: none; fill-opacity: 0.2}
    </style>

Group elements - used to signify the floor as well as the different segments or buildings that the related path elements are representing within a campus scale drawing

.. code-block:: xml

    <g id='Contents'>
        <g id='FacilityName' class='floorplan'>
            <g id='SP-03'>
            <g class="floors">
				<path id="FI_3D29" d="M-24 24 7224 24 7224 -4824 -24 -4824Z"/>
			</g>
            <g class="spaces">
                <path ... />
            </g>
            <g class="doors">
                <path ... />
            </g>
        </g>
    </g>

Path elements - used to represent the polylines that define each of the spaces

 NOTE that each path with the unique id that is required to tie to related metadata for each space

.. code-block:: xml

    <path id='SI_60985' d='M-3359.88 -2451.25 -3251.88 -2451.25 -3251.88 -2343.25 -3359.88 -2343.25Z'/>
    <path id='SI_61037' d='M-2700.69 -1699.25 -2623.44 -1699.25 -2623.44 -1778.25 -2700.69 -1778.25Z'/>
    <path id='SI_61036' d='M-2777.94 -1699.25 -2700.69 -1699.25 -2700.69 -1778.25 -2777.94 -1778.25Z'/>
    <path id='SI_61034' d='M-3066 -2683.81 -3000.97 -2618.78 -2925.84 -2693.94 -2935.78 -2703.84 -2937.53 -2702.09 -2992.62 -2757.19Z'/>
    <path id='SI_61033' d='M-3067.84 -2832.41 -3141.22 -2759.03 -3066 -2683.81 -2992.62 -2757.19Z'/>
    <path id='SI_61032' d='M-3211.22 -2689.03 -3136 -2613.81 -3066 -2683.81 -3141.22 -2759.03Z'/>

