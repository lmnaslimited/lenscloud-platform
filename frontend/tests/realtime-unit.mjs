import assert from 'node:assert/strict'
import { EventEmitter } from 'node:events'

import { watchDocument } from '../src/lib/realtime.js'
import { getSocketUrl } from '../src/socket.js'

global.window = {
	site_name: 'dev.localhost',
	socketio_port: 9000,
	location: {
		protocol: 'http:',
		hostname: 'dev.localhost',
		port: '8000',
		origin: 'http://dev.localhost:8000',
	},
}
assert.equal(getSocketUrl(), 'http://dev.localhost:9000/dev.localhost')
window.location = {
	protocol: 'https:',
	hostname: 'cloud.example.com',
	port: '',
	origin: 'https://cloud.example.com',
}
window.site_name = 'cloud.example.com'
assert.equal(getSocketUrl(), 'https://cloud.example.com/cloud.example.com')

class SocketMock extends EventEmitter {
	connected = true
	emitted = []
	emit(event, ...args) {
		this.emitted.push([event, ...args])
		return super.emit(event, ...args)
	}
}

const socket = new SocketMock()
let updates = 0
const stop = watchDocument(socket, {
	doctype: 'Issue',
	name: 'ISS-1',
	onUpdate: () => updates++,
})

assert.deepEqual(socket.emitted[0], ['doc_subscribe', 'Issue', 'ISS-1'])
socket.emit('doc_update', { doctype: 'Issue', name: 'ISS-2' })
assert.equal(updates, 0)
socket.emit('doc_update', { doctype: 'Issue', name: 'ISS-1' })
assert.equal(updates, 1)
socket.connected = false
socket.emit('connect')
assert.deepEqual(socket.emitted.at(-1), ['doc_subscribe', 'Issue', 'ISS-1'])
stop()
socket.emit('doc_update', { doctype: 'Issue', name: 'ISS-1' })
assert.equal(updates, 1)
assert.equal(socket.listenerCount('connect'), 0)
assert.equal(socket.listenerCount('doc_update'), 0)

console.log('realtime subscription filtering, reconnect, and cleanup passed')