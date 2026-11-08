import { mount } from 'svelte';
import '../freeze-clock';
import '../../src/app.css';
import VersionPreview from '../../src/stories/VersionPreview.svelte';
import { page } from '../mocks/app-state.svelte';
import { scenarios, type Scenario, type ComparisonVersion } from '../../src/stories/scenarios';

declare global {
    interface Window {
        __DESIGN_COMPARISON__?: { scenario?: Scenario; version?: ComparisonVersion; theme?: 'light' | 'dark' };
    }
}

const input = window.__DESIGN_COMPARISON__ ?? {};
const scenario: Scenario = input.scenario && input.scenario in scenarios ? input.scenario : 'calendar';
const version: ComparisonVersion = input.version === 'before' ? 'before' : 'after';
page.url = new URL(`/calendar${scenarios[scenario].query}`, 'https://storybook.invalid');
document.documentElement.lang = 'ko';
document.documentElement.dataset.theme = input.theme === 'dark' ? 'dark' : 'light';
document.body.classList.add('arena');
mount(VersionPreview, { target: document.getElementById('app')!, props: { scenario, version } });
