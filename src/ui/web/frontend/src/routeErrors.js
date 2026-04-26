export const ROUTE_LOAD_TIMEOUT_MS = 20000

function normalizePath(target) {
  if (typeof target === 'string' && target) return target
  if (typeof target?.fullPath === 'string' && target.fullPath) return target.fullPath
  return '/'
}

function isResponseLike(value) {
  return Boolean(value && typeof value.status === 'number' && typeof value.ok === 'boolean')
}

export function routeNotFoundLocation(target) {
  return {
    name: 'not-found',
    query: { path: normalizePath(target) },
  }
}

export function routeFailureLocation(target, failure) {
  const path = normalizePath(target)

  if (isResponseLike(failure)) {
    if (failure.status === 404) return routeNotFoundLocation(path)

    return {
      name: 'error',
      query: {
        path,
        kind: failure.status >= 500 ? 'server' : 'http',
        status: String(failure.status),
      },
    }
  }

  return {
    name: 'error',
    query: {
      path,
      kind: failure?.name === 'TimeoutError' ? 'timeout' : 'network',
    },
  }
}

export function replaceForRouteFailure(router, target, failure) {
  return router.replace(routeFailureLocation(target, failure))
}

export function replaceForRouteNotFound(router, target) {
  return router.replace(routeNotFoundLocation(target))
}