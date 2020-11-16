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
  <div id="mainLayout">
    <nav class="topnav navbar navbar-expand sticky-top navbar-light justify-content-between">
      <div class="navbar-brand title"><span> CITAM </span> (COVID-19 Indoor Transmission Agent-based Modeling) is 
      an open source project initiated by Corning, Inc.</div>
      <form class="form-inline">
        <div class="mr-sm-2 navbar-text abt-text">
          <a :href="aboutLink" target="_blank">ABOUT</a></div>
        <div class="mr-sm-2 navbar-text"><a :href="gitHubLink" target="_blank">
           <font-awesome-icon :icon="['fab','github']" size="lg"/></a></div>
        <div class="mr-sm-2 navbar-text">
          <a :href="helpLink" target="_blank">
            <font-awesome-icon icon="question-circle" size="lg"/></a></div>
            <div class="mr-sm-2 navbar-text">
              <img src="../assets/CorningLogo_White.png" width="82" height="12" alt=""></div>        
      </form>
    </nav>

    <ul class="nav nav-tabs" id="my-tab" role="tablist">
      <li class="nav-item">
        <a class="nav-link active" id="summary-tab" data-toggle="tab" href="" role="tab"
           aria-controls="home" aria-selected="true" @click="toVizToggle($event)">Facility A</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" id="viz-tab" data-toggle="tab" role="tab" href=""
           aria-controls="profile" aria-selected="false" @click="toVizToggle($event)">Facility B</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" id="viz-tab" data-toggle="tab" role="tab" href=""
           aria-controls="profile" aria-selected="false" @click="toVizToggle($event)">Facility C</a>
      </li>

    </ul>
    <footer class="footer">
      <div class="container">
        <h5>Floor Plans</h5>
        <div class="flex-container">
          <div @click="floorPlan()">Floor plan 1</div>
          <div>Floor plan 2</div>
          <div>Floor plan 3</div>
          <div>Floor plan 4</div>
          <div>Floor plan 5</div>
          <div>Add floor plan</div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: "Home",
  methods:{
    floorPlan(){
      alert("You are viewing a floor")
    }
  },
  data(){return{
  aboutLink:'https://github.com/corning-incorporated/citam/blob/alpha/README.md',
  gitHubLink:'https://github.com/corning-incorporated/citam',
  helpLink:'https://github.com/corning-incorporated/citam/blob/alpha/docs/index.rst'
  }}
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css?family=Barlow');
.navbar {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.navbar-brand.title{
font-family: Barlow;
font-style: normal;
font-weight: 500;
font-size: 14px;
align-items: center;
color: #607080 !important;
margin-left: 115px;
}

.navbar-brand span{
position: absolute;
left: 2.41%;
right: 92.55%;
top: 16.67%;
bottom: 22.92%;
font-family: Barlow;
font-style: normal;
font-weight: 1000;
font-size: 24px;
line-height: 29px;
display: flex;
align-items: center;
color: #FC2474;
} 

.navbar-light {
  background-color: #F7F9FA;
  height: 48px;
  box-shadow: 0px 1px 4px rgba(0, 0, 0, 0.1), 0px 1px 2px -1px rgba(0, 0, 0, 0.16);
}

.form-inline > .navbar-text{
  margin-right: 25px !important;
}

.form-inline > .navbar-text.abt-text{
font-family: Barlow;
font-style: normal;
font-weight: 600;
font-size: 12px;
color: #607080;
}

.footer {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 160px;
  line-height: 60px;
  background-color: #f0f0f0;
}

.flex-container {
  display: flex;
}

.flex-container > div {
  background-color: #c4c2c2;
  margin: 10px;
  padding: 20px;
  font-size: 20px;
  cursor: pointer;
}
</style>
