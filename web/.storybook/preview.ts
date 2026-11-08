import type { Preview } from '@storybook/sveltekit';
import './freeze-clock';
import '../src/app.css';

const preview: Preview = {
    parameters: {
        layout: 'fullscreen',
        controls: { expanded: true },
        options: { storySort: { order: ['디자인 비교'] } },
    },
    globalTypes: {
        theme: {
            description: '색상 테마',
            toolbar: { title: '테마', items: ['light', 'dark'], dynamicTitle: true },
        },
    },
    initialGlobals: { theme: 'light' },
    decorators: [
        (Story, context) => {
            document.documentElement.lang = 'ko';
            document.documentElement.dataset.theme = context.globals.theme === 'dark' ? 'dark' : 'light';
            document.body.classList.add('arena');
            return Story();
        },
    ],
};

export default preview;
