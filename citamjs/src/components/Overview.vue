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
  <main>
    <div id="overviewLayout">
      <div id="title">
        <span>Overview of Simulation Results</span>Runs are grouped by policy.
        Select a row to view individual runs.
      </div>
      <div class="container-fluid">
        <div class="row">
          <div class="table-responsive">
            <table class="table table-bordered" v-if="statsList">
              <thead>
                <tr class="tableHeader">
                  <th colspan="2"></th>
                  <th id="metricCols">KEY METRICS</th>
                  <th colspan="4">KEY POLICY INPUTS</th>
                </tr>
                <tr>
                  <th class="noBorder">View runs</th>
                  <th class="noBorder">Policies</th>
                  <th v-for="(att, id) in metricAttributes" :key="id">
                    <div class="th-container">{{ att }}</div>
                  </th>
                  <th
                    v-for="(header, id) in policyInputHeaders"
                    :key="'p' + id"
                  >
                    <div class="th-container">{{ header }}</div>
                  </th>
                </tr>
              </thead>
              <tbody v-for="(item, idx) in policyData.policies" :key="idx">
                <tr>
                  <td class="noBorder">
                    <button type="button" class="btn" @click="viewRuns(idx)">
                      <span><font-awesome-icon icon="chevron-down" /></span>
                    </button>
                  </td>
                  <td class="noBorder">
                    <button
                      type="button"
                      class="btn btn-link"
                      @click="showPolicyInfo(item.policyName)"
                    >
                      {{ item.policyName }}
                    </button>
                    <br />
                    {{ item.simulationRuns.length }} Runs
                  </td>
                  <td
                    v-for="(avg, id) in item.simulationRuns.average"
                    :key="id"
                  >
                    {{ avg }}
                  </td>
                  <td>{{ item.simulationRuns.individuals }}</td>
                  <td>{{ item.simulationRuns.totalFloors }}</td>
                  <td>{{ item.simulationRuns.totalTimeStep }}</td>
                  <td>{{ item.simulationRuns.totalScaleMultiplier }}</td>
                </tr>
                <template v-if="subRows.includes(idx)">
                  <tr
                    v-for="(sim, index) in simRuns[0].simulationRuns"
                    :key="index"
                  >
                    <td class="noBorder"></td>
                    <td class="noBorder">
                      <button
                        type="button"
                        class="btn btn-link simBtn"
                        @click="
                          showSimulations(
                            item.policyName,
                            sim.simName,
                            'simMaps'
                          )
                        "
                      >
                        {{ sim.simName }}
                      </button>
                    </td>
                    <td
                      v-for="(stats, ind) in sim.statisctics"
                      :key="sim.simName + ind"
                    >
                      {{ stats.value }}
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script>
import Vue from "vue";
import axios from "axios";
import _ from "lodash";

