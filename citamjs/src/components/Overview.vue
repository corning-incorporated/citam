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
        <div class="row">
          <div class="table-responsive">
            <table class="table table-bordered" v-if="statsList">
              <thead>
                <tr>
                  <th colspan="2">ADD POLICY</th>
                  <th id="metricCols">KEY METRICS</th>
                  <th colspan="4">KEY POLICY INPUTS</th>
                </tr>
                <tr>
                  <th>View runs</th>
                  <th>Policies</th>                  
                  <th v-for="(att, id) in metricAttributes" :key="id">
                    <div class="th-container"> {{ att }}
                      <span class="sort-right"><button class="btn btn-sm btn-link" @click="sortTable(att)">
                        <font-awesome-icon icon="sort" /></button></span>
                    </div>
                  </th>
                  <th v-for="(header, id) in policyInputHeaders" :key="'p'+id">
                    <div class="th-container"> {{ header }}
                      <span class="sort-right"><button class="btn btn-sm btn-link" @click="sortTable(header)">
                        <font-awesome-icon icon="sort" /></button></span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody  v-for="(item, idx) in policyData.policies" :key="idx">             
                <tr>
                  <td>
                    <button type="button" class="btn" @click="viewRuns(idx)">
                      <span><font-awesome-icon icon="chevron-down" /></span>
                    </button>
                  </td>
                  <td><button type="button" class="btn btn-link">{{ item.policyName }}</button> <br/> {{ item.simulationRuns.length }} Runs </td>                  
                  
                  <td>{{ item.simulationRuns.totalContact }}</td>
                  <td>{{ item.simulationRuns.avgContactsPerAgent }}</td>
                  <td>{{ item.simulationRuns.avgContactDuration }}</td>
                  <td>{{ item.simulationRuns.avgPeoplePerAgent }}</td>

                  <td>{{ item.simulationRuns.individuals }}</td>
                  <td>{{ item.simulationRuns.totalFloors }}</td>
                  <td>{{ item.simulationRuns.totalTimeStep }}</td>
                  <td>{{ item.simulationRuns.totalScaleMultiplier }}</td>
                </tr>
                  <template v-if="subRows.includes(idx)">
                    <tr v-for="(sim, index) in simRuns[0].simulationRuns" :key="index">
                      <td> </td>
                      <td> {{sim.simName}}</td> 
                      <td v-for="(stats, ind) in sim.statisctics" :key="sim.simName + ind">
                        {{stats.value}}
                      </td>
                      <td colspan="4"><button type="button" class="btn btn-link simBtn">Simulation Map</button>
                      <button type="button" class="btn btn-link">Data Visualizations</button></td>                      
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
    selectedFacility: String
  },
  data() {
    return {
      metricHeaders: ["Total Contact (minutes)", "Average Contacts/Agent",
        "Average Contact Duration (min/Agent)", "Average Number of People/Agent"],
      metricAttributes: [],
      policyInputHeaders: ["Individuals", "Total Floors","Time Step", "Scale Multiplier"],
      simRuns: [],
      subRows: [],
      policyList: [],
      statsList: [],
      runList: [],
      policyData: {},
      overviewData: { facilities: [] },
      hasSims: false
    };
  },
  watch: {
    selectedFacility(newVal) {
      this.policyData = {policies: this.overviewData.facilities.find(item=>item.facilityName == newVal).policies}
    }
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
          statCard.data.sim_id = response[i].config.url .match(/(?<=\/)(.*)(?=\/)/)[0].toString();
          this.statsList.push(statCard.data);
        });    
       
        this.getOverviewData();
        this.$store.commit("setFacilities", this.overviewData.facilities) // Store it in a centralized variable to use in other components
        this.$emit('setFacilities', this.overviewData.facilities) // To display facility list in the dropdown
        
        if(this.selectedFacility){
          this.policyData = {policies: this.overviewData.facilities.find(item=>item.facilityName == this.selectedFacility).policies}
        } else {
          this.policyData = { policies: this.overviewData.facilities[0].policies}; // Display first facility by default
          } 
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
      this.metricAttributes;
      this.overviewData.facilities = _.sortBy(this.overviewData.facilities, [att,]);
      this.$store.state.facilities
    },

    viewRuns(idx) {      
      const index = this.subRows.indexOf(idx)
      if(index > -1) {
        this.subRows.splice(index, 1)
        this.simRuns =  [] 
      }
      else{
        this.subRows = []
        this.subRows.push(idx)
        this.simRuns = []        
        this.simRuns.push(this.policyData.policies[idx])   
      }      
    },

    getOverviewData() {
      this.overviewData = { facilities: [] };
      this.policyList.forEach((policy) => {
        if (this.pushUniqueFacilities(policy.facility_name)) {
          this.overviewData.facilities.push({
            facilityName: policy.facility_name, policies: [{policyName: policy.policy_id, simulationRuns: [] } ],            
          });          
        } 
        this.overviewData.facilities.forEach((facility) => {     
          if (facility.facilityName === policy.facility_name && this.pushUniquePolicies(facility, policy.policy_id)) {
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
              pol.simulationRuns.individuals = 0
            } 
          })       
        });
      });

      // build stats object for each simulation run within each policies for each facility
      this.overviewData.facilities.forEach((facility) => {
        facility.policies.forEach((policy) => {
          policy.simulationRuns.forEach((sim) => {
            this.runList.forEach((run) => {            
              if (run.sim_id === sim.simName) {
                Vue.set(sim,"floors", run.NumberOfFloors);
                Vue.set(sim,"timeStep", run.TimestepInSec);
                Vue.set(sim,"scaleMultiplier", run.scaleMultiplier);
                Vue.set(sim, "individuals", run.NumberOfEmployees)

                this.statsList.forEach((stats) => {
                  if(this.metricAttributes.length == 0)  {
                    stats.forEach((stat) => 
                    this.metricAttributes.push(stat.name))
                  }                
                  if (stats.sim_id === sim.simName) {
                    stats.forEach((item) => {
                      Vue.set(sim,item.name,item.value);
                    });
                    Vue.set(sim,"statisctics",stats);                
                  }
                });                
                policy.simulationRuns.totalFloors = sim.floors
                policy.simulationRuns.totalTimeStep = sim.timeStep
                policy.simulationRuns.totalScaleMultiplier = sim.scaleMultiplier
                policy.simulationRuns.individuals = sim.individuals

                policy.simulationRuns.totalContact += sim.overall_total_contact_duration
                policy.simulationRuns.avgContactsPerAgent += sim.avg_n_contacts_per_agent/policy.simulationRuns.length
                policy.simulationRuns.avgContactDuration += sim.avg_contact_duration_per_agent/policy.simulationRuns.length                
                policy.simulationRuns.avgPeoplePerAgent += sim.avg_number_of_people_per_agent/policy.simulationRuns.length
              }
            });            
          })
        })
      })
      document.getElementById("metricCols").colSpan= this.metricAttributes.length;

      var stat_list = []
      for(var p of this.overviewData.facilities[0].policies){
        for (var sruns of p.simulationRuns){
          stat_list.push(_.mapValues(_.keyBy(sruns.statisctics, 'name'), 'value'))
        }
        var dynamicKeys = _.keys(stat_list[0])
        var sums = {}
        _.each(stat_list, function (item) {
          _.each(dynamicKeys, function (statKeys) {
            sums[statKeys] = (sums[statKeys] || 0) + item[statKeys];
          });
        });
        console.log("Sums", sums)
      }   
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

.simBtn {
  margin-right: 50px;
}
</style>

