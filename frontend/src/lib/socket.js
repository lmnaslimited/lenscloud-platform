// // src/socket.js
// import { initSocket } from 'frappe-ui'

// // initSocket automatically connects using current site credentials & location
// export const socket = initSocket()

// import { io } from 'socket.io-client'
// import { getCachedListResource, getCachedResource } from 'frappe-ui'

// export function initSocket() {
    
//     let socketio_port = window.socketio_port || 9000
//     let host = window.location.hostname
//     let siteName = window.site_name || "lenscloud"
//     let port = window.location.port ? `:${socketio_port}` : ''
//     let protocol = port ? 'http' : 'https'
//     let url = `${protocol}://${host}${port}/${siteName}`
  
//     let socket = io(url, {
//       withCredentials: true,
//       reconnectionAttempts: 5,
//     })

//     return socket
// }

import { io } from 'socket.io-client'

let socket = null

export function initSocket() {
  // 1. Singleton check: return existing socket if already connected
  if (socket) return socket

  const socketioPort = window.socketio_port || 9000
  const host = window.location.hostname
  const siteName = window.site_name || 'test.localhost'

  // 2. Dynamic protocol detection (avoids Mixed Content errors)
  const protocol = window.location.protocol // 'http:' or 'https:'
  const port = window.location.port ? `:${socketioPort}` : ''
  const url = `${protocol}//${host}${port}/${siteName}`

  socket = io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
    transports: ['websocket', 'polling'],
  })

  return socket
}