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
  <div id="app">
<<<<<<< HEAD
<!--<dashboard v-if="showDash"></dashboard>-->
    <home></home>
    </div>
=======
<!--          <dashboard v-if="showDash"></dashboard>-->
    <the-navigation></the-navigation>
    <main>
      <router-view>
      <home v-show="showDash"></home>
      </router-view>
    </main>
  </div>
>>>>>>> CITAM-118-New-Layout
</template>

<script>
// import Dashboard from "@/components/Dashboard";
import TheNavigation from '@/components/nav/Navigation'
import Home from '@/components/Home';
import {library} from '@fortawesome/fontawesome-svg-core'
import {faChartBar, faChartArea, faTable, faArrowAltCircleLeft,
  faSort, faMap, faQuestionCircle} from '@fortawesome/free-solid-svg-icons'
import {faGithub} from '@fortawesome/free-brands-svg-icons'

library.add(faGithub, faChartBar, faChartArea, faTable,
    faArrowAltCircleLeft, faSort, faMap, faQuestionCircle)

import axios from 'axios'

axios.defaults.baseURL = '/v1';

export default {
  name: 'App',
  components: {
    Home,
    TheNavigation
    // Dashboard
  },
  data(){return {
    showDash: true,
    
    }}
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
</style>
