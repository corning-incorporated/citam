<!--  Copyright 2021. Corning Incorporated. All rights reserved.-->

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
  <div class="container-fluid">
     <div v-if="!isBackendLive">
      <h2 style="padding-top: 100px; color:white">Unable to retrieve data from backend.</h2>
      <span style="color: white"> Make sure the backend is running on localhost:8000. </span>
      <p style="color: white">If not, start the backend server with `citam dash --results [your-results-folder]`` then refresh this page.</p>
    </div>
    <div class="row" v-if="isBackendLive">
      <div class="col-sm-3 header">
        <ul class="nav nav-tabs" id="my-tab" role="tablist">
          <li class="nav-item custTab facility">
            <select
              @change="updatePolicyData()"
              v-model="selectedFacility"
              class="nav-link"
            >
              <option v-for="(item, id) in overviewData.facilities" :key="id">
                {{ item.facilityName }}
              </option>
            </select>
          </li>
        </ul>
      </div>
      <div class="col-sm-9" style="margin-left: -30px">
        <ul class="nav nav-tabs" id="my-tab" role="tablist">
          <li class="nav-item custTab">
            <select
              @change="updateRunData()"
              v-model="selectedSimulation"
              class="nav-link"
            >
              <option v-for="(item, id) in policies" :key="id" v-bind:value="item.policyHash">
                {{item.simulationName}} ({{ item.policyHash.slice(-4)}})
              </option>
            </select>
          </li>
          <li class="nav-item custTab">
            <select
              @change="runSimulation($event)"
              v-model="selectedRun"
              class="nav-link"
            >
              <option v-for="(item, id) in simRuns" :key="id">
                {{ item.runName }}
              </option>
            </select>
          </li>
        </ul>
      </div>
    </div>
    <div class="row" v-if="isBackendLive">
      <div class="col-sm-3 subHeader" v-if="selectedFacility != ''">
        <div class="input">Inputs</div>
        <general-policy
          :policyHash="polHash"
          :runID="runId"
        >
        </general-policy>
      </div>
      <div class="col-sm-9 subHeader">
        <div style="margin-left: -30px">
          <div class="vizTab">Visualizer</div>
        </div>
        <div v-if="showSimulation" style="height: 100%">
          <visualizer :simId="runId"></visualizer>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Vue from "vue";
// import Simulations from "./simulations/Simulations.vue";
import GeneralPolicy from "./GeneralPolicy.vue";
// import FloorPlans from "./FloorPlans.vue";
// import Overview from "./Overview.vue";
import Visualizer from './run/Visualizer.vue';

export default {
  name: "Home",
  components: { GeneralPolicy, Visualizer },
  data() {
    return {
      selectedComponent: "simulations",
      facilities: [],
      selectedFacility: "",
      overviewSimObj: {},
      showSimulation: false,
      statsList: [],
      polHash: "",
      policies: [],
      selectedSimulation: "",
      selectedRun: "",
      selectedPolicy: null,
      simRuns: [],
      policyList: [],
      runList: [],
      policyData: {},
      overviewData: { facilities: [] },
      isBackendLive: true,
      runId: null

    };
  },
  created() {
    // If facilities already exists, avoid fetching data from API's again
    if (this.$store.state.facilities === null) {
      this.fetchData();
    } else {
      this.overviewData.facilities = this.$store.state.facilities;
      this.policyList = this.$store.state.policyList;
      this.getRunList();
      this.setDefaultValues(this.overviewData.facilities);
    }
  },
  methods: {
    // Set first facility from the list, first policy and it's first run by default and show the
    // simulation map for the landing page
    setDefaultValues(facilities) {
      if (facilities.length > 0) {
        this.showSimulation = true;
        this.policies = facilities[0].policies;
        this.simRuns = this.policies[0].simulationRuns;
        this.selectedFacility = facilities[0].facilityName;
        this.selectedSimulation = this.policies[0].policyHash;
        this.polHash = this.policies[0].policyHash;
        this.selectedPolicy = this.policies[0];
        this.selectedRun = this.simRuns[0].runName;
        this.runId = this.simRuns[0].runID;
        this.overviewSimObj = {
          policyHash: this.polHash,
          runId: this.runId,
        };
      }
    },

    // Copied from overiew - update functions

    // update policy data if a different facility is selected - ToDo - trigger from facility options method
    updatePolicyData() {
      this.policies = this.overviewData.facilities.find(
        (item) => item.facilityName == this.selectedFacility
      ).policies;
      this.selectedSimulation = this.policies[0].policyHash;
      this.simRuns = this.policies[0].simulationRuns;
      this.polHash = this.policies[0].policyHash;
      this.runId = this.simRuns[0].runID;
      this.selectedPolicy = this.policies[0];
      this.overviewSimObj = {
        policyHash: this.polHash,
        runId: this.runId,
      };
    },

    // update simulation runs data if a different policy is selected - ToDo - trigger from simulations options method
    updateRunData() {
      this.simRuns = this.policies.find(
        (item) => item.policyHash == this.selectedSimulation
      ).simulationRuns;
      this.selectedRun = this.simRuns[0].runName;
      this.runId = this.simRuns[0].runID;
      this.polHash = this.selectedSimulation;
      this.selectedPolicy = this.policies.find(
        (item) => item.policyHash == this.polHash
      );
      this.overviewSimObj = {
        policyHash: this.polHash,
        runId: this.runId,
      };
    },

    // run the simulation for the selected run to show the visualization
    runSimulation(event) {
      this.runId = this.simRuns[event.target.selectedIndex].runID;
      this.overviewSimObj = {
        policyHash: this.polHash,
        runId: this.runId,
      };
    },

    fetchData() {
      axios
        .get("/list") //get list of policies, simulations, facilities
        .then((response) => {
          this.policyList = response.data.map((list) => list);
          this.$store.commit("setPolicyList", this.policyList);
          return axios.all(response.data.map((x) => axios.get(`/${x.RunID}`)));
        })
        .then((runResponse) => {
          // eslint-disable-next-line no-unused-vars
          this.runList = runResponse.map((run) => run.data);
          return axios.all(
            runResponse.map((x) => axios.get(`/${x.data.RunID}/statistics`))
          );
        })
        .then((response) => {
          response.map((statCard, i) => {
            statCard.data.runID = response[i].config.url
              .match(/(?<=\/)(.*)(?=\/)/)[0]
              .toString();
            this.statsList.push(statCard.data);
          });
          this.$store.commit("setStatsList", this.statsList);
          this.getOverviewData();

          this.$store.commit("setFacilities", this.overviewData.facilities); // Store it in a centralized variable to use in other components
          this.getRunList();
          this.setDefaultValues(this.overviewData.facilities);
        })
        .catch( () => {
          this.isBackendLive = false;
        } );
    },

    getOverviewData() {
      this.overviewData = { facilities: [] };
      this.policyList.forEach((policy) => {
        if (this.pushUniqueFacilities(policy.FacilityName)) {
          this.overviewData.facilities.push({
            facilityName: policy.FacilityName,
            policies: [
              {
                simulationName: policy.SimulationName,
                policyHash: policy.SimulationHash,
                simulationRuns: [],
              },
            ],
          });
        }
        this.overviewData.facilities.forEach((facility) => {
          if (
            facility.facilityName === policy.FacilityName &&
            this.pushUniquePolicies(facility, policy.SimulationHash)
          ) {
            facility.policies.push({
              simulationName: policy.SimulationName,
              policyHash: policy.SimulationHash,
              simulationRuns: [],
            });
          }
          facility.policies.forEach((pol) => {
            if (policy.SimulationHash === pol.policyHash) {
              pol.simulationRuns.push({
                runName: policy.RunName,
                runID: policy.RunID,
              });
              pol.simulationRuns.agents = 0;
              pol.simulationRuns.totalFloors = 0;
              pol.simulationRuns.totalTimeStep = 0;
              pol.simulationRuns.totalScaleMultiplier = 0;
              pol.simulationRuns.individuals = 0;
            }
          });
        });
      });
    },

    getRunList() {
      // build stats object for each simulation run within each policies for each facility
      this.overviewData.facilities.forEach((facility) => {
        facility.policies.forEach((policy) => {
          policy.simulationRuns.forEach((sim) => {
            this.runList.forEach((run) => {
              if (run.RunID === sim.runID) {
                Vue.set(sim, "floors", run.Floors);
                Vue.set(sim, "totalSteps", run.TotalTimesteps);
                Vue.set(sim, "scaleMultiplier", run.ScaleMultiplier);
                Vue.set(sim, "agents", run.NumberOfAgents);
                Vue.set(sim, "numberOfEntrances", run.NumberOfEntrances);
                policy.simulationRuns.totalFloors = sim.floors.length;
                policy.simulationRuns.totalSteps = (
                  sim.totalSteps / 3600
                ).toFixed(2);
                policy.simulationRuns.numberOfEntrances = sim.numberOfEntrances;
                policy.simulationRuns.agents = sim.agents;
              }
            });
          });
        });
      });
    },

    pushUniqueFacilities(item) {
      var index = this.overviewData.facilities
        .map(function (e) {
          return e.facilityName;
        })
        .indexOf(item);
      return index === -1 ? true : false;
    },

    pushUniquePolicies(facility, item) {
      var index = facility.policies
        .map(function (e) {
          return e.policyHash;
        })
        .indexOf(item);
      return index === -1 ? true : false;
    },
  },
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap");
.navbar {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.navbar-light {
  background-color: #f0f0f0;
}

.nav-tabs {
  border-bottom: none !important;
}

.nav-tabs .nav-item {
  width: 340px;
  height: 50px;
  border-right: 1px solid black !important;
  background-color: #ebeff2;
}
.nav-tabs .nav-item.custTab {
  text-align: left;
  height: 50px;
  background-color: #32404d;
}

.nav-tabs .nav-item.facility {
  width: 100%;
}

.nav-tabs .nav-item.custTab select {
  font-family: Inter;
  font-weight: 600;
  font-size: 16px;
  color: #ffffff;
  background-color: #32404d;
}

.nav-tabs .nav-link {
  color: #607080;
  font-family: Inter;
  font-weight: 600;
  font-size: 16px;
  border: none;
  cursor: pointer;
}
.nav-tabs .nav-link.active {
  color: #0080ff;
  background-color: #fff;
  font-family: Inter;
  font-weight: 600;
  font-size: 16px;
  height: 50px;
}

.nav-tabs .nav-link:hover {
  border: none;
}

*:focus {
  outline: none;
}

.footer {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 160px;
  line-height: 60px;
  background-color: #f0f0f0;
}

.flex-container {
  display: flex;
}

.flex-container > div {
  background-color: #c4c2c2;
  margin: 10px;
  padding: 20px;
  font-size: 20px;
  cursor: pointer;
}

.input {
  color: #607080;
  background-color: #ebeff2;
  height: 50px;
  width: 100px;
  padding: 10px;
  text-align: left;
}
.vizTab {
  color: #607080;
  background-color: #ebeff2;
  width: 150px;
  height: 50px;
  padding: 10px;
  text-align: left;
}
.subHeader {
  background-color: #98a6b3;
  padding: 0px 0px 0px 0px !important ;
}
.header {
  padding-left: 0px !important;
}
</style>
