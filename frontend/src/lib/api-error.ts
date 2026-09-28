export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: Record<string, unknown> = {},
  ) {
    super(message);
  }
}

export async function toApiError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    const err = body?.error ?? {};
    return new ApiError(res.status, err.code ?? "error", err.message ?? res.statusText, err.details ?? {});
  } catch {
    return new ApiError(res.status, "error", res.statusText);
  }
}
