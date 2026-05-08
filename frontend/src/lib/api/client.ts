import { ApiError, NetworkError } from './errors'

export interface ApiRequestOptions {
  method?: string
  headers?: Record<string, string>
  body?: unknown
  signal?: AbortSignal
}

export async function apiFetch<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { method = 'GET', headers = {}, body, signal } = options

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  const requestHeaders: Record<string, string> = {
    ...headers,
  }

  if (token && !requestHeaders.Authorization) {
    requestHeaders.Authorization = `Bearer ${token}`
  }

  if (body !== undefined && !(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json'
  }

  try {
    const response = await fetch(`/api/v1${path}`, {
      method,
      headers: requestHeaders,
      body: body instanceof FormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
      signal,
      credentials: 'include',
    })

    if (!response.ok) {
      if (response.status === 401 && path !== '/auth/login') {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token')
          localStorage.removeItem('bidder_id')
          localStorage.removeItem('user_id')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
      }

      let detail: string | undefined
      let errorDetails: unknown
      try {
        const errorBody = await response.json()
        errorDetails = errorBody
        detail = formatApiErrorDetail(errorBody)
      } catch {
        detail = response.statusText
      }
      throw new ApiError(response.status, detail || 'Request failed', errorDetails)
    }

    // Handle blob/file responses
    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      return response.json() as Promise<T>
    }

    // For non-JSON responses, return the whole response
    return response as unknown as T
  } catch (err) {
    if (err instanceof ApiError) throw err
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw err
    }
    throw new NetworkError(err)
  }
}

function formatApiErrorDetail(errorBody: unknown): string {
  if (typeof errorBody === 'string') return errorBody
  if (!errorBody || typeof errorBody !== 'object') return 'Request failed'

  const detail = (errorBody as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    const messages = detail
      .map((entry) => {
        if (!entry || typeof entry !== 'object') return null
        const maybeMsg = (entry as { msg?: unknown }).msg
        if (typeof maybeMsg === 'string') return maybeMsg
        return null
      })
      .filter((msg): msg is string => Boolean(msg))

    if (messages.length > 0) {
      return messages.join('; ')
    }
  }

  if (detail && typeof detail === 'object') {
    const maybeMessage = (detail as { message?: unknown }).message
    if (typeof maybeMessage === 'string') return maybeMessage
    const maybeError = (detail as { error?: unknown }).error
    if (typeof maybeError === 'string') return maybeError
  }

  const maybeMessage = (errorBody as { message?: unknown }).message
  if (typeof maybeMessage === 'string') return maybeMessage

  return 'Request failed'
}

export function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  if (!params) return path
  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      searchParams.set(key, String(value))
    }
  }
  const qs = searchParams.toString()
  return qs ? `${path}?${qs}` : path
}
