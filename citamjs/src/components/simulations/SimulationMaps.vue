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
   <div id="simMapLayout">                                                 
      <!-- <button type="button" class=" btn btn-link">Floor 2</button>
      <button type="button" class=" btn btn-link">Floor 3</button>
      <button type="button" class=" btn btn-link">Floor 4</button>       -->
      <div class="title"> SIMULATION</div>            
        <plot-visualization :simId="currSimId"></plot-visualization>        
    </div>                                                  
</template>

<script>
//import PolicyList from './PolicyList.vue'
import PlotVisualization from '@/components/run/PlotVisualization.vue'

export default {
  name: 'SimulationMaps',
  components: { PlotVisualization },
  props: {
    selectedFacility: String,
    simId: String
  },
  watch: {
    simId(newSimId) {
      this.currSimId = newSimId
    }
  },
  data() {
      return {
          policyData: {},          
          simRuns: [],
          currSimId: '',
      }
  },
  created (){
      //this.policyData = {policies: this.$store.state.facilities.find(item=>item.facilityName == this.selectedFacility).policies}
      //this.currSimId = this.policyData.policies[0].simulationRuns[0].simName;
      this.currSimId = this.simId
  },
  methods:{
    getSimMap(simId) {
      this.currSimId = simId
    }   
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap');
#simMapLayout {
    text-align: left !important;
    background-color: white;
    padding-top: 0px;
}

.title {
    color: #607080;
    font-family: Inter;
    align-items: center; 
    background-color:#EBEFF2;
    height: 45px;
    padding: 10px;
}
</style>
