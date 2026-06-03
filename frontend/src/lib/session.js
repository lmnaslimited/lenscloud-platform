import { defineStore } from 'pinia'
import { getLoggedUser, getUserRoles, isGuestUser } from './api'

export const PLATFORM_ROLES = new Set([
	'Administrator',
	'System Manager',
	'Workspace Manager',
	'LensCloud Platform Admin',
	'LensCloud Operator',
])

export const CUSTOMER_ROLES = new Set([
	'Customer',
	'Customer User',
	'Portal User',
	'Website User',
	'All',
])

export const useSessionStore = defineStore('session', {
	state: () => ({
		status: 'idle',
		user: null,
		roles: [],
		error: null,
	}),
	getters: {
		isAuthenticated: (state) => !isGuestUser(state.user),
		isPlatformUser: (state) => state.roles.some((role) => PLATFORM_ROLES.has(role)),
		isCustomerUser: (state) => state.roles.some((role) => CUSTOMER_ROLES.has(role)),
		canAccessPlatform: (state) => !isGuestUser(state.user) && (state.roles.some((role) => PLATFORM_ROLES.has(role)) || state.roles.length === 0),
		canAccessCustomer: (state) => !isGuestUser(state.user),
		defaultHome: (state) => {
			if (state.roles.some((role) => PLATFORM_ROLES.has(role)) || state.roles.length === 0) {
				return '/platform/dashboard'
			}

			return '/customer/dashboard'
		},
	},
	actions: {
		async initialize() {
			if (this.status === 'loading' || this.status === 'ready') {
				return
			}

			this.status = 'loading'
			this.error = null

			try {
				this.user = await getLoggedUser()
				if (!isGuestUser(this.user)) {
					this.roles = await getUserRoles(this.user)
				} else {
					this.roles = []
				}
			} catch (error) {
				const message = error?.message || 'Unable to load session.'
				this.error = /403|not permitted|forbidden/i.test(message) ? null : message
				this.user = 'Guest'
				this.roles = []
			} finally {
				this.status = 'ready'
			}
		},
		reset() {
			this.status = 'idle'
			this.user = null
			this.roles = []
			this.error = null
		},
	},
})
