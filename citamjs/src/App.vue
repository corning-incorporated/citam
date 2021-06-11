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

<template style="background-color: black">
  <div id="app">
    <the-navigation></the-navigation>
    <main id="mainLayout">
      <router-view>
        <home v-show="showDash"></home>
      </router-view>
      <footer class="py-4 bg-light mt-auto">
        <div class="container-fluid">
          <div class="d-flex align-items-center justify-content-between small">
            <div class="text-muted">&copy; Corning Incorporated</div>
            <div>
              <a
                href="https://github.com/corning-incorporated/citam/blob/main/LICENSE"
                target="_blank"
                >License</a
              >
            </div>
          </div>
        </div>
      </footer>
    </main>
  </div>
</template>

<script>
//import Dashboard from "@/components/Dashboard";
import TheNavigation from "@/components/nav/Navigation";
import Home from "@/components/Home";
import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faChartBar,
  faChartArea,
  faTable,
  faArrowAltCircleLeft,
  faSort,
  faMap,
  faQuestionCircle,
  faChevronDown,
  faChevronRight,
} from "@fortawesome/free-solid-svg-icons";
import { faGithub } from "@fortawesome/free-brands-svg-icons";

library.add(
  faGithub,
  faChartBar,
  faChartArea,
  faTable,
  faArrowAltCircleLeft,
  faSort,
  faMap,
  faQuestionCircle,
  faChevronDown,
  faChevronRight
);

import axios from "axios";

axios.defaults.baseURL = "/v1";

export default {
  name: "App",
  components: {
    Home,
    TheNavigation,
    //Dashboard
  },
  data() {
    return {
      showDash: true,
    };
  },
};
</script>

<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap");
body {
  background-color: black !important;
}
#app {
  font-family: Inter;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  background-color: black;
}
#mainLayout {
  margin: 0 30px 0 30px;
}

#mainLayout footer {
  position: fixed;
  left: 0;
  bottom: 0;
  width: 100%;
}
</style>
