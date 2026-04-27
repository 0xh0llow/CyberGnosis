import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

function getApiBase() {
  return process.env.CENTRAL_SERVER_URL?.trim() || 'http://central_server:8000';
}

function getApiToken() {
  return process.env.API_TOKEN ?? '';
}

async function forward(request: NextRequest, params: { path: string[] }) {
  const upstreamPath = params.path.join('/');
  const search = request.nextUrl.search || '';
  const apiBase = getApiBase();
  const apiToken = getApiToken();
  const target = `${apiBase}/api/${upstreamPath}${search}`;

  const headers = new Headers(request.headers);
  headers.set('Authorization', `Bearer ${apiToken}`);
  if (!headers.has('Content-Type') && request.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }
  headers.delete('host');

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: 'no-store',
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = await request.text();
  }

  let response: Response;
  try {
    response = await fetch(target, init);
  } catch (error) {
    console.error(`Failed to proxy ${target}`, error);
    return NextResponse.json(
      { error: 'Upstream central_server unreachable', target },
      { status: 502 },
    );
  }
  const contentType = response.headers.get('content-type') ?? 'application/json';
  const body = await response.text();

  return new NextResponse(body, {
    status: response.status,
    headers: {
      'content-type': contentType,
    },
  });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return forward(request, await context.params);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return forward(request, await context.params);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return forward(request, await context.params);
}
