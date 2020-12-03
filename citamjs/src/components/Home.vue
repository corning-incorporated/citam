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
    <ul class="nav nav-tabs" id="my-tab" role="tablist">
      <li class="nav-item facility">
        <a class="nav-link active" id="summary-tab" data-toggle="tab" href="" role="tab"
           aria-controls="home" aria-selected="true" @click="toVizToggle($event)">Facility Name A 
           <span><font-awesome-icon icon="chevron-down"/></span></a>           
      </li>
      <li class="nav-item">
        <a class="nav-link" id="viz-tab" data-toggle="tab" role="tab" href=""
           aria-controls="profile" aria-selected="false" @click="toVizToggle($event)">Overview</a>
      </li>
        <li class="nav-item">
        <a class="nav-link" id="viz-tab" data-toggle="tab" role="tab" href=""
           aria-controls="profile" aria-selected="false" @click="toVizToggle($event)">Simulations</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" id="viz-tab" data-toggle="tab" role="tab" href=""
           aria-controls="profile" aria-selected="false" @click="toVizToggle($event)">Policies</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" id="viz-tab" data-toggle="tab" role="tab" href=""
           aria-controls="profile" aria-selected="false" @click="toVizToggle($event)">Floor Plans</a>
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
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap');
#mainLayout {
margin: 0 30px 0 30px;
}
.navbar {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.navbar-light {
  background-color: #f0f0f0;
}

.nav-tabs .nav-item {
width: 140px;
height: 50px;
border-right: 1px solid black !important;
background-color: #EBEFF2;
}
.nav-tabs .nav-item.facility {
width:250px;
text-align: left;
height: 50px;
background-color: #32404D;
}

.nav-tabs .nav-item.facility a{
font-family: Inter;
font-style: normal;
font-weight: 600;
font-size: 16px;
color: #FFFFFF;
background-color: #32404D;
}

.nav-tabs .nav-link { 
  color: #607080;
  font-family: Inter;
  font-style: normal;
  font-weight: 600;
  font-size: 16px;
  border: none;
}
.nav-tabs .nav-link.active {
  color: #0080FF;
  background-color: #fff;
  font-family: Inter;
  font-style: normal;
  font-weight: 600;
  font-size: 16px;
  height: 50px;
}

.nav-tabs .nav-link:hover {
  border: none;
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
