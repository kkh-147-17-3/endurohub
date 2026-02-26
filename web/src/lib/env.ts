import { env } from '$env/dynamic/private';
import { env as publicEnv } from '$env/dynamic/public';

/** Internal API URL for SSR server-side calls (e.g. http://api:8000) */
export const API_URL_INTERNAL = env.API_URL_INTERNAL || 'http://localhost:8000';

/** Public API URL for client-side calls (e.g. /api, proxied by nginx) */
export const PUBLIC_API_URL = publicEnv.PUBLIC_API_URL || '/api';

/** Kakao Maps JavaScript key */
export const KAKAO_JAVASCRIPT_KEY = publicEnv.PUBLIC_KAKAO_JAVASCRIPT_KEY || '';

/** Naver Maps client ID */
export const NAVER_MAP_CLIENT_ID = publicEnv.PUBLIC_NAVER_MAP_CLIENT_ID || '';

/** Google Analytics ID */
export const GOOGLE_ANALYTICS_ID = publicEnv.PUBLIC_GOOGLE_ANALYTICS_ID || '';

/** Google Feedback Form URL */
export const FEEDBACK_FORM_URL = publicEnv.PUBLIC_FEEDBACK_FORM_URL || '';

/** App URL for canonical URLs and OG tags */
export const APP_URL = publicEnv.PUBLIC_APP_URL || 'https://www.endurohub.kr';

/** App name */
export const APP_NAME = publicEnv.PUBLIC_APP_NAME || 'EnduroHub';

/** Admin secret token for admin UI features (compared against admin_token cookie) */
export const ADMIN_SECRET = env.ADMIN_SECRET || '';
