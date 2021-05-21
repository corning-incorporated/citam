<!--  Copyright 2020. Corning Incorporated. All rights reserved.-->

<!--  This software may only be used in accordance with the licenses granted by-->
<!--  Corning Incorporated. All other uses as well as any copying, modification or-->
<!--  reverse engineering of the software is strictly prohibited.-->

<!--  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR-->
<!--  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,-->
<!--  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL-->
<!--  CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN-->
<!--  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION-->
<!--  WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.-->
<!--  ==============================================================================-->

<template>
  <div id="policiesLayout">
    <div id="title">View and Create Policy</div>
    <div class="container-fluid">
      <div class="row header">
        <div class="col-sm-2 policy">
          <div class="policyBtn">
            <!-- <button type="button" class="btn btn-link">Add Policy</button> -->
          </div>
          <ul class="ulStyle">
            <li v-for="(policy, id) in policyData.policies" :key="id">
              <a
                class="polName"
                :id="id"
                href="#"
                @click="getPolicyDetails(policy.policyHash, id)"
              >
                {{ policy.policyHash }}
              </a>
            </li>
          </ul>
        </div>
        <div class="col-sm-10">
          <div class="polHeading">GENERAL POLICY</div>
          <div class="polPanel">
            <div>
              <span class="headingFont">ENTRANCES</span>
              <template>
                <div class="row polSubSection">
                  <div class="col">
                    <span>Space name</span>
                    <div
                      class="polValue"
                      v-for="(entrance, id) in policyDetails.general.entrances"
                      :key="id"
                    >
                      {{ entrance.name }}
                    </div>
                  </div>
                  <div class="col">
                    <span>Floor</span>
                    <div
                      class="polValue"
                      v-for="(entrance, id) in policyDetails.general.entrances"
                      :key="id"
                    >
                      {{ entrance.floor }}
                    </div>
                  </div>
                  <div class="col"></div>
                </div>
              </template>
            </div>
            <div>
              <span class="headingFont">DAY LENGTH</span>
              <div class="row polSubSection">
                <div class="col">
                  <span>Total Steps</span>
                  <div class="polValue">
                    {{ policyDetails.general.daylength }}
                  </div>
                </div>
                <div class="col">
                  <span>Total Hours</span>
                  <div class="polValue">
                    {{ policyDetails.general.daylength / 3600 }}
                  </div>
                </div>
                <div class="col"></div>
              </div>
            </div>
            <div>
              <span class="headingFont">NUMBER OF AGENTS</span>
              <div class="row polSubSection">
                <div class="col">
                  <span>Quantity</span>
                  <div class="polValue">
                    {{ policyDetails.general.NumberOfEmployees }}
                  </div>
                </div>
                <div class="col"></div>
                <div class="col"></div>
              </div>
            </div>
            <div>
              <span class="headingFont">CONTACT DISTANCE</span>
              <div class="row polSubSection">
                <div class="col">
                  <span>Distance (Meters)</span>
                  <div class="polValue">
                    {{ policyDetails.general.contact_distance }}
                  </div>
                </div>
                <div class="col"></div>
                <div class="col"></div>
              </div>
            </div>
            <div>
              <span class="headingFont">SHIFTS</span>
              <div class="row polSubSection">
                <div class="col">
                  <span>Name of Shift</span>
                  <div
                    class="polValue"
                    v-for="(shift, id) in policyDetails.general.shifts"
                    :key="id"
                  >
                    {{ shift.name }}
                  </div>
                </div>
                <div class="col">
                  <span>Shift Start time</span>
                  <div
                    class="polValue"
                    v-for="(shift, id) in policyDetails.general.shifts"
                    :key="id"
                  >
                    {{ shift.start_time }}
                  </div>
                </div>
                <div class="col">
                  <span>Percent of agents assigned to shift</span>
                  <div
                    class="polValue"
                    v-for="(shift, id) in policyDetails.general.shifts"
                    :key="id"
                  >
                    {{ shift.percent_workforce }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="polHeading">MEETINGS POLICY</div>
          <div class="polPanel">
            <div class="polDesc">
              The meetings policy controls when and where meetings take place as
              well who attends them. A meeting is defined as any gathering of
              people in the same physical space. The parameters listed below are
              used to generate meetings and attendee list randomly. In the
              future, the possibility will be given to manually add specific
              meetings that always take place (e.g. classroom instructions).
            </div>
            <div>
              <span class="headingFont">MEETING DURATION</span>
              <div class="row polSubSection">
                <div class="col">
                  <span>Minimum duration</span>
                  <div class="polValue">
                    {{ policyDetails.meetings.min_meeting_duration }}
                  </div>
                </div>
                <div class="col">
                  <span>Maximum duration</span>
                  <div class="polValue">
                    {{ policyDetails.meetings.max_meeting_length }}
                  </div>
                </div>
                <div class="col"></div>
              </div>
              <div class="row polSubSection">
                <div class="col">
                  <span>Average meeting per room per day</span>
                  <div class="polValue">
                    {{ policyDetails.meetings.avg_meetings_per_room }}
                  </div>
                </div>
                <div class="col"></div>
                <div class="col"></div>
              </div>
              <div class="row polSubSection">
                <div class="col">
                  <span>Average meeting rooms used (percentage)</span>
                  <div class="polValue">
                    {{
                      policyDetails.meetings.percent_meeting_rooms_used * 100 +
                      "%"
                    }}
                  </div>
                </div>
                <div class="col"></div>
                <div class="col"></div>
              </div>
              <div class="row polSubSection">
                <div class="col">
                  <span>Average meeting per agent</span>
                  <div class="polValue">
                    {{ policyDetails.meetings.avg_meetings_per_person }}
                  </div>
                </div>
                <div class="col"></div>
                <div class="col"></div>
              </div>
              <div class="row polSubSection">
                <div class="col">
                  <span>Minimum attendees per meeting</span>
                  <div class="polValue">
                    {{ policyDetails.meetings.min_attendees_per_meeting }}
                  </div>
                </div>
                <div class="col"></div>
                <div class="col"></div>
              </div>
            </div>
          </div>
          <div class="polHeading">SCHEDULING POLICY</div>
          <div class="polPanel">
            <div class="polDesc">
              The scheduling policy controls what items are added to people’s
              schedules and itineraries. It can be used for example to disallow
              meetings or cafeteria visits. A scheduling policy is made of a
              list of scheduling rules where each rule is as follows:
            </div>
            <div class="row polSubSection">
              <div class="col">
                <span>Purpose</span>
                <div
                  class="polValue"
                  v-for="(schedule, id) in policyDetails.scheduling"
                  :key="id"
                >
                  {{ schedule.purpose }}
                </div>
              </div>
              <div class="col">
                <span>Minimum duration</span>
                <div
                  class="polValue"
                  v-for="(schedule, id) in policyDetails.scheduling"
                  :key="id"
                >
                  {{ schedule.min_duration }}
                </div>
              </div>
              <div class="col">
                <span>Maximum duration</span>
                <div
                  class="polValue"
                  v-for="(schedule, id) in policyDetails.scheduling"
                  :key="id"
                >
                  {{ schedule.max_duration }}
                </div>
              </div>
              <div class="col">
                <span>Minimum Instance</span>
                <div
                  class="polValue"
                  v-for="(schedule, id) in policyDetails.scheduling"
                  :key="id"
                >
                  {{ schedule.min_instances }}
                </div>
              </div>
              <div class="col">
                <span>Maximum Instance</span>
                <div
                  class="polValue"
                  v-for="(schedule, id) in policyDetails.scheduling"
                  :key="id"
                >
                  {{ schedule.max_instances }}
                </div>
              </div>
            </div>
          </div>
          <div class="polHeading">TRAFFIC POLICY</div>
          <div class="polPanel">
            <div class="polDesc">
              A traffic policy is made of list of circulation rules where each
              rule is as follows:
            </div>
            <div class="row polSubSection">
              <div class="col">
                <span>Floor</span>
                <div
                  class="polValue"
                  v-for="(traffic, id) in policyDetails.traffic"
                  :key="id"
                >
                  {{ traffic.floor }}
                </div>
              </div>
              <div class="col">
                <span>Aisle SSegment Id</span>
                <div
                  class="polValue"
                  v-for="(traffic, id) in policyDetails.traffic"
                  :key="id"
                >
                  {{ traffic.aisle }}
                </div>
              </div>
              <div class="col">
                <span>Direction</span>
                <div
                  class="polValue"
                  v-for="(traffic, id) in policyDetails.traffic"
                  :key="id"
                >
                  {{ traffic.value }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import _ from "lodash";
import axios from "axios";

export default {
  props: {
    selectedFacility: String,
    polName: String,
  },
  data() {
    return {
      policyData: {},
      selectedPolicyData: {
        generalPolicy: {
          spaceName: "",
          floor: "",
          entranceTime: "",
          leaveTime: "",
          quantity: "",
          distance: "",
          shiftName: "",
          shiftStartTime: "",
          shiftAgentPercent: "",
        },
        meetingsPolicy: {
          minDuration: "",
          maxDuration: "",
          avgMtngsPerRoomPerDay: "",
          avgMtngRooms: "",
          avgMtngsPerAgent: "",
          minMtngAttendees: "",
        },
        schedulingPolicy: {
          purpose: "",
          minDuration: "",
          maxDuration: "",
          minInstance: "",
          maxInstance: "",
        },
        trafficPolicy: { floor: "", aisleId: "", direction: "" },
      },
      polIndex: "",
      policyDetails: {},
    };
  },
  watch: {
    selectedFacility(newFacility) {
      this.policyData = {
        policies: this.$store.state.facilities.find(
          (item) => item.facilityName == newFacility
        ).policies,
      };
      this.selectedPolicyData.policyInfo = this.policyData.policies[0];
      this.setActiveSelectedPolicy(0);
    },
  },
  created() {
    this.policyData = {
      policies: this.$store.state.facilities.find(
        (item) => item.facilityName == this.selectedFacility
      ).policies,
    };
    if (_.isEmpty(this.polName)) {
      this.selectedPolicyData.policyInfo = this.policyData.policies[0];
      axios
      .get(`/${this.selectedPolicyData.policyInfo.simulationRuns[0].runID}/policy`) //get policy info with any of the simid
      .then((response) => {
        this.policyDetails = response.data;
        return response.data;
      })
       .catch((error) => {
         console.log(error.response)
         alert('No policy data found, please check if policy.json file exists')
       });
    } else {
      this.selectedPolicyData.policyInfo = this.policyData.policies.find(
        (item) => item.policyHash == this.polName
      );
      axios
      .get(`/${this.selectedPolicyData.policyInfo.simulationRuns[0].runID}/policy`) //get policy info with any of the simid
      .then((response) => {
        this.policyDetails = response.data;
        return response.data;
      })
        .catch((error) => {
         console.log(error.response)
         alert('No policy data found, please check if policy.json file exists')
       });
      this.polIndex = this.policyData.policies.findIndex(
        (item) => item.policyHash == this.polName
      );
    }
  },
  mounted() {
    // wait till Simulations component is loaded and update the DOM element
    this.$nextTick(function () {
      this.polIndex == ""
        ? this.setActiveSelectedPolicy(0)
        : this.setActiveSelectedPolicy(this.polIndex);
    });
  },
  methods: {
    getPolicyDetails(policyName, Id) {
      this.selectedPolicyData.policyInfo = this.policyData.policies.find(
        (item) => item.policyHash == policyName
      );
      this.setActiveSelectedPolicy(Id);
    },

    setActiveSelectedPolicy(Id) {
      var current = document.getElementsByClassName("setActive");
      if (current.length > 0) {
        current[0].className = current[0].className.replace("setActive", "");
      }
      var polId = document.getElementById(Id);
      polId.className += " setActive";
    },
  },
};
</script>

><style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap");
#policiesLayout {
  background-color: #ffff;
  margin-bottom: 80px;
}

#title {
  color: black !important;
  font-family: Inter;
  font-weight: 600;
  font-size: 16px;
  margin: 0px 10px 0px 5px;
  padding: 10px;
  text-align: left;
}

