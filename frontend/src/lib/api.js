function parseBody(response, bodyText) {
	if (!bodyText) {
		return {}
	}

	try {
		return JSON.parse(bodyText)
	} catch {
		return {
			message: bodyText,
		}
	}
}

async function request(path, options = {}) {
	const url = new URL(path, window.location.origin)

	if (options.params) {
		for (const [key, value] of Object.entries(options.params)) {
			if (value === undefined || value === null || value === '') {
				continue
			}

			url.searchParams.set(key, typeof value === 'string' ? value : JSON.stringify(value))
		}
	}

	const response = await fetch(url, {
		method: options.method || 'GET',
		credentials: 'include',
		headers: {
			Accept: 'application/json',
			...(options.body ? { 'Content-Type': 'application/json' } : {}),
		},
		body: options.body ? JSON.stringify(options.body) : undefined,
	})

	const bodyText = await response.text()
	const body = parseBody(response, bodyText)

	if (!response.ok) {
		throw new Error(body?.message || body?.exc || response.statusText || 'Request failed')
	}

	return body
}

export async function callMethod(method, params = {}, httpMethod = 'GET') {
	return request(`/api/method/${method}`, {
		method: httpMethod,
		params: httpMethod === 'GET' ? params : undefined,
		body: httpMethod === 'GET' ? undefined : params,
	})
}

export async function getLoggedUser() {
	const response = await callMethod('frappe.auth.get_logged_user')
	return response.message || response.data || response
}

export async function getUserRoles(uid) {
	const response = await callMethod('frappe.core.doctype.user.user.get_roles', { uid })
	const roles = response.message || response.data || response
	return Array.isArray(roles) ? roles : []
}

export async function listDocs(doctype, options = {}) {
	const params = {
		fields: JSON.stringify(options.fields || ['name']),
		limit_start: options.offset ?? 0,
		limit_page_length: options.limit ?? 20,
		order_by: options.orderBy || 'modified desc',
	}

	if (options.filters) {
		params.filters = JSON.stringify(options.filters)
	}

	const response = await request(`/api/resource/${encodeURIComponent(doctype)}`, {
		params,
	})

	return response.data || []
}

export async function getDoc(doctype, name) {
	const response = await request(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`)
	return response.data || response.message || response
}

export async function saveDoc(doctype, name, payload) {
	const response = await request(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`, {
		method: 'PUT',
		body: payload,
	})

	return response.data || response.message || response
}

export async function createDoc(doctype, payload) {
	const response = await request(`/api/resource/${encodeURIComponent(doctype)}`, {
		method: 'POST',
		body: payload,
	})

	return response.data || response.message || response
}

export function isGuestUser(user) {
	return !user || user === 'Guest'
}

export function formatFieldValue(value) {
	if (value === null || value === undefined || value === '') {
		return '—'
	}

	if (typeof value === 'boolean') {
		return value ? 'Yes' : 'No'
	}

	if (Array.isArray(value)) {
		return value.length ? value.map((item) => formatFieldValue(item)).join(', ') : '—'
	}

	if (typeof value === 'object') {
		return value.title || value.name || JSON.stringify(value)
	}

	return String(value)
}

export function titleFromDoctype(doctype) {
	return doctype
		.replace(/_/g, ' ')
		.replace(/\b\w/g, (match) => match.toUpperCase())
}
