import {createApp} from 'vue';
import RoughnessParametersCard from './RoughnessParametersCard.vue';

export function createCardApp(el, props) {
    let app = createApp(RoughnessParametersCard, props);
    app.mount(el);
    return app;
}
