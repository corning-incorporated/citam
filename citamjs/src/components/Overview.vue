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
            <div id="title"><span>Policy Results</span>Select metric (header) to determine the best policy</div>
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
                                <div class="col-sm-2">                                
                                    <th>View runs</th>
                                    <th v-for="att in policyHeaders" :key="att">
                                        <div class="th-container">{{ att }}
                                            <span class="sort-right"><button class="btn btn-sm btn-link" @click="sortTable(att)">
                                            <font-awesome-icon icon="sort"/></button></span>
                                        </div>
                                    </th>  
                                </div>  
                                <div class="col-sm-5">                                                            
                                    <th v-for="att in metricsHeaders" :key="att">
                                        <div class="th-container">{{ att }}
                                            <span class="sort-right"><button class="btn btn-sm btn-link" @click="sortTable(att)">
                                            <font-awesome-icon icon="sort"/></button></span>
                                        </div>
                                    </th> 
                                </div>
                                <div class="col-sm-5">                               
                                    <th v-for="att in inputsHeaders" :key="att">
                                        <div class="th-container">{{ att }}
                                            <span class="sort-right"><button class="btn btn-sm btn-link" @click="sortTable(att)">
                                            <font-awesome-icon icon="sort"/></button></span>
                                        </div>
                                    </th>
                                </div>
                            </tr>
                        </thead>
                      <tbody>
                        <!-- <tr v-for="policy in policyList" :key="policy.sim_id" :id="policy.sim_id">
                            <td>
                                <button type="button" class="btn" @click="viewRuns(policy.policy_id)">
                                <span><font-awesome-icon icon="chevron-down"/></span></button>
                            </td>
                            <td v-for="att in policyHeaders" :key="policy.sim_id+att" :id="policy.sim_id+att">
                            {{ policy[att] }}
                            </td>
                            <td v-for="att in metricsHeaders" :key="policy.policy_id+att" :id="policy.policy_id+att">
                            {{ policy[att] }}
                            </td>
                            <td v-for="att in inputsHeaders" :key="policy.policy_id+att" :id="policy.policy_id+att">
                            {{ policy[att] }}
                            </td>
                        </tr> -->
                        <tr v-for="(item, idx) in policyList" :key="idx.sim_id">
                            <td>
                                <button type="button" class="btn" @click="viewRuns(policy.policy_id)">
                                <span><font-awesome-icon icon="chevron-down"/></span></button>
                            </td>
                            <td>{{ item.policy_id }}</td>                                   
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
import Vue from 'vue';
import axios from 'axios';
import _ from "lodash";

export default {
    name: "Overview",
    data (){
        return{
            policyHeaders: ["Policies", "Number of Policy Simulation Runs"],
            metricsHeaders: ["Total Contact (minutes)", "Average Contacts/Agent", "Average Contact Duration (min/Agent)", "Average Number of People/Agent"],
            inputsHeaders: ["Individuals", "Shifts", "Entrances", "One-way Aisles"],
            policyList : [],
            statsList: [],
            runList: [],
            overviewData: [],
        }
    },
      created() {
    axios.get('/list') //get list of policies, simulations, facilities
        .then((response) => {
          this.policyList = response.data.map(list => list);
          return axios.all(response.data.map(x => axios.get(`/${x.sim_id}`)))
        })
        .then((runResponse) => {
          // eslint-disable-next-line no-unused-vars
          this.runList = runResponse.map(run => run.data)
          return axios.all(runResponse.map(x => axios.get(`/${x.data.SimulationID}/statistics`)))
        })
        .then((response) => {        
            response.map((statCard, i) => {              
              statCard.data.sim_id = response[i].config.url.match(/(?<=\/)(.*)(?=\/)/)[0].toString()
              this.statsList.push(statCard.data)            
            });
            this.getOverviewData();
          } )
          .catch(function (error) {
            console.log(error);
        })
    },
    methods: {
        sortTable(att) {
        this.policyList = _.sortBy(this.policyList, [att]);
        this.runList = _.sortBy(this.runList, [att]);
        this.statsList = _.sortBy(this.statsList, [att]); 
        this.overviewData = _.sortBy(this.overviewData, [att]);              
        },

        viewRuns(){
            alert("Viewing Runs")
        },

        getOverviewData(){
            this.policyList.forEach((policy) => {               
                var isUniqueFacility = this.pushUniqueItems(policy.facility_name, "facility")
                if(isUniqueFacility){
                    //this.overviewData.push({facilityName:policy.facility_name})
                    var isUniquePolicy = this.pushUniqueItems(policy.policy_id, "policy")
                        if(isUniquePolicy){
                            this.overviewData.push({policyName:policy.policy_id, facilityName:policy.facility_name})
                            //this.overviewData = Vue.set(policy, 'policyName', policy.policy_id)
                            //Vue.set(this.overviewData, 'policy', {policyName:policy.policy_id, facilityName:policy.facility_name})
                        }
                }
                //if(this.overviewData.length > 0){
                    //this.overviewData[x].push({simulationName: policy.sim_id})
                    this.overviewData.forEach((data) =>  {
                        //data.push({...{simulationName: policy.sim_id}})
                        Vue.set(data, 'simulationName', policy.sim_id)
                        //this.overviewData.push(Object.assign({}, x,{simulationName: policy.sim_id}))
                    })
                    //Vue.set(this.overviewData, 'simulationName', policy.sim_id)
                    //Vue.set(this.overviewData, x, {simulationName :policy.sim_id})
                //}
            });
        },

        pushUniqueItems(item, type){
             var index = this.overviewData.map(function(e){
                return type =="policy"? e.policyName : e.facilityName;
            }).indexOf(item)
            return (index === -1) ? true: false;
        }
    }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap');
#overviewLayout {
background-color: #ffff;
}
#title {
font-family: Inter;
text-align: left;
padding: 10px;
color:#607080;
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
    background-color: #EBEFF2;    
}
.subTitle div {
   color: #607080; 
   font-family: Inter;
   text-align: left;
   padding: 10px 0 10px 15px;
   border-right: 1px solid #DAE0E6 !important;
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

.table .col-sm-2, .table .col-sm-5 {
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

