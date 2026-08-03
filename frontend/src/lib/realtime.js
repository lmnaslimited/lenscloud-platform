
export function watchDocument(socket, { doctype, name, onUpdate }) {
	if (!socket) throw new Error('A Socket.IO connection is required')
	if (!doctype || !name) throw new Error('doctype and document name are required')
	if (typeof onUpdate !== 'function') throw new Error('onUpdate must be a function')

	let active = true
	const subscribe = () => {
		if (!active) return
		socket.emit('doc_subscribe', doctype, name)
		console.info('[realtime] subscribed', { doctype, name })
	}
	const handleUpdate = (message) => {
		if (!active || message?.doctype !== doctype || message?.name !== name) return
		onUpdate(message)
	}

	socket.on('connect', subscribe)
	socket.on('doc_update', handleUpdate)
	if (socket.connected) subscribe()

	return () => {
		if (!active) return
		active = false
		socket.off('connect', subscribe)
		socket.off('doc_update', handleUpdate)
		if (socket.connected) socket.emit('doc_unsubscribe', doctype, name)
	}
}