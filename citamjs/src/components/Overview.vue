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
        <span>Policy Results</span>Select metric (header) to determine the best policy
      </div>
      <div class="container-fluid">
        <div class="row subTitle">
          <div class="col-sm-2 policy">
            <button type="button" class="btn btn-link">Add Policy</button>
          </div>
          <div class="col-sm-5">KEY METRICS</div>
          <div class="col-sm-5">KEY POLICY INPUTS</div>
        </div>
        <div class="row">
          <div class="table-responsive">
            <table class="table table-bordered" v-if="statsList">
              <thead>
                <tr>
                  <th>View runs</th>
                  <th v-for="att in policyHeaders" :key="att">
                    <div class="th-container"> {{ att }}
                      <span class="sort-right"><button class="btn btn-sm btn-link" @click="sortTable(att)">
                        <font-awesome-icon icon="sort" /></button></span>
                    </div>
                  </th>
                  <th v-for="att in metricsHeaders" :key="att">
                    <div class="th-container"> {{ att }}
                      <span class="sort-right"><button class="btn btn-sm btn-link" @click="sortTable(att)">
                        <font-awesome-icon icon="sort" /></button></span>
                    </div>
                  </th>
                  <th v-for="att in inputsHeaders" :key="att">
                    <div class="th-container">{{ att }}
                      <span class="sort-right"><button class="btn btn-sm btn-link" @click="sortTable(att)">
                        <font-awesome-icon icon="sort" /></button></span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in policyData.policies" :key="idx.policyName">
                  <td>
                    <button type="button" class="btn" @click="viewRuns(policy.policy_id)">
                      <span><font-awesome-icon icon="chevron-down" /></span>
                    </button>
                  </td>
                  <td>{{ item.policyName }}</td>
                  <td>{{ item.simulationRuns.length }}</td>
                  <td>{{ item.simulationRuns[0].overall_total_contact_duration }}</td>
                  <td>{{ item.simulationRuns[0].avg_n_contacts_per_agent }}</td>
                  <td>{{ item.simulationRuns[0].avg_contact_duration_per_agent }}</td>
                  <td>{{ item.simulationRuns[0].avg_number_of_people_per_agent }}</td>
                  <td>ind</td>
                  <td>{{ item.simulationRuns[0].totalFloors }}</td>
                  <td>{{ item.simulationRuns[0].timeStep }}</td>
                  <td>{{ item.simulationRuns[0].scaleMultiplier }}</td>
                </tr>
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
  data() {
    return {
      policyHeaders: ["Policies", "Number of Policy Simulation Runs"],
      metricsHeaders: [
        "Total Contact (minutes)",
        "Average Contacts/Agent",
        "Average Contact Duration (min/Agent)",
        "Average Number of People/Agent",
      ],
      inputsHeaders: [
        "Individuals",
        "Total Floors",
        "Time Step",
        "Scale Multiplier",
      ],
      policyList: [],
      statsList: [],
      runList: [],
      policyData: {},
      overviewData: { facilities: [] },
    };
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
      })
      .catch(function (error) {
        console.log(error);
      });
  },
  methods: {
    sortTable(att) {
      this.policyList = _.sortBy(this.policyList, [att]);
      this.runList = _.sortBy(this.runList, [att]);
      this.statsList = _.sortBy(this.statsList, [att]);
      this.policyData;
      this.overviewData.facilities = _.sortBy(this.overviewData.facilities, [
        att,
      ]);
    },

    viewRuns() {
      alert("Viewing Runs");
    },

    getOverviewData() {
      this.overviewData = { facilities: [] };
      this.policyList.forEach((policy) => {
        if (this.pushUniqueItems(policy.facility_name, "facility")) {
          this.overviewData.facilities.push({
            facilityName: policy.facility_name,
            policies: [{ policyName: policy.policy_id, simulationRuns: [] }],
          });
          this.getOverviewPolicies(policy);
        } else {
          this.getOverviewPolicies(policy);
        }
        this.overviewData.facilities.push(this.overviewData.facilities);
        this.policyData = {
          policies: this.overviewData.facilities[0].policies,
        }; // ToDo - push data by facility selected in the dropdown
      });
    },

    getOverviewPolicies(policy) {
      this.overviewData.facilities.forEach((data, x) => {
        data.policies[x].simulationRuns.push({ simName: policy.sim_id });
        this.runList.forEach((run, y) => {
          if (run.sim_id === data.policies[x].simulationRuns[y].simName) {
            Vue.set(
              data.policies[x].simulationRuns[y],
              "totalFloors",
              run.NumberOfFloors
            );
            Vue.set(
              data.policies[x].simulationRuns[y],
              "timeStep",
              run.TimestepInSec
            );
            Vue.set(
              data.policies[x].simulationRuns[y],
              "scaleMultiplier",
              run.scaleMultiplier
            );

            this.statsList.forEach((stats, z) => {
              if (stats.sim_id === data.policies[x].simulationRuns[z].simName) {
                stats.forEach((item) => {
                  Vue.set(
                    data.policies[x].simulationRuns[y],
                    item.name,
                    item.value
                  );
                });
              }
            });
          }
        });
      });
    },

    pushUniqueItems(item, type) {
      var index = this.overviewData.facilities
        .map(function (e) {
          return type == "policy" ? e.policyName : e.facilityName;
        })
        .indexOf(item);
      return index === -1 ? true : false;
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
  /* border-right: 1px solid #DAE0E6 !important; */
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

.sort-right {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.table .col-sm-2,
.table .col-sm-5 {
  float: left;
  padding: 0px !important;
}

.table thead th {
  font-family: Inter;
  font-weight: 500;
  font-size: 10px;
  line-height: 12px;
  align-items: flex-end;
  text-align: center;
  color: #607080;
}
</style>

