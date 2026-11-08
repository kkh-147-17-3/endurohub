import type { Meta, StoryObj } from '@storybook/sveltekit';
import Comparison from './Comparison.svelte';

const meta = {
	id: 'design-comparison',
	title: '디자인 비교/나란히 비교',
	component: Comparison,
	parameters: { layout: 'fullscreen' },
	args: { scenario: 'date-groups', viewport: 'mobile', theme: 'light', standalone: false },
	argTypes: {
		scenario: { control: false },
		viewport: { control: false },
		theme: { control: false },
		standalone: { table: { disable: true } },
		previewDocument: { table: { disable: true } }
	}
} satisfies Meta<typeof Comparison>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Overview: Story = { name: '모바일에서 비교', args: { scenario: 'date-groups' } };
export const Desktop: Story = { name: '데스크톱에서 비교', args: { viewport: 'desktop' } };
export const DateGroups: Story = { name: '일자별 그룹 목록 비교', args: { scenario: 'date-groups' } };
export const Primitives: Story = { name: '태그와 접수 상태 비교', args: { scenario: 'primitives' } };
export const HomeRecords: Story = { name: '후기와 회원 기록 비교', args: { scenario: 'home' } };
export const SingleSport: Story = { name: '단일 종목 비교', args: { scenario: 'calendar-single' } };
export const OpenRegistration: Story = { name: '단일 접수 상태 비교', args: { scenario: 'calendar-open' } };
