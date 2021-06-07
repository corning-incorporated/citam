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
  <div>
    <nav class="topnav navbar navbar-expand sticky-top navbar-dark justify-content-between">
      <div class="navbar-brand title"><router-link to="/"> CITAM </router-link> 
      Indoor Agent-based Modeling</div>
      <form class="form-inline">
        <div class="mr-sm-2 navbar-text text">
          <a :href="docLink" target="_blank">Documentation</a></div> 
        <div class="mr-sm-2 navbar-text text">
          <a :href="aboutLink" target="_blank">About</a></div>
        <div class="mr-sm-2 navbar-text text">
          <a :href="aboutLink" target="_blank">Tutorials</a></div>  
       <div class="mr-sm-2 navbar-text"><a :href="gitHubLink" target="_blank">
           <font-awesome-icon :icon="['fab','github']" size="lg"/></a></div>       
      </form>
    </nav>
  </div>
</template>

<script>
export default {
  name: "Navigation",
  data(){return{
  aboutLink:'https://github.com/corning-incorporated/citam/blob/alpha/README.md',
  gitHubLink:'https://github.com/corning-incorporated/citam',
  docLink:'https://github.com/corning-incorporated/citam/blob/alpha/docs/index.rst'
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
font-weight: 600;
font-size: 14px;
line-height: 15px;
display: flex;
align-items: center;
color: #DAE0E6 !important;
margin-left: 115px;
}
.navbar-brand a{
position: absolute;
left: 2.41%;
right: 92.55%;
top: 16.67%;
bottom: 22.92%;
font-family: Barlow;
font-style: normal;
font-weight: bold;
font-size: 24px;
line-height: 29px;
display: flex;
align-items: center;
color: #0080FF;
} 
.navbar-brand a.router-link-active{
  text-decoration: none;
}
.navbar-dark {
  height: 48px;
  box-shadow: 0px 1px 4px rgba(0, 0, 0, 0.1), 0px 1px 2px -1px rgba(0, 0, 0, 0.16);
  margin-bottom: 10px;
}
.form-inline > .navbar-text{
  margin-right: 25px !important;
}
.mr-sm-2.navbar-text.text a {
    color: #0080FF;
    font-family: Barlow;
    font-style: normal;
    font-weight: 600;
    font-size: 16px;
    display: flex;
    align-items: center;
}
</style>
