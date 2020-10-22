# Copyright 2020. Corning Incorporated. All rights reserved.
#
# This software may only be used in accordance with the licenses granted by
# Corning Incorporated. All other uses as well as any copying, modification or
# reverse engineering of the software is strictly prohibited.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
# ==============================================================================


VERTICAL_AISLE = 1
HORIZONTAL_AISLE = 2
DIAGONAL_AISLE = 3

ONEWAY_TRAFFIC_POSITIVE_DIRECTION = 1
ONEWAY_TRAFFIC_NEGATIVE_DIRECTION = -1
TWO_WAY_TRAFFIC = 0

# Constants related to floorplan data

REQUIRED_SPACE_METADATA = [
    "id",
    "facility",
    "building",
    "unique_name",
    "space_function",
]

OPTIONAL_SPACE_METADATA = [
    "space_category",
    "floor",
    "department",
    "capacity",
    "square_footage",
]

SUPPORTED_SPACE_FUNCTIONS = [
    "circulation",
    "office",
    "lab",
    "restroom",
    "cafeteria",
    "stairs",
    "elevator",
    "meeting room",
    "conference room",
    "auditorium",
    "other",
]

RESTROOM_VISIT = "Restroom visit"
MEETING = "Meeting"
LAB_WORK = "Lab work"
CAFETERIA_VISIT = "Cafeteria"
OFFICE_WORK = "Office work"


DEFAULT_SCHEDULING_RULES = {
    OFFICE_WORK: {
        "purpose": OFFICE_WORK,
        "min_duration": 600,
        "max_duration": 7200,
        "min_instances": 2,
        "max_instances": 10,
    },
    RESTROOM_VISIT: {
        "purpose": RESTROOM_VISIT,
        "min_duration": 300,
        "max_duration": 900,
        "min_instances": 1,
        "max_instances": 4,
    },
    CAFETERIA_VISIT: {
        "purpose": CAFETERIA_VISIT,
        "min_duration": 900,
        "max_duration": 3600,
        "min_instances": 0,
        "max_instances": 2,
    },
    MEETING: {
        "purpose": MEETING,
        "min_duration": 1200,
        "max_duration": 7200,
        "min_instances": 1,
        "max_instances": 8,
    },
    LAB_WORK: {
        "purpose": LAB_WORK,
        "min_duration": 1200,
        "max_duration": 10800,
        "min_instances": 1,
        "max_instances": 4,
    },
}

DEFAULT_MEETINGS_POLICY = {
    # Meetings duration
    "min_meeting_duration": 15 * 60,  # 15 min
    "max_meeting_length": 7200,  # 2 hours
    "meeting_duration_increment": 15 * 60,  # 15 min
    # Meetings frequency
    "avg_meetings_per_room": 3,
    "avg_percent_meeting_rooms_used": 0.6,  # Less than 1.0
    # Meetings participants
    "avg_meetings_per_person": 3,
    "min_attendees_per_meeting": 3,
    # Meeting timing
    "min_buffer_between_meetings": 0,
    "max_buffer_between_meetings": 10800,
}

MEETING_BUFFER = 60 * 15
