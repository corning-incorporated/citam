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

import {shallowMount} from "@vue/test-utils";
import Statcards from "@/components/Statcards";
import cards from '../data/cards'

describe('Statcards Tests', () => {
    const wrapper = shallowMount(Statcards, {
        sync: false,
        stubs: {transition: false}
    })

    wrapper.setData({
        cardsData: cards.cardsInput
    })

    test('displays first card with ', () => {
        const firstCard = cards.cardsInput[0];
        expect(wrapper.find('#card-0').text()).toEqual(`${firstCard.name} ${firstCard.value} ${firstCard.unit}`)
    })
    test('displays second card', () => {
        const secondCard = cards.cardsInput[1];
        expect(wrapper.find('#card-1').text()).toEqual(`${secondCard.name} ${secondCard.value}`)
    })
    test('displays third card', () => {
        const thirdCard = cards.cardsInput[2];
        expect(wrapper.find('#card-2').text()).toEqual(`${thirdCard.name} ${thirdCard.value} ${thirdCard.unit}`)
    })
    test('displays fourth card', () => {
        const fourthCard = cards.cardsInput[3];
        expect(wrapper.find('#card-3').text()).toEqual(`${fourthCard.name} ${fourthCard.value}`)
    })

    test('first card style class', () => {
        expect(wrapper.find('#card-0').classes()).toContain(cards.cardsInput[0]['style'])
    })
    test('second card style class', () => {
        expect(wrapper.find('#card-1').classes()).toContain(cards.cardsInput[1]['style'])
    })
    test('third card style class', () => {
        expect(wrapper.find('#card-2').classes()).toContain(cards.cardsInput[2]['style'])
    })
    test('fourth card style class', () => {
        expect(wrapper.find('#card-3').classes()).toContain(cards.cardsInput[3]['style'])
    })

})

