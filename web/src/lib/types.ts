// === Pagination ===

export interface PaginationMeta {
	currentPage: number;
	lastPage: number;
	perPage: number;
	total: number;
	from: number;
	to: number;
}

export interface PaginationLinks {
	first: string | null;
	last: string | null;
	prev: string | null;
	next: string | null;
}

export interface PaginatedResponse<T> {
	data: T[];
	meta: PaginationMeta;
	links: PaginationLinks;
}

// === Race ===

export type Sport = 'running' | 'swimming' | 'cycling' | 'triathlon' | 'trail_running';
export type RaceStatus = 'upcoming' | 'registration_open' | 'registration_closed' | 'finished';

export interface EntryFee {
	distance: string;
	fee: string;
}

export interface Race {
	id: number;
	slug: string;
	title: string;
	sport: Sport;
	sportLabel: string;

	raceDate: string | null;
	raceEndDate: string | null;
	startTime: string | null;

	location: string | null;
	address: string | null;
	latitude: number | null;
	longitude: number | null;
	region: string | null;

	distances: string[] | null;

	registrationStart: string | null;
	registrationEnd: string | null;
	entryFee: EntryFee[] | null;

	officialUrl: string | null;
	source: string | null;
	sourceUrl: string | null;

	status: RaceStatus;
	statusLabel: string;

	description: string | null;
	organizer: string | null;
	organizerContact: string | null;
	organizerEmail: string | null;

	imageSrc: string | null;
	giveaways: string[] | null;
	courseImageSrcs: string[];
	giveawayImageSrcs: string[];

	viewCount: number;
	daysUntilRace: number;
	daysUntilRegistrationEnd: number | null;
	isRegistrationOpen: boolean;

	recapUrl: string | null;
	url: string;

	createdAt: string;
	updatedAt: string;
}

// === Post ===

export interface TaggedRace {
	id: number;
	slug: string;
	title: string;
	sport: Sport;
	sportLabel: string;
}

export interface Post {
	id: number;
	nickname: string;
	title: string;
	content: string;
	images: string[] | null;
	imageSrcs: string[];
	viewCount: number;
	commentCount: number;
	likeCount: number;
	createdAt: string;
	createdAtFormatted: string;
	updatedAt: string;
	taggedRaces?: TaggedRace[];
	comments?: PostComment[];
}

// === PostComment ===

export interface PostComment {
	id: number;
	postId: number;
	parentId: number | null;
	nickname: string;
	content: string;
	isReply: boolean;
	createdAt: string;
	createdAtFormatted: string;
	replies?: PostComment[];
}

// === Review ===

export interface Review {
	id: number;
	nickname: string;
	rating: number;
	comment: string;
	createdAt: string;
	createdAtFormatted: string;
}

export interface ReviewStats {
	count: number;
	average: number;
}

// === API Response Types ===

export interface HomeResponse {
	closingSoon: Race[];
	upcomingRaces: Race[];
	recentlyAdded: Race[];
	recentPosts: Post[];
	sportCounts: Record<Sport, number>;
	totalUpcoming: number;
}

export interface RaceListResponse extends PaginatedResponse<Race> {
	filters: {
		regions: string[];
		sports: SportOption[];
		distanceCategories: Record<string, DistanceCategory[]>;
	};
	applied: {
		sport: string[];
		region: string[];
		status: string[];
		name: string | null;
		distanceCategory: string[];
		monthFrom: string;
		monthTo: string | null;
	};
}

export interface RaceDetailResponse {
	race: Race;
	relatedRaces: Race[];
	relatedPosts: Post[];
	reviews: Review[];
	reviewStats: ReviewStats;
	hasReviewed: boolean;
}

export interface RaceYearlyResponse {
	races: Record<string, Race[]>;
	year: number;
	totalCount: number;
}

export interface CalendarResponse {
	year: number;
	month: number;
	startOfMonth: string;
	racesGrouped: Record<string, Race[]>;
	previousMonth: { year: number; month: number };
	nextMonth: { year: number; month: number };
	sport: string | null;
	sports: SportOption[];
}

export interface PostDetailResponse {
	post: Post;
	hasLiked: boolean;
}

export interface PostListResponse extends PaginatedResponse<Post> {
	search: string | null;
}

export interface PostRacesResponse {
	races: Array<{
		id: number;
		title: string;
		sport: Sport;
		sportLabel: string;
		raceDate: string;
	}>;
}

export interface SitemapResponse {
	races: Array<{ slug: string; updatedAt: string }>;
	posts: Array<{ id: number; updatedAt: string }>;
	calendarMonths: Array<{ year: number; month: number }>;
}

// === Filter Types ===

export interface SportOption {
	value: Sport;
	label: string;
}

export interface DistanceCategory {
	value: string;
	label: string;
	type: 'range' | 'range_m' | 'keyword' | 'non_numeric';
	min?: number;
	max?: number;
	keyword?: string;
}

// === Action Response Types ===

export interface ApiErrors {
	errors: Record<string, string[]>;
}

export interface ReviewCreateResponse {
	success: boolean;
	message: string;
	review: Review;
}

export interface PostCreateResponse {
	success: boolean;
	message: string;
	post: Post;
	redirect: string;
}

export interface PostUpdateResponse {
	success: boolean;
	message: string;
	post: Post;
	redirect: string;
}

export interface PostDeleteResponse {
	success: boolean;
	message: string;
	redirect: string;
}

export interface VerifyPasswordResponse {
	success: boolean;
	post: Post;
	races: Array<{
		id: number;
		title: string;
		sport: Sport;
		sportLabel: string;
		raceDate: string;
	}>;
	editToken: string;
}

export interface CommentCreateResponse {
	success: boolean;
	message: string;
	comment: PostComment;
}

export interface CommentUpdateResponse {
	success: boolean;
	message: string;
	comment: PostComment;
}

export interface CommentDeleteResponse {
	success: boolean;
	message: string;
}

export interface LikeToggleResponse {
	success: boolean;
	liked: boolean;
	likeCount: number;
}
