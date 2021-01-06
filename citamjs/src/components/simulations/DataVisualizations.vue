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
  <div id="vizLayout">
      <div class="container-fluid">
        <div class="row header">
          <div class="col-sm-2">
            <policy-list :policyData="policyData" v-model="policyData"></policy-list>  
          </div>
          <div class="col-sm-10">
            <button type="button" class="btn btn-link">Data Viz2</button>
          </div>          
        </div>
      </div>
  </div>
</template>

<script>
import PolicyList from './PolicyList.vue'

export default {
  name: "DataVisualization",
  components: {PolicyList},
  props: {
    selectedFacility: String
  },
  watch: {
   selectedFacility(newFacility) {  
    this.policyData = {policies: this.$store.state.facilities.find(item=>item.facilityName == newFacility).policies}
    this.subRows = []
    console.log(this.policyData)
    }
  },
  data() {
    return {
      policyData: {},
      subRows: [],
      simRuns: []
    }
  },
  created (){
    this.policyData = {policies: this.$store.state.facilities.find(item=>item.facilityName == this.selectedFacility).policies}
    console.log(this.policyData)
  },
}
</script>

<style scoped>
#vizLayout {
  text-align: left !important;
}
</style>
