// Copyright 2021. Corning Incorporated. All rights reserved.
//
// This software may only be used in accordance with the licenses granted by
// Corning Incorporated. All other uses as well as any copying, modification or
// reverse engineering of the software is strictly prohibited.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
// CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
// ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
// WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
// ==============================================================================


import Vue from "vue";
import Vuex from "vuex";
import { getBaseMap, getTrajectory, getSummary } from "@/script/data_service";

Vue.use(Vuex);

export default new Vuex.Store({
    state: {
        facilities: null,
        policyList: null,
        statsList: null,
        floorOptions: null,
        currentSimID: null,
        trajectoryData: null,
        totalSteps: null,
        nAgents: null,
        mapData: null,
        scaleMultiplier: null,
        status: null, // fetchingData | error | ready | null
        errorMessage: null,
        fetchingStartTime: null,
        currentStep: null,
        currentFloor: null
    },
    getters: {},
    mutations: {
        setFacilities(state, payload) {
            state.facilities = payload
        },
        setPolicyList(state, policyList) {
            state.policyList = policyList;
        },
        setStatsList(state, stats) {
            state.statsList = stats;
        },
        setFloorOptions(state, floorOptions) {
            state.floorOptions = floorOptions;
        },
        setTrajectoryData(state, trajectoryData) {
            state.trajectoryData = trajectoryData;
        },
        setNumberOfAgents(state, nAgents) {
            state.nAgents = nAgents;
        },
        setTotalSteps(state, totalSteps) {
            state.totalSteps = totalSteps;
        },
        setMapData(state, mapData) {
            state.mapData = mapData;
        },
        setScaleMultiplier(state, scaleMultiplier) {
            state.scaleMultiplier = scaleMultiplier;
        },
        setSimulationID(state, simId) {
            state.currentSimID = simId;
        },
        setCurrentFloor(state, floor) {
            state.currentFloor = floor;
        },
        setCurrentStep(state, step) {
            state.currentStep = step;
        },
        setFetchingStartTime(state, startTime) {
            state.fetchingStartTime = startTime;
        },
        updateStatus(state, { status, msg }) {
            state.status = status;
            state.errorMessage = msg;
        },
        removeTrajectoryData(state) {
            state.trajectoryData = null;
            state.totalSteps = null;
            state.currentSimID = null;
            state.nAgents = null;
            state.mapData = null;
            state.status = 'ready';
            state.currentFloor = null;
        }
    },
    actions: {
        async fetchSimulationData({ dispatch, commit, state }) {
            commit("updateStatus", { status: "fetchingData", msg: null });
            commit("setFetchingStartTime", new Date().getTime() / 1000);
            return new Promise(() => {
                try {
                    getSummary(state.currentSimID).then(async (response) => {
                        let floorOptions = response.data.Floors.map((x) => x.name);
                        commit("setFloorOptions", floorOptions);
                        commit("setNumberOfAgents", response.data.NumberOfAgents);
                        commit("setTotalSteps", response.data.TotalTimesteps);
                        commit("setScaleMultiplier", response.data.ScaleMultiplier);

                        getBaseMap(state.currentSimID, state.currentFloor).then((resp) => {
                            commit("setMapData", resp.data);
                        });
                        if (response.data.NumberOfAgents > 0 || response.data.TotalTimesteps >= 0) {
                            await dispatch("getTrajectoryData");
                        } else {
                            commit('updateStatus', { status: 'error', msg: 'Number of agents or total steps is zero.' });
                        }

                    });

                } catch (e) {
                    commit('updateStatus', { status: 'error', msg: 'Unable to fetch data.' });
                }
            });

        },
        async getTrajectoryData({ commit, state }) {
            let trajectories = [];
            let max_chunk_size = Math.ceil(1e8 / state.nAgents);
            let request_arr = [], first_timestep = 0, max_contacts = 0;

            while (first_timestep < state.totalSteps) {
                request_arr.push(
                    getTrajectory(
                        state.currentSimID,
                        state.currentFloor,
                        first_timestep,
                        max_chunk_size)
                );
                first_timestep += max_chunk_size;
            }
            await Promise.all(request_arr).then((response) => {
                if (response !== undefined) {
                    response.forEach((chunk) => {
                        trajectories = trajectories.concat(chunk.data.data);
                        max_contacts = Math.max(max_contacts, chunk.data.max_count);
                    });
                    commit("setTrajectoryData", trajectories);
                    commit("updateStatus", { status: "ready", msg: null });
                }
            });
            commit("setTotalSteps", trajectories.length);
        },
    }
});
