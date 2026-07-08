function getCsrfToken() {
	return window.csrf_token || window.frappe?.csrf_token || window.frappe?.csrfToken || ''
}

function parseBody(response, bodyText) {
	if (!bodyText) return {}

	try {
		return JSON.parse(bodyText)
	} catch {
		return { message: bodyText }
	}
}

function parseServerMessages(value) {
	if (!value) return []
	try {
		const messages = typeof value === 'string' ? JSON.parse(value) : value
		return (Array.isArray(messages) ? messages : [messages]).map((entry) => {
			try {
				return typeof entry === 'string' ? JSON.parse(entry) : entry
			} catch {
				return { message: String(entry) }
			}
		})
	} catch {
		return []
	}
}

function requestError(body, response) {
	const serverMessages = parseServerMessages(body?._server_messages)
	const serverMessage = [...serverMessages].reverse().find((entry) => entry?.message)
	const message = serverMessage?.message || body?.message || body?.exception || body?.exc_type || response.statusText || 'Request failed'
	const error = new Error(message)
	error.title = serverMessage?.title || body?.exc_type || 'Request failed'
	error.status = response.status
	error.details = body
	return error
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
			...(options.body && getCsrfToken() ? { 'X-Frappe-CSRF-Token': getCsrfToken() } : {}),
		},
		body: options.body ? JSON.stringify(options.body) : undefined,
	})

	const bodyText = await response.text()
	const body = parseBody(response, bodyText)

	if (!response.ok) {
		throw requestError(body, response)
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

export async function getLinkFieldValue(doctype, name, fieldname) {
	const response = await callMethod('lenscloud.api.launch.get_link_field_value', { doctype, name, fieldname })
	return response.message || response.data || response
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

export async function submitDoc(doc) {
	const response = await callMethod('frappe.client.submit', { doc }, 'POST')
	return response.message || response.data || response
}

export async function cancelDoc(doctype, name) {
	const response = await callMethod('frappe.client.cancel', { doctype, name }, 'POST')
	return response.message || response.data || response
}

export async function deleteDoc(doctype, name) {
	const response = await callMethod('frappe.client.delete', { doctype, name }, 'POST')
	return response.message || response.data || response
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
		return value.title || value.app || value.name || JSON.stringify(value)
	}

	return String(value)
}

export function titleFromDoctype(doctype) {
	return doctype
		.replace(/_/g, ' ')
		.replace(/\b\w/g, (match) => match.toUpperCase())
}
