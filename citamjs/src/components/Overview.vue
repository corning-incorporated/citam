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
                    <button type="button" class="btn" @click="viewRuns(idx, item.policyName)">
                      <span><font-awesome-icon icon="chevron-down" /></span>
                    </button>
                  </td>
                  <td>{{ item.policyName }}</td>
                  <td>{{ item.simulationRuns.length }}</td>
                  <td>{{ item.simulationRuns.totalContact }}</td>
                  <td>{{ item.simulationRuns.avgContactsPerAgent }}</td>
                  <td>{{ item.simulationRuns.avgContactDuration }}</td>
                  <td>{{ item.simulationRuns.avgPeoplePerAgent }}</td>
                  <td>{{ item.simulationRuns.totalIndividuals }}</td>
                  <td>{{ item.simulationRuns.totalFloors }}</td>
                  <td>{{ item.simulationRuns.totalTimeStep }}</td>
                  <td>{{ item.simulationRuns.totalScaleMultiplier }}</td>
                </tr>
                  <template v-if="hasSims">
                    <tr v-for="(sim, index) in simRuns[0].simulationRuns" :key="index.simName">
                      <td> </td>
                      <td>Run Simulation</td>
                      <td>{{sim.simName}}</td>
                      <td>{{sim.overall_total_contact_duration}}</td>
                      <td>{{sim.avg_n_contacts_per_agent}}</td>
                      <td>{{sim.avg_contact_duration_per_agent}}</td>
                      <td>{{sim.avg_number_of_people_per_agent}}</td>
                      <td>Simulation Map</td>
                      <td>Data Visualizations</td>
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
      simRuns: [],
      policyList: [],
      statsList: [],
      runList: [],
      policyData: {},
      overviewData: { facilities: [] },
      hasSims: false
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

        // ************** test data below need to be removed later *************//
        this.policyList.push({"sim_id": "sim_1", "policy_id": "pol_id_0002", "facility_name": "TEST"})
        this.policyList.push({"sim_id": "sim_2", "policy_id": "pol_id_0002", "facility_name": "TEST"})

        this.runList.push({"TimestepInSec": 1, "NumberOfFloors": 1, "SimulationName": "sim_1", "SimulationID": "sim_1", "PolicyID": "pol_id_0002", "FacilityName": "TEST", "trajectory_file": "trajectory.txt", "floors": [{"name": "0", "directory": "floor_0/"}], "scaleMultiplier": 2, "sim_id": "sim_1", "floor_dict": {"0": "floor_0/"}})
        this.runList.push({"TimestepInSec": 2, "NumberOfFloors": 4, "SimulationName": "sim_2", "SimulationID": "sim_2", "PolicyID": "pol_id_0002", "FacilityName": "TEST", "trajectory_file": "trajectory.txt", "floors": [{"name": "0", "directory": "floor_0/"}], "scaleMultiplier": 6, "sim_id": "sim_2", "floor_dict": {"0": "floor_0/"}})
        
        var sim1stats = [{"name": "overall_total_contact_duration", "value": 305.930, "unit": "min"}, {"name": "avg_n_contacts_per_agent", "value": 56.3, "unit": ""}, {"name": "avg_contact_duration_per_agent", "value": 30.59, "unit": "min"}, {"name": "avg_number_of_people_per_agent", "value": 9.5, "unit": ""}]
        sim1stats.sim_id = "sim_1"
        this.statsList.push(sim1stats)

        var sim2stats = [{"name": "overall_total_contact_duration", "value": 400.00, "unit": "min"}, {"name": "avg_n_contacts_per_agent", "value": 40, "unit": ""}, {"name": "avg_contact_duration_per_agent", "value": 40, "unit": "min"}, {"name": "avg_number_of_people_per_agent", "value": 11, "unit": ""}]
        sim2stats.sim_id = "sim_2"
        this.statsList.push(sim2stats)
        // ************** test data above need to be removed later *************//

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

    viewRuns(idx, policy) {      
      const index = this.simRuns
        .map(function (e) {
          return e.policyName;
        })
        .indexOf(policy);

      if(index > -1) {
      //this.simRuns.splice(index, 1)
      //this.hasSims = Object.values(this.simRuns[0]).includes(policy)
      this.simRuns = []
      this.hasSims = false  
      }
      else{
        this.simRuns = []
        this.simRuns.push(this.policyData.policies[idx])
        //var hasSim = this.simRuns[0].includes(policy)
         this.hasSims = true      
      }      
    },

    getOverviewData() {
      this.overviewData = { facilities: [] };
      this.policyList.forEach((policy) => {
        if (this.pushUniqueFacilities(policy.facility_name)) {
          this.overviewData.facilities.push({
            facilityName: policy.facility_name, policies: [{policyName: policy.policy_id, simulationRuns: [] } ],
            //facilityName: policy.facility_name, policies: [{ policyName: policy.policy_id, simulationRuns: [policy.sim_id] }],
          });
          this.getOverviewPolicies(policy);
        } else {
          this.getOverviewPolicies(policy);
        }
        //this.overviewData.facilities.push(this.overviewData.facilities);
      });

      // build stats object for each simulation run within each policies for each facility
      this.overviewData.facilities.forEach((facility) => {
        facility.policies.forEach((policy) => {
          policy.simulationRuns.forEach((sim) => {
            this.runList.forEach((run) => {            
              if (run.sim_id === sim.simName) {
                Vue.set(sim,"floors",run.NumberOfFloors);
                Vue.set(sim,"timeStep",run.TimestepInSec);
                Vue.set(sim,"scaleMultiplier",run.scaleMultiplier);

                this.statsList.forEach((stats) => {
                  if (stats.sim_id === sim.simName) {
                    stats.forEach((item) => {
                      Vue.set(sim,item.name,item.value);
                    });
                  }
                });
                policy.simulationRuns.totalFloors += sim.floors
                policy.simulationRuns.totalTimeStep += sim.timeStep
                policy.simulationRuns.totalScaleMultiplier += sim.scaleMultiplier
                policy.simulationRuns.totalContact += sim.overall_total_contact_duration
                policy.simulationRuns.avgContactsPerAgent += sim.avg_n_contacts_per_agent/policy.simulationRuns.length
                policy.simulationRuns.avgContactDuration += sim.avg_contact_duration_per_agent/policy.simulationRuns.length                
                policy.simulationRuns.avgPeoplePerAgent += sim.avg_number_of_people_per_agent/policy.simulationRuns.length
              }
            });            
          })
        })
      })
      this.policyData = { policies: this.overviewData.facilities[0].policies}; // ToDo - push data by facility selected in the dropdown
    },

    getOverviewPolicies(policy) {
      this.overviewData.facilities.forEach((facility) => {     
         if (this.pushUniquePolicies(facility, policy.policy_id)) {
           facility.policies.push({policyName: policy.policy_id, simulationRuns: [] })
         } 
        facility.policies.forEach((pol) => {
          if(policy.policy_id === pol.policyName){
            pol.simulationRuns.push({ simName: policy.sim_id })
            pol.simulationRuns.totalContact = 0
            pol.simulationRuns.avgContactsPerAgent = 0
            pol.simulationRuns.avgContactDuration = 0
            pol.simulationRuns.avgPeoplePerAgent = 0
            pol.simulationRuns.totalIndividuals = 0
            pol.simulationRuns.totalFloors = 0
            pol.simulationRuns.totalTimeStep = 0
            pol.simulationRuns.totalScaleMultiplier = 0
          } 
        })       
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
          return e.policyName;
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

