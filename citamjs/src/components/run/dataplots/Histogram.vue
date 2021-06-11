<!--
 Copyright 2021. Corning Incorporated. All rights reserved.

 This software may only be used in accordance with the identified license(s).

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
 ==========================================================================
-->

<template>
    <div :id="divId"></div>
</template>

<script>
import Plotly from 'plotly.js-dist'

export default {
  name: "Scatterplot",

  props: {
    pairData: {type: Array, required: true},
    options:{type: Object, default(){return {chartTitle: 'Histogram', chartCol: 'blue'}}}
  },
  data() {
    return {
      histogramChartData: this.pairData,
      divId: `contactHistogramPlot${this.options.chartTitle.replace(/ /g, "_")}`,
    };
  },

  watch: {
    pairData: {
      handler: function (histogramData) {
        this.histogramChartData = histogramData;
        this.setHistogram()
      },
    },
  },

  mounted() {
    this.setHistogram()
  },

  methods: {

    /**
     * Load histogram with data
     */

    setHistogram() {
      let data = [{
            x: this.histogramChartData,
            type: "histogram",
            name: this.options.chartTitle,
            marker: {
              color: this.options.chartCol,
            },
          }],
          layout = {
            barmode: 'stack',
            title: this.options.chartTitle,
            xaxis: {
              title: 'Value Range'
            },
            yaxis: {
              title: '# of Value'
            },
          };
      if(document.getElementById(this.divId)){
        Plotly.react(this.divId, data, layout);
      }

    },
  }
}
</script>

<style scoped>

</style>
