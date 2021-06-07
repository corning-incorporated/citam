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
  <div id="policyListLayout">
    <ul class="ulStyle">
      <li v-for="(policy, id) in policyData.policies" :key="id">
        <button type="button" class="btn" @click="viewRuns(id)">
          <span><font-awesome-icon icon="chevron-down" /></span>
          <span class="polName"> {{ policy.policyHash }} </span>
          <span class="polRuns"> {{ policy.simulationRuns.length }} Runs </span>
        </button>
        <div id="empty"></div>
        <template v-if="subRows.includes(id)">
          <ul class="subUlStyle">
            <li
              v-for="(sim, index) in simRuns[0].simulationRuns"
              :key="index"
              :value="sim.simName"
            >
              <a
                class="simName"
                :id="index"
                @click="setSimMap(sim.simName, index)"
                href="#"
              >
                Run {{ sim.simName }}
              </a>
            </li>
          </ul>
        </template>
      </li>
    </ul>
  </div>
</template>

<script>
import _ from "lodash"
export default {
    name: "PolicyList",
    props: {
    policyData: Object,  
  },
  watch: {
   policyData(policy) {      
    this.policyData = policy
    this.subRows = []
    this.viewRuns(0)
    this.currSimId = '' 
    }
  },
  data() {
      return {        
        subRows: [],
        simRuns: [],
        polIndex: '',
        simIndex: '' ,
        currSimId: ''
      }
  },
  created() {
      if(this.policyData.selectedPolicy) {
        this.currSimId = this.policyData.selectedSim
        this.subRows.push(this.policyData.policies.findIndex(item=>item.policyHash == this.policyData.selectedPolicy))        
        this.simRuns.push(this.policyData.policies.find(item=>item.policyHash == this.policyData.selectedPolicy))
        this.simIndex = this.simRuns[0].simulationRuns.findIndex(item=>item.simName == this.currSimId)     
      }
      else {
          // show simulation runs for the first policy by default
        this.viewRuns(0)
        this.currSimId = this.simRuns[0].simulationRuns[0].simName
      }          
  },
 mounted() {
    // wait till Simulations component is loaded and update the DOM element
    this.$nextTick (function(){
      if(this.simIndex == '' ) {
          this.simIndex = 0
      } 
      this.setActiveSelectedSimulation(this.simIndex)      
    })
  },

  updated: function() {
      if(_.isEmpty(this.currSimId)) {
          this.setActiveSelectedSimulation(0)
          this.currSimId = this.simRuns[0].simulationRuns[0].simName
      }
      else {
          this.simIndex = this.simRuns[0].simulationRuns.findIndex(item=>item.simName == this.currSimId)
         this.simIndex >=0 ? this.setActiveSelectedSimulation(this.simIndex) : ''
      }  
  },
  methods: {
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
    setSimMap(newSimId, simIndex) {
        this.currSimId = newSimId
        this.$emit('getSimMap', newSimId)
        this.setActiveSelectedSimulation(simIndex)
    },
    
    setActiveSelectedSimulation(Id) {
      var current =  document.getElementsByClassName('setActive')
      if(current.length > 0) {
        current[0].className = current[0].className.replace("setActive", "");
      }      
      var simId = document.getElementById(Id)
      simId.className += " setActive"
    }
  }
}
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap");
#policyListLayout {
  background-color: #f7f9fa;
}

.ulStyle {
  list-style-type: none;
  padding-inline-start: 5px;
}

.ulStyle li {
  padding-bottom: 10px;
}

.subUlStyle {
  list-style-type: none;
  color: #607080;
  font-size: 14px;
}

.subUlStyle li {
  height: 45px;
  border-bottom: 2px solid white;
  padding: 5px;
}

.polName {
  font-family: Inter;
  color: #0080ff;
  font-weight: 600;
  margin: 0 5px 0 5px;
}

.polRuns {
  font-family: Inter;
  color: #607080 !important;
}

.btn span {
  color: #0080ff;
}

.btn:focus {
  box-shadow: none !important;
}

.simName {
  color: #607080;
}

.simName:hover {
  color: #0080ff;
  text-decoration: none;
}

.simName:focus {
  color: #0080ff;
}

.simName.setActive {
  color: #0080ff;
}
/* a.simName {
    color: #0080FF;
} */
</style>
