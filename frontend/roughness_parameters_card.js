import {createApp} from 'vue';
import RoughnessParametersCard from './RoughnessParametersCard.vue';

export function createCardApp(el, csrfToken, props) {
    let app = createApp(RoughnessParametersCard, props);
    app.provide('csrfToken', csrfToken);
    app.mount(el);
    return app;
}
