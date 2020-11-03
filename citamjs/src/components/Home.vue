<template>
  <div id="mainLayout">
    <nav class="topnav navbar navbar-expand sticky-top navbar-light justify-content-between">
      <span class="navbar-brand">CITAM</span>
      <form class="form-inline">
        <span class="mr-sm-2 navbar-text">
          <a href="https://github.com/corning-incorporated/citam/blob/alpha/README.md" target="_blank">About</a></span>
        <span class="mr-sm-2 navbar-text"><a href="https://github.com/corning-incorporated/citam" target="_blank">
          GitHub <font-awesome-icon icon="github-square"/></a></span>
        <span class="mr-sm-2 navbar-text">
          <a href="https://github.com/corning-incorporated/citam/blob/alpha/docs/index.rst" target="_blank">
          Help <font-awesome-icon icon="question-circle"/></a></span>
        <span class="mr-sm-2 navbar-text">CORNING</span>
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
  }
}
</script>

<style scoped>
.navbar {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.navbar-light {
  background-color: #f0f0f0;
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
