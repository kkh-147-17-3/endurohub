import type { Meta, StoryObj } from '@storybook/sveltekit';
import VersionPreview from './VersionPreview.svelte';
import { scenarios, type ComparisonVersion, type Scenario } from './scenarios';

const meta = {
	id: 'design-preview',
	title: '디자인 비교/개별 보기',
	component: VersionPreview,
	parameters: { layout: 'fullscreen' },
	argTypes: {
		version: { control: false },
		scenario: { control: false }
	}
} satisfies Meta<typeof VersionPreview>;

export default meta;
type Story = StoryObj<typeof meta>;

function versionStory(scenario: Scenario, version: ComparisonVersion): Story {
	return {
		name: `${scenarios[scenario].label} 변경 ${version === 'before' ? '전' : '후'}`,
		args: { scenario, version },
		parameters: {
			sveltekit_experimental: {
				state: { page: { url: new URL(`https://storybook.invalid/calendar${scenarios[scenario].query}`), data: {}, params: {} } }
			}
		}
	};
}

export const PrimitivesBefore: Story = { ...versionStory('primitives', 'before'), name: '종목 태그와 접수 상태 변경 전' };
export const PrimitivesAfter: Story = { ...versionStory('primitives', 'after'), name: '종목 태그와 접수 상태 변경 후' };
export const CardsBefore: Story = { ...versionStory('cards', 'before'), name: '대회 카드 변경 전' };
export const CardsAfter: Story = { ...versionStory('cards', 'after'), name: '대회 카드 변경 후' };
export const RaceResultsBefore: Story = { ...versionStory('single-sport', 'before'), name: '러닝 대회 목록 변경 전' };
export const RaceResultsAfter: Story = { ...versionStory('single-sport', 'after'), name: '러닝 대회 목록 변경 후' };
export const HomeBefore: Story = { ...versionStory('home', 'before'), name: '홈 후기와 회원 기록 변경 전' };
export const HomeAfter: Story = { ...versionStory('home', 'after'), name: '홈 후기와 회원 기록 변경 후' };
export const DateGroupsBefore: Story = { ...versionStory('date-groups', 'before'), name: '일자별 그룹 목록 변경 전' };
export const DateGroupsAfter: Story = { ...versionStory('date-groups', 'after'), name: '일자별 그룹 목록 변경 후' };
export const CalendarHeightBefore: Story = { ...versionStory('calendar-height', 'before'), name: '달력 높이 개선 직전' };
export const CalendarHeightAfter: Story = { ...versionStory('calendar-height', 'after'), name: '달력 높이 개선 후' };
export const CalendarBefore: Story = { ...versionStory('calendar', 'before'), name: '여러 종목의 달력 변경 전' };
export const CalendarAfter: Story = { ...versionStory('calendar', 'after'), name: '여러 종목의 달력 변경 후' };
export const CalendarSingleBefore: Story = { ...versionStory('calendar-single', 'before'), name: '러닝 필터 달력 변경 전' };
export const CalendarSingleAfter: Story = { ...versionStory('calendar-single', 'after'), name: '러닝 필터 달력 변경 후' };
export const CalendarOpenBefore: Story = { ...versionStory('calendar-open', 'before'), name: '접수 중 필터 목록 변경 전' };
export const CalendarOpenAfter: Story = { ...versionStory('calendar-open', 'after'), name: '접수 중 필터 목록 변경 후' };
export const MapBefore: Story = { ...versionStory('map', 'before'), name: '지역별 대회 지도 변경 전' };
export const MapAfter: Story = { ...versionStory('map', 'after'), name: '지역별 대회 지도 변경 후' };
