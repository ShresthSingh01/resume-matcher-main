import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const token = request.cookies.get('session_token')?.value;
    const path = request.nextUrl.pathname;

    // 1. If user is trying to access the Dashboard (root) without a token
    if (path === '/' && !token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    // 2. If user is trying to access Login page WITH a token, redirect to Dashboard
    //    (Prevents showing login screen to logged-in users)
    if (path === '/login' && token) {
        return NextResponse.redirect(new URL('/', request.url));
    }

    // 3. Inject ngrok skip warning header for all requests (proxied to backend)
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set('ngrok-skip-browser-warning', 'true');

    // Default: Continue with modified headers
    return NextResponse.next({
        request: {
            headers: requestHeaders,
        },
    });
}

// Configure which paths the middleware runs on
export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         * - static (public directory)
         */
        '/((?!_next/static|_next/image|favicon.ico|VirexLogo.jpg).*)',
    ],
};