.polHeading {
  text-align: left;
  background-color: #ebeff2;
  font-family: Inter;
  color: #607080;
  height: 50px;
  padding: 10px;
  border-left: 1px solid lightgray;
}

.headingFont {
  color: #607080;
}
.policyBtn {
  font-family: Inter;
  font-weight: bold;
  color: #0080ff;
  background-color: #ebeff2 !important;
  height: 50px;
}

#policiesLayout .col-sm-2,
.col-sm-10 {
  text-align: left;
  background-color: white;
  padding-right: 0px !important;
  padding-left: 0px !important;
}

.polName {
  font-family: Inter;
  color: #607080;
  font-weight: 600;
  margin: 0 5px 0 5px;
}

.polName.setActive {
  color: #0080ff;
}
.polName:hover {
  color: #0080ff;
  text-decoration: none;
}
.policy:focus {
  color: #0080ff;
}
.ulStyle {
  list-style-type: none;
  padding-inline-start: 5px;
  background-color: #f7f9fa;
  text-align: center;
}

.ulStyle li {
  height: 45px;
  padding: 10px 0 10px 0;
  border-bottom: 2px solid white;
}

.ulStyle li span {
  color: #607080;
}

.ulStyle li span:hover {
  color: #0080ff;
  cursor: pointer;
}

.polPanel {
  padding: 0 30px 30px 30px;
}

.polPanel > div {
  margin-top: 30px;
}

.polDesc {
  font-family: Inter;
  color: #607080;
}
.polValue {
  background-color: #f7f9fa;
  height: 40px;
  padding: 5px;
}

.polSubSection {
  margin-top: 25px;
}

.polSubSection span {
  color: #607080;
  font-size: 14px;
  font-family: Inter;
}

*:focus {
  outline: none;
}
</style>
