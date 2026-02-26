const DAY_NAMES = ['일', '월', '화', '수', '목', '금', '토'];

function parse(date: string): Date {
    return new Date(date + 'T00:00:00');
}

/** "2025년 03월 15일" */
export function formatDateFull(date: string): string {
    const d = parse(date);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}년 ${m}월 ${day}일`;
}

/** "토" */
export function formatDateDay(date: string): string {
    return DAY_NAMES[parse(date).getDay()];
}

/** "2025.03.15" */
export function formatDate(date: string): string {
    const d = parse(date);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}.${m}.${day}`;
}

/** "03.15" */
export function formatDateShort(date: string): string {
    const d = parse(date);
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${m}.${day}`;
}

/** "03/15" */
export function formatDateSlash(date: string): string {
    const d = parse(date);
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${m}/${day}`;
}
