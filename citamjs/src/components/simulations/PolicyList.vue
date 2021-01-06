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
                    <span class="polName"> {{policy.policyName}} </span> <span class="polRuns"> {{ policy.simulationRuns.length }} Runs </span>
                </button>  
                <template v-if="subRows.includes(id)">
                    <ul class="subUlStyle">
                        <li v-for="(sim, index) in simRuns[0].simulationRuns" :key="index">
                            <a class="simName" href="#"> Run {{sim.simName}} </a>
                        </li>
                    </ul>
                </template>    
            </li>
        </ul>   
    </div>   
</template>

<script>

export default {
    name: "PolicyList",
    props: {
    policyData: Object,    
  },
  watch: {
   policyData(policy) {      
    this.policyData = policy
    this.subRows = []
    console.log(this.policyData)
    }
  },
  data() {
      return {        
        subRows: [],
        simRuns: []
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
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap');
.policy {
    text-align: left;
    background-color: #F7F9FA;;
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
    color: #0080FF;
    font-weight: 600;
    margin: 0 5px 0 5px;
}

.polRuns {
    font-family: Inter;
    color: #607080 !important;
}

.btn span {
    color: #0080FF;
}

.btn:focus {
    box-shadow: none !important;
}

.simName {
    color: #607080;
}

.simName:hover {
    color: #0080FF;
    text-decoration: none;
}

.simName:focus {
    color: #0080FF;
}
</style>
