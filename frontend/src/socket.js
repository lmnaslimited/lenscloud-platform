import { io } from 'socket.io-client'

export function initSocket() {
	const siteName = window.site_name
	const socketioPort = Number(window.socketio_port || 9000)

	if (!siteName || siteName === 'undefined') {
		throw new Error('Cannot initialize realtime: window.site_name is missing')
	}

	if (!Number.isInteger(socketioPort) || socketioPort <= 0) {
		throw new Error('Cannot initialize realtime: invalid socketio_port')
	}

	const socketOrigin = import.meta.env.DEV
		? `${window.location.protocol}//${window.location.hostname}:${socketioPort}`
		: window.location.origin

	const socket = io(`${socketOrigin}/${siteName}`, {
		withCredentials: true,
		reconnectionAttempts: 5,
	})

	socket.on('connect', () => {
		console.info('[realtime] connected', {
			socketId: socket.id,
			siteName,
			socketOrigin,
		})
	})

	socket.on('connect_error', (error) => {
		console.error('[realtime] connection failed', {
			message: error.message,
			siteName,
			socketOrigin,
		})
	})

	socket.on('disconnect', (reason) => {
		console.warn('[realtime] disconnected', reason)
	})

	return socket
}