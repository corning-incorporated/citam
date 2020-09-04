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
    <div :id="contactScatterPlot"></div>
</template>

<script>
import Plotly from 'plotly.js-dist'
import _ from 'lodash';

export default {
  name: "Scatterplot",

  props: {pairData: {type: Array}},
  data() {
    return {
      scatterChartData: this.pairData,
      contactScatterPlot: "contactScatterPlot"
    };
  },

  watch: {
    pairData: {
      handler: function (scatterData) {
        this.scatterChartData = scatterData;
        this.setChart()
      },
    },
  },
  mounted() {
      this.setChart();
  },
  methods: {

    /**
     * Load Scatter plot
     */

    setChart() {
      let data = [{
            x: _.map(this.scatterChartData, 'x'),
            y: _.map(this.scatterChartData, 'y'),
            mode: 'markers',
            type: 'scatter',
            name: 'Agents',
            text: _.map(this.scatterChartData, 'a'),
            marker: {size: 12, color: '#cb0f0f'}
          }],
          layout = {
            xaxis: {
              title: 'Total Contacts Per Agent'
            },
            yaxis: {
              title: 'Average Contact Duration per Agent (mins)'
            },
            title: 'Per Agent Total Contact and Average Contact Duration'
          };
      if(document.getElementById(this.contactScatterPlot)){
        Plotly.react(this.contactScatterPlot, data, layout);
      }

    },
  }
}
</script>

<style scoped>

</style>
