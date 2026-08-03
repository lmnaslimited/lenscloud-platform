import { io } from 'socket.io-client'

export function getSocketUrl() {
	const siteName = window.site_name

    if (!siteName || siteName === 'undefined') {
        throw new Error('Cannot initialize realtime: site_name is missing')
    }

    return `/${siteName}`
}

export function initSocket() {
	const url = getSocketUrl()
	const socket = io(url, {
        path: "/socket.io",
        withCredentials: true,
        reconnection: true,
    })

	socket.on('connect', () => {
		console.info('[realtime] connected', { namespace: socket })
	})
	socket.on('connect_error', (error) => {
		console.error('[realtime] connection failed', {
			message: error.message,
			namespace: socket.nsp,
		})
	})
	socket.on('disconnect', (reason) => {
		console.warn('[realtime] disconnected', { reason, namespace: socket.nsp })
	})

	return socket
}