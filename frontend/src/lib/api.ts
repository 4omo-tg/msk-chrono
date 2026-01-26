import { API_BASE } from './config';

/**
 * Wrapper для fetch запросов с обработкой истечения токена.
 * При 401/403 ошибках автоматически удаляет токен и редиректит на страницу регистрации.
 */
export async function apiFetch(
    url: string,
    options: RequestInit = {}
): Promise<Response> {
    const token = localStorage.getItem('token');
    
    const headers: HeadersInit = {
        ...options.headers,
    };
    
    if (token) {
        (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers,
    });
    
    // Если токен истек или невалиден - редирект на регистрацию
    if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        window.location.hash = '#/register';
        throw new Error('Session expired');
    }
    
    return response;
}

/**
 * GET запрос с авторизацией
 */
export async function apiGet(url: string): Promise<Response> {
    return apiFetch(url, { method: 'GET' });
}

/**
 * POST запрос с авторизацией и JSON body
 */
export async function apiPost(url: string, data?: any): Promise<Response> {
    return apiFetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: data ? JSON.stringify(data) : undefined,
    });
}

/**
 * DELETE запрос с авторизацией
 */
export async function apiDelete(url: string): Promise<Response> {
    return apiFetch(url, { method: 'DELETE' });
}

/**
 * Проверяет, авторизован ли пользователь (есть ли токен)
 */
export function isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
}

/**
 * Выход из системы
 */
export function logout(): void {
    localStorage.removeItem('token');
    window.location.hash = '#/register';
}
