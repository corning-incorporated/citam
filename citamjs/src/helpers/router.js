import Vue from 'vue';
import Router from 'vue-router';

Vue.use(Router);

const router = new Router({
    mode:'history',
    routes: [
        {
            path: '/',
            name: 'home',
            component: () => import('../components/Home.vue'),
            meta: {
              title: 'CITAM',
            },
          },
        // add more routes as we go
        // otherwise redirect to home
        { path: '*', redirect: '/' }
    ]
});

export default router;
