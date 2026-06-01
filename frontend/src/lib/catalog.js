import {
	ArrowRight,
	CloudDownload,
	Database,
	Globe2,
	LayoutDashboard,
	Layers3,
	RefreshCcw,
	Server,
	Settings2,
	Pause,
	ShieldAlert,
	SquareArrowOutUpRight,
	Users,
	UserRound,
	AlertTriangle,
	CircleHelp,
} from 'lucide-vue-next'

export const platformResources = [
	{
		key: 'customers',
		scope: 'platform',
		label: 'Customers',
		doctype: 'Customer',
		route: '/platform/customers',
		detailRoute: (name) => `/platform/customers/${encodeURIComponent(name)}`,
		icon: Users,
		listHelp: 'Customer records, identity links, and primary region placement.',
		summaryFields: [
			{ key: 'first_name', label: 'First name' },
			{ key: 'last_name', label: 'Last name' },
			{ key: 'region', label: 'Primary region', linkPrefix: '/platform/regions/' },
			{ key: 'external_customer_id', label: 'External ID' },
		],
		detailFields: [
			{ key: 'name', label: 'Customer ID' },
			{ key: 'first_name', label: 'First name' },
			{ key: 'last_name', label: 'Last name' },
			{ key: 'user', label: 'User' },
			{ key: 'region', label: 'Primary region', linkPrefix: '/platform/regions/' },
			{ key: 'external_customer_id', label: 'External ID' },
		],
		relations: [
			{
				label: 'Sites',
				doctype: 'Site',
				linkField: 'customer',
				sourceField: 'name',
				fields: ['name', 'title', 'bench', 'modified'],
				route: (name) => `/platform/sites/${encodeURIComponent(name)}`,
			},
		],
		actions: [
			{
				key: 'request-site',
				label: 'Request site',
				icon: SquareArrowOutUpRight,
				description: 'Capture a new site request in the UI. Backend creation support is not wired yet.',
				backendSupported: false,
				fields: [
					{ key: 'company_name', label: 'Company name', type: 'text', placeholder: 'Acme Incorporated' },
					{ key: 'preferred_region', label: 'Preferred region', type: 'text', placeholder: 'us-east' },
					{ key: 'preferred_release_group', label: 'Preferred release group', type: 'text', placeholder: '2026.06' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Describe the request and rollout constraints.' },
				],
			},
		],
	},
	{
		key: 'release-groups',
		scope: 'platform',
		label: 'Release Groups',
		doctype: 'Release Group',
		route: '/platform/release-groups',
		detailRoute: (name) => `/platform/release-groups/${encodeURIComponent(name)}`,
		icon: Layers3,
		listHelp: 'Release groups are the unit of bench image management.',
		summaryFields: [
			{ key: 'title', label: 'Title' },
			{ key: 'registry', label: 'Registry' },
		],
		detailFields: [
			{ key: 'name', label: 'Release group ID' },
			{ key: 'title', label: 'Title' },
			{ key: 'registry', label: 'Registry' },
		],
		relations: [
			{
				label: 'Benches',
				doctype: 'Bench',
				linkField: 'release_group',
				sourceField: 'name',
				fields: ['name', 'title', 'region', 'privacy'],
				route: (name) => `/platform/benches/${encodeURIComponent(name)}`,
			},
		],
		actions: [
			{
				key: 'promote-release',
				label: 'Promote release',
				icon: ArrowRight,
				description: 'Promotion flow is exposed in the UI, but backend orchestration is not wired in this pass.',
				backendSupported: false,
				fields: [
					{ key: 'target', label: 'Target context', type: 'text', placeholder: 'Production bench or release lane' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Promotion notes and expected impact.' },
				],
			},
		],
	},
	{
		key: 'benches',
		scope: 'platform',
		label: 'Benches',
		doctype: 'Bench',
		route: '/platform/benches',
		detailRoute: (name) => `/platform/benches/${encodeURIComponent(name)}`,
		icon: Server,
		listHelp: 'Bench records group runtime capacity by release group and region.',
		summaryFields: [
			{ key: 'title', label: 'Title' },
			{ key: 'release_group', label: 'Release group', linkPrefix: '/platform/release-groups/' },
			{ key: 'region', label: 'Region', linkPrefix: '/platform/regions/' },
			{ key: 'privacy', label: 'Privacy' },
		],
		detailFields: [
			{ key: 'name', label: 'Bench ID' },
			{ key: 'title', label: 'Title' },
			{ key: 'release_group', label: 'Release group', linkPrefix: '/platform/release-groups/' },
			{ key: 'region', label: 'Region', linkPrefix: '/platform/regions/' },
			{ key: 'privacy', label: 'Privacy' },
		],
		relations: [
			{
				label: 'Sites',
				doctype: 'Site',
				field: 'bench',
				fields: ['name', 'title', 'customer', 'modified'],
				route: (name) => `/platform/sites/${encodeURIComponent(name)}`,
			},
		],
		actions: [
			{
				key: 'upgrade-bench',
				label: 'Upgrade bench',
				icon: RefreshCcw,
				description: 'Upgrade controls are surfaced in the UI, while the orchestration backend remains a gap.',
				backendSupported: false,
				fields: [
					{ key: 'target_release_group', label: 'Target release group', type: 'text', placeholder: 'Release group name' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Why this upgrade is needed.' },
				],
			},
			{
				key: 'retire-bench',
				label: 'Retire bench',
				icon: ShieldAlert,
				description: 'Retirement is represented in the UI; backend execution is not wired yet.',
				backendSupported: false,
				fields: [
					{ key: 'reason', label: 'Reason', type: 'textarea', placeholder: 'Explain the retirement request.' },
				],
			},
		],
	},
	{
		key: 'sites',
		scope: 'platform',
		label: 'Sites',
		doctype: 'Site',
		route: '/platform/sites',
		detailRoute: (name) => `/platform/sites/${encodeURIComponent(name)}`,
		icon: Globe2,
		listHelp: 'Tenant instances inside benches, tied to customers and runtime placement.',
		summaryFields: [
			{ key: 'title', label: 'Title' },
			{ key: 'bench', label: 'Bench', linkPrefix: '/platform/benches/' },
			{ key: 'customer', label: 'Customer', linkPrefix: '/platform/customers/' },
		],
		detailFields: [
			{ key: 'name', label: 'Site ID' },
			{ key: 'title', label: 'Title' },
			{ key: 'bench', label: 'Bench', linkPrefix: '/platform/benches/' },
			{ key: 'customer', label: 'Customer', linkPrefix: '/platform/customers/' },
		],
		relations: [
			{
				label: 'Bench',
				doctype: 'Bench',
				linkField: 'name',
				sourceField: 'bench',
				fields: ['name', 'title', 'release_group', 'region'],
				route: (name) => `/platform/benches/${encodeURIComponent(name)}`,
			},
		],
		actions: [
			{
				key: 'create-site',
				label: 'Create site',
				icon: SquareArrowOutUpRight,
				description: 'Site creation is shown as a UI flow while the backend contract is still pending.',
				backendSupported: false,
				fields: [
					{ key: 'company_name', label: 'Company name', type: 'text', placeholder: 'Acme Incorporated' },
					{ key: 'target_region', label: 'Target region', type: 'text', placeholder: 'us-east' },
					{ key: 'target_bench', label: 'Target bench', type: 'text', placeholder: 'bench-us-east-01' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Any placement or migration constraints.' },
				],
			},
			{
				key: 'suspend-site',
				label: 'Suspend site',
				icon: Pause,
				description: 'Suspension is surfaced here, but the actual state transition remains a backend gap.',
				backendSupported: false,
				fields: [
					{ key: 'reason', label: 'Reason', type: 'textarea', placeholder: 'Why is the site being suspended?' },
				],
			},
			{
				key: 'delete-site',
				label: 'Delete site',
				icon: AlertTriangle,
				description: 'Destructive deletion is represented in the UI, but backend execution is not wired in this pass.',
				backendSupported: false,
				fields: [
					{ key: 'confirmation', label: 'Confirmation', type: 'text', placeholder: 'Type DELETE to confirm intent' },
					{ key: 'reason', label: 'Reason', type: 'textarea', placeholder: 'Explain the deletion request.' },
				],
			},
			{
				key: 'backup-site',
				label: 'Backup site',
				icon: CloudDownload,
				description: 'Backup request entry point is present in the UI; backend dispatch remains a gap.',
				backendSupported: false,
				fields: [
					{ key: 'label', label: 'Backup label', type: 'text', placeholder: 'nightly-2026-06-01' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Retention or restore intent.' },
				],
			},
			{
				key: 'restore-site',
				label: 'Restore site',
				icon: Database,
				description: 'Restore entry point exists in the UI; backend execution is not implemented here.',
				backendSupported: false,
				fields: [
					{ key: 'backup_name', label: 'Backup name', type: 'text', placeholder: 'latest backup label' },
					{ key: 'target_time', label: 'Target time', type: 'text', placeholder: 'optional timestamp' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Restore intent and constraints.' },
				],
			},
			{
				key: 'upgrade-site',
				label: 'Upgrade site',
				icon: RefreshCcw,
				description: 'Upgrade entry point is a UI-only control until the orchestration backend lands.',
				backendSupported: false,
				fields: [
					{ key: 'target_release_group', label: 'Target release group', type: 'text', placeholder: 'Release group name' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Expected impact and timing.' },
				],
			},
			{
				key: 'dns-site',
				label: 'DNS automation',
				icon: CircleHelp,
				description: 'DNS automation is surfaced in the UI, but the workflow backend is a planned gap.',
				backendSupported: false,
				fields: [
					{ key: 'record', label: 'Requested record', type: 'text', placeholder: 'subdomain.example.com' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'DNS lifecycle details.' },
				],
			},
		],
	},
	{
		key: 'regions',
		scope: 'platform',
		label: 'Regions',
		doctype: 'Region',
		route: '/platform/regions',
		detailRoute: (name) => `/platform/regions/${encodeURIComponent(name)}`,
		icon: Globe2,
		listHelp: 'Placement hierarchy for region-aware and environment-aware workflows.',
		tree: {
			parentField: 'parent_region',
			groupField: 'is_group',
			orderBy: 'lft asc',
			extraFields: ['lft', 'rgt'],
		},
		listLimit: 200,
		summaryFields: [
			{ key: 'title', label: 'Title' },
			{ key: 'parent_region', label: 'Parent region', linkPrefix: '/platform/regions/' },
			{ key: 'is_group', label: 'Group' },
		],
		detailFields: [
			{ key: 'name', label: 'Region ID' },
			{ key: 'title', label: 'Title' },
			{ key: 'parent_region', label: 'Parent region', linkPrefix: '/platform/regions/' },
			{ key: 'is_group', label: 'Group' },
		],
		relations: [
			{
				label: 'Customers',
				doctype: 'Customer',
				linkField: 'region',
				sourceField: 'name',
				fields: ['name', 'first_name', 'last_name', 'external_customer_id'],
				route: (name) => `/platform/customers/${encodeURIComponent(name)}`,
			},
			{
				label: 'Benches',
				doctype: 'Bench',
				linkField: 'region',
				sourceField: 'name',
				fields: ['name', 'title', 'release_group', 'privacy'],
				route: (name) => `/platform/benches/${encodeURIComponent(name)}`,
			},
		],
		actions: [],
	},
]

export const platformSettings = {
	key: 'settings',
	scope: 'platform',
	label: 'Platform Settings',
	doctype: 'Platform Settings',
	route: '/platform/settings',
	icon: Settings2,
	editable: true,
	summaryFields: [
		{ key: 'root_domain', label: 'Root domain' },
		{ key: 'crm_system', label: 'CRM system' },
		{ key: 'support_system', label: 'Support system' },
		{ key: 'billing_system', label: 'Billing system' },
	],
	detailFields: [
		{ key: 'root_domain', label: 'Root domain' },
		{ key: 'crm_system', label: 'CRM system' },
		{ key: 'support_system', label: 'Support system' },
		{ key: 'billing_system', label: 'Billing system' },
	],
}

export const customerResources = [
	{
		key: 'customer-account',
		scope: 'customer',
		label: 'Account',
		doctype: 'Customer',
		route: '/customer/account',
		icon: UserRound,
		listHelp: 'Your customer identity, region, and external account links.',
		summaryFields: [
			{ key: 'first_name', label: 'First name' },
			{ key: 'last_name', label: 'Last name' },
			{ key: 'region', label: 'Primary region', linkPrefix: '/platform/regions/' },
		],
		detailFields: [
			{ key: 'name', label: 'Customer ID' },
			{ key: 'first_name', label: 'First name' },
			{ key: 'last_name', label: 'Last name' },
			{ key: 'region', label: 'Primary region', linkPrefix: '/platform/regions/' },
			{ key: 'external_customer_id', label: 'External ID' },
		],
		associated: true,
		actions: [
			{
				key: 'request-site',
				label: 'Request site',
				icon: SquareArrowOutUpRight,
				description: 'This entry point collects the request in the UI. Backend creation support is not yet wired.',
				backendSupported: false,
				fields: [
					{ key: 'company_name', label: 'Company name', type: 'text', placeholder: 'Acme Incorporated' },
					{ key: 'preferred_region', label: 'Preferred region', type: 'text', placeholder: 'us-east' },
					{ key: 'preferred_release_group', label: 'Preferred release group', type: 'text', placeholder: '2026.06' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Describe the request and rollout constraints.' },
				],
			},
		],
	},
	{
		key: 'customer-sites',
	scope: 'customer',
		label: 'Sites',
		doctype: 'Site',
		route: '/customer/sites',
		detailRoute: (name) => `/customer/sites/${encodeURIComponent(name)}`,
		icon: Globe2,
		listHelp: 'Sites linked to your customer record.',
		customerScoped: true,
		summaryFields: [
			{ key: 'title', label: 'Title' },
			{ key: 'bench', label: 'Bench', linkPrefix: '/platform/benches/' },
			{ key: 'customer', label: 'Customer', linkPrefix: '/platform/customers/' },
		],
		detailFields: [
			{ key: 'name', label: 'Site ID' },
			{ key: 'title', label: 'Title' },
			{ key: 'bench', label: 'Bench', linkPrefix: '/platform/benches/' },
			{ key: 'customer', label: 'Customer', linkPrefix: '/platform/customers/' },
		],
		relations: [
			{
				label: 'Bench',
				doctype: 'Bench',
				linkField: 'name',
				sourceField: 'bench',
				fields: ['name', 'title', 'release_group', 'region'],
				route: (name) => `/platform/benches/${encodeURIComponent(name)}`,
			},
		],
		actions: [
			{
				key: 'request-site',
				label: 'Request site',
				icon: SquareArrowOutUpRight,
				description: 'Create requests are captured in the UI first while backend orchestration remains pending.',
				backendSupported: false,
				fields: [
					{ key: 'company_name', label: 'Company name', type: 'text', placeholder: 'Acme Incorporated' },
					{ key: 'preferred_region', label: 'Preferred region', type: 'text', placeholder: 'us-east' },
					{ key: 'preferred_release_group', label: 'Preferred release group', type: 'text', placeholder: '2026.06' },
					{ key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Describe the request and rollout constraints.' },
				],
			},
		],
	},
]

export const platformNav = [
	{
		heading: 'Platform console',
		items: [
			{ key: 'platform-dashboard', label: 'Dashboard', note: 'System status and record shortcuts', route: '/platform/dashboard', icon: LayoutDashboard },
			{ key: 'platform-customers', label: 'Customers', note: 'Identity and access', route: '/platform/customers', icon: Users },
			{ key: 'platform-release-groups', label: 'Release Groups', note: 'Image management unit', route: '/platform/release-groups', icon: Layers3 },
			{ key: 'platform-benches', label: 'Benches', note: 'Runtime grouping', route: '/platform/benches', icon: Server },
			{ key: 'platform-sites', label: 'Sites', note: 'Tenant instances', route: '/platform/sites', icon: Globe2 },
			{ key: 'platform-regions', label: 'Regions', note: 'Placement hierarchy', route: '/platform/regions', icon: Globe2 },
			{ key: 'platform-settings', label: 'Platform Settings', note: 'DNS and integrations', route: '/platform/settings', icon: Settings2 },
		],
	},
]

export const customerNav = [
	{
		heading: 'Customer portal',
		items: [
			{ key: 'customer-dashboard', label: 'Dashboard', note: 'Your active work surface', route: '/customer/dashboard', icon: LayoutDashboard },
			{ key: 'customer-account', label: 'Account', note: 'Identity and region', route: '/customer/account', icon: UserRound },
			{ key: 'customer-sites', label: 'Sites', note: 'Your tenant instances', route: '/customer/sites', icon: Globe2 },
		],
	},
]

export function getResourceByKey(key) {
	return [...platformResources, ...customerResources].find((resource) => resource.key === key) || null
}

export function getRoutesForScope(scope) {
	return scope === 'customer' ? customerNav : platformNav
}

export function getHomeRoute(session) {
	if (session?.canAccessPlatform) {
		return '/platform/dashboard'
	}

	return '/customer/dashboard'
}
