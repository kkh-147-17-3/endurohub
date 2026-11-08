import { reviews } from '../../src/stories/fixtures';

const likedPaths = new Map<string, boolean>();

/** Local deterministic responses for reversible preview interactions. */
export async function clientApiFetch<T>(path: string, _options?: unknown): Promise<T> {
    const reviewId = Number(path.match(/reviews\/(\d+)/)?.[1]);
    const initialCount = reviews.find((review) => review.id === reviewId)?.likeCount ?? 0;
    const liked = !likedPaths.get(path);
    likedPaths.set(path, liked);
    return { success: true, liked, likeCount: initialCount + (liked ? 1 : 0) } as T;
}

export function isApiError(response: unknown): response is { errors: Record<string, string[]> } {
    return !!response && typeof response === 'object' && 'errors' in response;
}
