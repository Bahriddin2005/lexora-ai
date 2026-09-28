import { NextResponse, type NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

function cookieValue(setCookies: string[], name: string): string | undefined {
  const raw = setCookies.find((c) => c.startsWith(`${name}=`));
  return raw?.slice(name.length + 1).split(";")[0];
}

/**
 * Silent session refresh: the access cookie lives 15 minutes, the refresh cookie 30 days.
 * When only the refresh cookie is left, rotate the tokens before the page renders so
 * server components see a logged-in user.
 */
export async function proxy(request: NextRequest) {
  const refresh = request.cookies.get("lx_refresh")?.value;
  if (request.cookies.has("lx_access") || !refresh) return NextResponse.next();

  let res: Response;
  try {
    res = await fetch(`${BACKEND_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { cookie: `lx_refresh=${refresh}` },
      cache: "no-store",
    });
  } catch {
    return NextResponse.next();
  }
  if (!res.ok) {
    const response = NextResponse.next();
    response.cookies.delete("lx_refresh");
    return response;
  }
  const setCookies = res.headers.getSetCookie();
  const access = cookieValue(setCookies, "lx_access");
  const rotated = cookieValue(setCookies, "lx_refresh");
  if (access) request.cookies.set("lx_access", access);
  if (rotated) request.cookies.set("lx_refresh", rotated);
  const response = NextResponse.next({ request: { headers: request.headers } });
  for (const cookie of setCookies) response.headers.append("set-cookie", cookie);
  return response;
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)"],
};
