export function watchDocument(socket, { doctype, name, onUpdate }) {
	if (!socket) {
		throw new Error('A Socket.IO connection is required')
	}

	if (!doctype || !name) {
		throw new Error('doctype and document name are required')
	}

	const subscribe = () => {
		console.info('[realtime] subscribing', { doctype, name })
		socket.emit('doc_subscribe', doctype, name)
	}

	const handleUpdate = (message) => {
		if (message?.doctype !== doctype || message?.name !== name) {
			return
		}

		console.info('[realtime] document updated', message)
		onUpdate(message)
	}

	socket.on('connect', subscribe)
	socket.on('doc_update', handleUpdate)

	if (socket.connected) {
		subscribe()
	}

	return () => {
		socket.off('connect', subscribe)
		socket.off('doc_update', handleUpdate)

		if (socket.connected) {
			socket.emit('doc_unsubscribe', doctype, name)
		}
	}
}