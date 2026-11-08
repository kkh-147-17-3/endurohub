import { mount } from 'svelte';
import '../freeze-clock';
import '../../src/app.css';
import Comparison from '../../src/stories/Comparison.svelte';

declare global {
    interface Window { __DESIGN_PREVIEW_DOCUMENT__?: string; }
}

document.documentElement.lang = 'ko';
document.documentElement.dataset.theme = 'light';
document.body.classList.add('arena');
mount(Comparison, {
    target: document.getElementById('app')!,
    props: { standalone: true, previewDocument: window.__DESIGN_PREVIEW_DOCUMENT__ ?? '' },
});
