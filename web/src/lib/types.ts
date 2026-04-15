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
	imageSrcThumb: string | null;
	giveaways: string[] | null;
	courseImageSrcs: string[];
	giveawayImageSrcs: string[];

	viewCount: number;
	daysUntilRace: number;
	daysUntilRegistrationEnd: number | null;
	isRegistrationOpen: boolean;

	recapUrl: string | null;
	aiSummary: string | null;
	url: string;

	createdAt: string;
	updatedAt: string;
}

// === Auth ===

export interface AuthUser {
	id: number;
	email: string;
	nickname: string;
	profileImage: string;
	emailVerified: boolean;
	emailUpdatesOptIn: boolean;
	preferredSports: string[] | null;
	preferredRegions: string[] | null;
	onboardingCompleted: boolean;
	needsNickname: boolean;
	needsEmailVerification: boolean;
	needsOnboarding: boolean;
}

export interface OAuthLoginResponse {
	authorizeUrl: string;
	state?: string;
}

export interface OAuthCallbackResponse {
	token: string;
	user: AuthUser;
}

export interface OAuthPendingResponse {
	pendingToken: string;
}

export interface NicknameSetupResponse {
	success: boolean;
	user: AuthUser;
}

export interface EmailSendResponse {
	success: boolean;
	message: string;
}

export interface EmailVerifyResponse {
	success: boolean;
	message: string;
	user: AuthUser;
}

export interface PendingEmailVerifyResponse {
	token: string;
	user: AuthUser;
}

export interface MeResponse {
	user: AuthUser | null;
}

export interface ProfileUpdateResponse {
	success: boolean;
	message: string;
	user: AuthUser;
}

export interface OnboardingResponse {
	success: boolean;
	message: string;
	user: AuthUser;
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
	contentText: string;
	category?: string | null;
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
	isOwner?: boolean;
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
	isOwner?: boolean;
}

// === Review ===

export interface Review {
	id: number;
	nickname: string;
	rating: number;
	comment: string;
	completionTime?: string | null;
	courseDifficulty?: string | null;
	operationSatisfaction?: number | null;
	recommendationTags?: string[] | null;
	createdAt: string;
	createdAtFormatted: string;
}

export interface ReviewStats {
	count: number;
	average: number;
	averageOperationSatisfaction?: number;
	difficultyDistribution?: Record<string, number>;
}

// === API Response Types ===

export interface HomeResponse {
	closingSoon: Race[];
	upcomingRaces: Race[];
	recentlyAdded: Race[];
	recentPosts: Post[];
	sportCounts: Record<string, number>;
	totalUpcoming: number;
	recommendations?: RecommendationsResponse;
}

export interface RecommendationsResponse {
	type: 'personalized' | 'popular';
	races: Race[];
	reason: { topSports: string[]; topRegions: string[] } | null;
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
	category: string | null;
	sort: string;
	sidebar: {
		popularPosts: Post[];
		upcomingRaces: Array<{
			id: number;
			title: string;
			sport: Sport;
			sportLabel: string;
			raceDate: string;
		}>;
	};
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
