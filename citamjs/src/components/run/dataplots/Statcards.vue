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
  <div class="row" v-if="cardsData.length > 0">
    <div class="col-xl-3 col-md-6" v-for="(cd, idx) in cardsData" :key="cd.name">
      <div class="card card-shadow text-white mb-4" :class="cd.style" :id="`card-${idx}`">
        <div class="card-body">{{ cd.name }}</div>
        <div class="card-footer">
          <span class="small text-white">
            <span class="card-value">{{ cd.value }}</span> {{ cd.unit }}</span>
          <div class="small text-white"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

const bgStyles = ['primary', 'warning', 'success', 'danger'];

export default {
  name: "Statcards",
  props: {simid: {type: String}},
  data() {
    return {
      cardsData: []
    }
  },
  watch: {
    simid: {
      handler: function () {
        this.getStatCard()
      },
    },
  },
  mounted() {
    this.getStatCard()
  },
  methods: {
    toUpper(w) {
      if (w.length > 0) {
        return `${w[0].toUpperCase()}${w.substring(1)}`
      }
      return "";
    },

    /**
     * Get Statistics for a given simid
     */
    getStatCard() {
      this.cardsData = []
      axios.get(`/${this.simid}/statistics`)
          .then((response) => {
            this.cardsData = response.data.map((statCard, i) => {
              statCard['style'] = `bg-${bgStyles[i]}`
              statCard.name = statCard.name.split("_").map(d => {
                return this.toUpper(d)
              }).join(" ")
              statCard.unit = this.toUpper(statCard.unit)
              return statCard;
            });
          })
          .catch(function (error) {
            console.log(error);
          })
    }
  }
}
</script>

<style scoped>
.card-footer {
  padding: 0 !important;
}

.card-shadow {
  box-shadow: 4px 10px 25px rgba(0, 0, 0, 0.45), 8px 15px 35px rgba(0, 0, 0, 0.04);
}

.card-value {
  font-size: xx-large;
}
</style>