export default {
  name: "Overview",
  props: {
    selectedFacility: String,
  },
  data() {
    return {
      metricHeaders: [
        "Total Contact (minutes)",
        "Average Contacts/Agent",
        "Average Contact Duration (min/Agent)",
        "Average Number of People/Agent",
      ],
      metricAttributes: [],
      policyInputHeaders: [
        "Individuals",
        "Total Floors",
        "Time Step",
        "Scale Multiplier",
      ],
      simRuns: [],
      subRows: [],
      policyList: [],
      statsList: [],
      runList: [],
      policyData: {},
      overviewData: { facilities: [] },
      hasSims: false,
    };
  },
  watch: {
    selectedFacility(newFacility) {
      this.policyData = {
        policies: this.overviewData.facilities.find(
          (item) => item.facilityName == newFacility
        ).policies,
      };
      this.subRows = [];
      this.calculatePolicyAvg();
    },
  },
  created() {
    axios
      .get("/list") //get list of policies, simulations, facilities
      .then((response) => {
        this.policyList = response.data.map((list) => list);
        return axios.all(response.data.map((x) => axios.get(`/${x.sim_id}`)));
      })
      .then((runResponse) => {
        // eslint-disable-next-line no-unused-vars
        this.runList = runResponse.map((run) => run.data);
        return axios.all(
          runResponse.map((x) =>
            axios.get(`/${x.data.SimulationID}/statistics`)
          )
        );
      })
      .then((response) => {
        response.map((statCard, i) => {
          statCard.data.sim_id = response[i].config.url
            .match(/(?<=\/)(.*)(?=\/)/)[0]
            .toString();
          this.statsList.push(statCard.data);
        });

        this.getOverviewData();
        this.$store.commit("setFacilities", this.overviewData.facilities); // Store it in a centralized variable to use in other components
        this.$emit("setFacilities", this.overviewData.facilities); // To display facility list in the dropdown

        if (this.selectedFacility) {
          this.policyData = {
            policies: this.overviewData.facilities.find(
              (item) => item.facilityName == this.selectedFacility
            ).policies,
          };
        } else {
          this.policyData = {
            policies: this.overviewData.facilities[0].policies,
          }; // Display first facility by default
        }
        this.calculatePolicyAvg();
      })
  },
  methods: {
    sortTable(att) {
      this.policyList = _.sortBy(this.policyList, [att]);
      this.runList = _.sortBy(this.runList, [att]);
      this.statsList = _.sortBy(this.statsList, [att]);
      this.policyData;
      this.metricAttributes;
      this.overviewData.facilities = _.sortBy(this.overviewData.facilities, [
        att,
      ]);
      this.$store.state.facilities;
    },

    viewRuns(idx) {
      const index = this.subRows.indexOf(idx);
      if (index > -1) {
        this.subRows.splice(index, 1);
        this.simRuns = [];
      } else {
        this.subRows = [];
        this.subRows.push(idx);
        this.simRuns = [];
        this.simRuns.push(this.policyData.policies[idx]);
      }
    },

    getOverviewData() {
      this.overviewData = { facilities: [] };
      this.policyList.forEach((policy) => {
        if (this.pushUniqueFacilities(policy.facility_name)) {
          this.overviewData.facilities.push({
            facilityName: policy.facility_name,
            policies: [{ policyName: policy.policy_id, simulationRuns: [] }],
          });
        }
        this.overviewData.facilities.forEach((facility) => {
          if (
            facility.facilityName === policy.facility_name &&
            this.pushUniquePolicies(facility, policy.policy_id)
          ) {
            facility.policies.push({
              policyName: policy.policy_id,
              simulationRuns: [],
            });
          }
          facility.policies.forEach((pol) => {
            if (policy.policy_id === pol.policyName) {
              pol.simulationRuns.push({ simName: policy.sim_id });
              pol.simulationRuns.totalIndividuals = 0;
              pol.simulationRuns.totalFloors = 0;
              pol.simulationRuns.totalTimeStep = 0;
              pol.simulationRuns.totalScaleMultiplier = 0;
              pol.simulationRuns.individuals = 0;
            }
          });
        });
      });

      // build stats object for each simulation run within each policies for each facility
      this.overviewData.facilities.forEach((facility) => {
        facility.policies.forEach((policy) => {
          policy.simulationRuns.forEach((sim) => {
            this.runList.forEach((run) => {
              if (run.sim_id === sim.simName) {
                Vue.set(sim, "floors", run.floors);
                Vue.set(sim, "timeStep", run.TimestepInSec);
                Vue.set(sim, "scaleMultiplier", run.scaleMultiplier);
                Vue.set(sim, "individuals", run.NumberOfEmployees);
                Vue.set(sim, "individuals", run.NumberOfEmployees);

                this.statsList.forEach((stats) => {
                  if (this.metricAttributes.length == 0) {
                    stats.forEach((stat) =>
                      this.metricAttributes.push(stat.name)
                    );
                  }
                  if (stats.sim_id === sim.simName) {
                    stats.forEach((item) => {
                      Vue.set(sim, item.name, item.value);
                    });
                    Vue.set(sim, "statisctics", stats);
                  }
                });
                policy.simulationRuns.totalFloors = sim.floors.length;
                policy.simulationRuns.totalTimeStep = sim.timeStep;
                policy.simulationRuns.totalScaleMultiplier =
                  sim.scaleMultiplier;
                policy.simulationRuns.individuals = sim.individuals;                
              }
            });
          });
        });
      });
      document.getElementById(
        "metricCols"
      ).colSpan = this.metricAttributes.length;
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
          return e.policyName;
        })
        .indexOf(item);
      return index === -1 ? true : false;
    },

    calculatePolicyAvg() {
      var stat_list = [];
      for (var p of this.policyData.policies) {
        for (var sruns of p.simulationRuns) {
          stat_list.push(
            _.mapValues(_.keyBy(sruns.statisctics, "name"), "value")
          );
        }
        var dynamicKeys = _.keys(stat_list[0]);
        var sums = {};
        _.each(stat_list, function (item) {
          _.each(dynamicKeys, function (statKeys) {
            sums[statKeys] = (sums[statKeys] || 0) + item[statKeys];
          });
        });        
        p.simulationRuns.average = sums;
        stat_list = [];
      }
    },

    showSimulations(policyName, simId, type) {
      this.$emit("showSims", {
        policyName: policyName,
        simId: simId,
        type: type,
      });
    },

    showPolicyInfo(policyName) {
      this.$emit("showPolicy", policyName);
    },
  },
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap");
#overviewLayout {
  background-color: #ffff;
}
#title {
  font-family: Inter;
  text-align: left;
  padding: 10px;
  color: #607080;
}
#title span {
  color: black !important;
  font-family: Inter;
  font-weight: 600;
  font-size: 16px;
  margin: 0px 10px 0px 5px;
  padding: 10px 0 10px 0;
}
.subTitle {
  background-color: #ebeff2;
}
.subTitle div {
  color: #607080;
  font-family: Inter;
  text-align: left;
  padding: 10px 0 10px 15px;
}
.subTitle div button {
  padding: 0px !important;
  font-family: Inter;
}
.th-container {
  height: 100%;
  vertical-align: middle;
  text-align: center;
  display: flex;
  align-items: center;
}
.policyBtn {
  line-height: 0.7;
}
.sort-right {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.table {
  margin-bottom: 0px !important;
}
.table .col-sm-2,
.table .col-sm-5 {
  float: left;
  padding: 0px !important;
}
.table thead th {
  font-family: Inter;
  font-weight: 500;
  font-size: 13px;
  line-height: 12px;
  align-items: flex-end;
  text-align: center;
  color: #607080;
}
.tableHeader {
  background-color: #ebeff2;
}
.simBtn {
  margin-right: 50px;
}
.btn:focus {
  box-shadow: none !important;
}
.noBorder {
  border-left: none !important;
  border-right: none !important;
}
</style>

