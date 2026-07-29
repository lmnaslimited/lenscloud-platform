import { io } from 'socket.io-client'

export function getSocketUrl() {
	const siteName = window.site_name
	const socketioPort = Number(window.socketio_port)

	if (!siteName || siteName === 'undefined') {
		throw new Error('Cannot initialize realtime: site_name is missing')
	}
	if (!Number.isInteger(socketioPort) || socketioPort <= 0) {
		throw new Error('Cannot initialize realtime: invalid socketio_port')
	}

	const origin = window.location.port
		? `${window.location.protocol}//${window.location.hostname}:${socketioPort}`
		: window.location.origin

	return `${origin}/${siteName}`
}

export function initSocket() {
	const url = getSocketUrl()
	const socket = io(url, {
		withCredentials: true,
		reconnection: true,
	})

	socket.on('connect', () => {
		console.info('[realtime] connected', { namespace: socket.nsp })
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
