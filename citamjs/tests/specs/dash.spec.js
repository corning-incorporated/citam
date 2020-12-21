/**
 Copyright 2020. Corning Incorporated. All rights reserved.

 This software may only be used in accordance with the identified license(s).

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
 ==========================================================================
**/

import {mount, createLocalVue} from "@vue/test-utils";
import Dashboard from "@/components/Dashboard";
import Scatterplot from "@/components/Scatterplot";
import Histogram from "@/components/Histogram"
import {FontAwesomeIcon} from '@fortawesome/vue-fontawesome'
import dashData from '../data/dashboard'

const localVue = createLocalVue()
localVue.component('font-awesome-icon', FontAwesomeIcon)


describe('Dashboard Tests', () => {
    const wrapper = mount(Dashboard, {
        localVue,
        sync: false,
        stubs: {transition: false}
    })

    wrapper.setData({
        runList: dashData.runList,
        runAttributes: dashData.attList,
        chartData: dashData.chartData,
        totalContactsPerAgentHistogram: dashData.totalContactsPerAgentHistogram,
        avgContactDurationPerAgentHistogram: dashData.avgContactDurationPerAgentHistogram,
        totalContactsHistogramOption: dashData.totalContactsHistogramOption,
        avgContactDurationHistogramOption: dashData.avgContactDurationHistogramOption,
    })

    test('displays title', () => {
        const dashTitle = wrapper.find('.navbar-brand')
        expect(dashTitle.text()).toContain('Dashboard')
    })

    test('all columns found', () => {

        const columns = wrapper.findAll('#data-table > thead > tr > th:not(:first-child)');
        const colsOnPage = columns.wrappers.map(th => {
            return th.text()
        })
        expect(colsOnPage.sort()).toEqual(dashData.attList.sort())
    })

    test('all columns data found', () => {
        let columns, colsOnPage, result;
        const simIds = dashData.runList.map(x => {
            return x.sim_id
        });
        simIds.map(simId => {
            columns = wrapper.findAll(`#data-table > tbody > tr#${simId} > td:not(:first-child)`);
            colsOnPage = columns.wrappers.map(td => {
                return td.text()
            })
            result = dashData.runList.filter(row => {
                return row.sim_id === simId
            });
            expect(colsOnPage.sort()).toEqual(Object.values(result[0]).sort())

        })
    })

    test('Summary tab heading', async ()=>{
        await wrapper.setData({showDetails: 1})
        expect(wrapper.find('a#summary-tab').text()).toBe('Summary')
    })

    test('Scatterplot Mounted', () => {
        expect(wrapper.findComponent(Scatterplot).exists()).toBe(true)
    })
    test('Scatterplot exists', () => {
        expect(wrapper.find('div#contactScatterPlot').exists()).toBe(true);
    })

    test('Histogram Mounted', () => {
        expect(wrapper.findComponent(Histogram).exists()).toBe(true)
    })
    test('Histogram for total data exists', () => {
        const id = `contactHistogramPlot${dashData.totalContactsHistogramOption.chartTitle.replace(
            / /g, "_")}`
        expect(wrapper.find(`div#${id}`).exists()).toBe(true);
    })
    test('Histogram for average data exists', () => {
        const id = `contactHistogramPlot${dashData.avgContactDurationHistogramOption.chartTitle.replace(
            / /g, "_")}`
        expect(wrapper.find(`#${id}`).exists()).toBe(true);
    })

    test('Visualization tab heading',()=>{
        expect(wrapper.find('a#viz-tab').text()).toBe('Visualization')
    })
})

