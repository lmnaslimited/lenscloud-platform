<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, inject } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Alert, Badge, Button } from 'frappe-ui'
import {
	AlertTriangle,
	Check,
	CheckCircle2,
	Clock3,
	ExternalLink,
	Globe2,
	RefreshCcw,
	Send,
	ShieldCheck,
	Sparkles,
	XCircle,
	Headset,
	Rocket,Clock, CircleCheckBig, Globe, CreditCard, Layers, Workflow, Building, Shield, Users, LifeBuoy
} from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import WorkspaceLayout from '@/components/WorkspaceLayout.vue'
import posthog from 'posthog-js'

const route = useRoute()
const router = useRouter()
// Cleanly inject the socket instance provided in main.js
const socket = inject('socket')

const loading = ref(true)
const submitting = ref(false)
const polling = ref(false)
const advancing = ref(false)
const canonicalProgress = ref(null)
const setupSchemaLoading = ref(false)
const setupDialogOpen = ref(false)
const setupDialogDismissed = ref(false)
const error = ref('')
const context = ref(null)
const selectedPlan = ref('')
const result = ref(null)
const step = ref('choose')
const placementFilter = ref('all')
let progressPoller = null
let advanceTimer = null
const setupSchemaState = ref(null)

const form = reactive({
	region: '',
	site_name: '',
	company_name: '',
	subdomain: '',
	notes: '',
	setup_defaults: {},
})

const plans = computed(() => context.value?.plans || [])
const regions = computed(() => context.value?.regions || [])
const settings = computed(() => context.value?.settings || {})
const usage = computed(() => context.value?.usage || {})
const membership = computed(() => context.value?.membership || context.value?.customer || {})
const membershipPending = computed(() => membership.value?.status === 'Pending' || membership.value?.membership_status === 'Pending')
const permissions = computed(() => context.value?.permissions || {})
const canCreateSubscription = computed(() => Boolean(permissions.value.can_create_subscription))
const canReadPlans = computed(() => Boolean(permissions.value.doctypes?.Plan?.read))
const existingSites = computed(() => context.value?.sites || [])
const freePlan = computed(() => plans.value.find((plan) => plan.is_free) || null)
const selectedPlanRecord = computed(() => plans.value.find((plan) => plan.name === selectedPlan.value) || freePlan.value || plans.value[0] || null)
const visiblePlans = computed(() => plans.value.filter((plan) => placementFilter.value === 'all' || planPlacement(plan) === placementFilter.value))
const selectedRegion = computed(() => regions.value.find((region) => region.name === form.region) || null)
const selectableRegions = computed(() => regions.value.filter((item) => !item.is_group).slice(0, 8))
const normalizedSubdomain = computed(() => form.subdomain.trim().toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/^-+|-+$/g, ''))
const domainSuffix = computed(() => settings.value.root_domain ? `.${settings.value.root_domain}` : '.lmnas.cloud')
const hostnamePreview = computed(() => normalizedSubdomain.value && settings.value.root_domain ? `${normalizedSubdomain.value}.${settings.value.root_domain}` : '')
const setupSchema = computed(() => context.value?.setup_schema || setupSchemaState.value || null)
const setupFields = computed(() => setupSchema.value?.fields || [])
const setupDefaultsComplete = computed(() => Boolean(setupSchema.value) && setupFields.value.every((field) => !field.required || Boolean(form.setup_defaults[field.name])))
const setupComplete = computed(() => Boolean(form.region && form.site_name.trim() && normalizedSubdomain.value && settings.value.root_domain && setupDefaultsComplete.value))
const canStartFree = computed(() => Boolean(selectedPlanRecord.value?.is_free && !planDisabled(selectedPlanRecord.value) && setupComplete.value))
const resultSite = computed(() => existingSites.value.find((site) => site.name === result.value?.site || site.subscription === result.value?.subscription) || null)
const resultRouteReady = computed(() => result.value?.route_status === 'Ready' || resultSite.value?.route_status === 'Ready')
const oauthConfiguredStatuses = new Set(['Configured', 'Enabled'])
const resultOauthStatus = computed(() => result.value?.oauth_status || resultSite.value?.oauth_status || 'Not Checked')
const resultOauthConfigured = computed(() => oauthConfiguredStatuses.has(resultOauthStatus.value))
const siteReadyForOpen = (site) => ['Ready', 'Active'].includes(site?.site_status) && site?.route_status === 'Ready' && site?.setup_status === 'Complete' && oauthConfiguredStatuses.has(site?.oauth_status)
const hasReadySite = computed(() => resultReady.value || existingSites.value.some(siteReadyForOpen))
const readySiteUrl = computed(() => {
	console.log('resultSite', resultSite.value)
	if (provisioningMode.value === 'ready' && resultOauthConfigured.value) return result.value?.access_url || resultSite.value?.access_url || ''
	return existingSites.value.find((site) => siteReadyForOpen(site) && site.access_url)?.access_url || ''
})
const effectiveStage = computed(
    () => currentStage.value ?? canonicalProgress.value?.stage
)
const canonicalMode = computed(() => ({
	requested: 'started', runtime_reconciling: 'started', route_pending: 'route_pending',
	bootstrap_installing: 'bootstrap_installing', setup_completing: 'setup_running', setup_verifying: 'setup_checking',
	oauth_configuring: 'oauth_configuring', oauth_verifying: 'oauth_checking', ready: 'ready',
	blocked_customer_input: 'setup_required', blocked_platform_action: 'failed', blocked_infra_action: 'failed', failed: 'failed',
}[effectiveStage.value] || ''))
const provisioningMode = computed(() => canonicalMode.value || result.value?.provisioning || (result.value?.reconcile?.status === 'dry_run' ? 'paused' : ''))
const resultStarted = computed(() => ['started', 'route_pending', 'bootstrap_installing', 'setup_checking', 'setup_running', 'setup_required', 'oauth_checking', 'oauth_configuring', 'ready'].includes(provisioningMode.value))
const resultPaused = computed(() => !canonicalProgress.value && (provisioningMode.value === 'paused' || provisioningMode.value === 'dry_run'))
const resultFailed = computed(() => canonicalProgress.value ? ['failed', 'blocked'].includes(canonicalProgress.value.stage_status) : ['failed', 'bootstrap_failed', 'oauth_failed'].includes(provisioningMode.value))
const resultSetupRequired = computed(() => effectiveStage.value === 'blocked_customer_input' || provisioningMode.value === 'setup_required')
const resultBootstrapStatus = computed(() => result.value?.bootstrap_status || resultSite.value?.bootstrap_status || '')
const resultReady = computed(() => provisioningMode.value === 'ready')
const resultRetryable = computed(() => Boolean(result.value?.site && (canonicalProgress.value ? canonicalProgress.value.can_retry : (result.value?.retry_available || resultStarted.value || resultPaused.value || resultFailed.value))))
const progressActive = computed(() => Boolean(result.value?.site && step.value === 'result' && !resultReady.value && !resultFailed.value && !resultSetupRequired.value))
const selectedSiteLabel = computed(() => result.value?.hostname || result.value?.access_url?.replace(/^https?:\/\//, '') || resultSite.value?.title || resultSite.value?.name || hostnamePreview.value || '')

const flowSteps = computed(() => {
	const isFree = Boolean(selectedPlanRecord.value?.is_free)

	return [
		{ key: 'choose', label: 'Choose Plan', helper: 'Select the service that fits today.' },
		{ key: 'setup', label: 'Setup Workspace', helper: 'Pick Region and Workspace details.' },
		{
			key: 'checkout',
			label: isFree ? 'Free Checkout' : 'Checkout',
			helper: isFree ? '$0 due today.' : 'Flexible Payment Options.'
		},
		{
			key: 'result',
			label: resultStarted.value || resultReady.value ? 'Launch Workspace' : 'Approval',
			helper: 'Track setup and open when ready.'
		},
	]
})

const currentStepIndex = computed(() => Math.max(0, flowSteps.value.findIndex((item) => item.key === step.value)))
const screenTitle = computed(() => {
	if (step.value === 'choose') return 'Select your LensCloud service'
	if (step.value === 'setup') return 'Set up your first Workspace'
	if (step.value === 'checkout') return 'Review Subscription'
	return resultStarted.value || resultReady.value ? 'Your Workspace launch has started' : 'Your request is received'
})
const screenSubtitle = computed(() => {
	if (step.value === 'choose') return 'Pick a Platform Plan to continue.'
	if (step.value === 'setup') return 'These details reserve your customer-facing Workspace. LensCloud chooses compatible capacity for you.'
	if (step.value === 'checkout') return 'The Free Plan has no payment method requirement. Review once and start the subscription.'
	return resultStarted.value || resultReady.value ? 'Follow setup progress here, then open the Workspace when it is ready.' : 'The LensCloud team will review this before setup starts.'
})

const rawProvisioningSteps = computed(() => {
	const usingRealtime = Boolean(canonicalProgress.value)
	const stage = effectiveStage.value

	const attempted = Boolean(result.value?.site || resultStarted.value || resultPaused.value || resultFailed.value || resultReady.value)
	const runtimeProgressed = ['route_pending', 'bootstrap_installing', 'setup_checking', 'setup_running', 'setup_required', 'oauth_checking', 'oauth_configuring', 'ready'].includes(provisioningMode.value)
	const runtimeReady = Boolean(runtimeProgressed || ['Ready', 'Active'].includes(result.value?.site_status) || result.value?.provisioning_status === 'Ready' || ['Ready', 'Active'].includes(resultSite.value?.site_status))
	// const routeReady = Boolean(resultRouteReady.value)
	const routeReady = usingRealtime
    ? [
        'bootstrap_installing',
        'setup_completing',
        'setup_verifying',
        'oauth_configuring',
        'oauth_verifying',
        'ready',
    ].includes(stage)
    : Boolean(resultRouteReady.value)

	const routeFailed = Boolean(result.value?.route_status === 'Failed' || resultSite.value?.route_status === 'Failed')
	const setupStatus = result.value?.setup_status || resultSite.value?.setup_status || 'Not Checked'
	const setupError = result.value?.setup_error || resultSite.value?.setup_error || ''
	const bootstrapStatus = resultBootstrapStatus.value
	// const setupDone = setupStatus === 'Complete' || resultReady.value
	const setupDone = usingRealtime
    ? [
        'oauth_configuring',
        'oauth_verifying',
        'ready',
    ].includes(stage)
    : (
        setupStatus === 'Complete' ||
        resultReady.value
    )
	const setupBlocked = setupStatus === 'Blocked' || resultSetupRequired.value
	const bootstrapFailed = bootstrapStatus === 'Failed' || provisioningMode.value === 'bootstrap_failed' || /bootstrap app install failed/i.test(setupError)
	// const bootstrapInstalling = provisioningMode.value === 'bootstrap_installing' || ['Queued', 'Running'].includes(bootstrapStatus)
	const bootstrapInstalling = usingRealtime
    ? stage === 'bootstrap_installing'
    : (
        provisioningMode.value === 'bootstrap_installing' ||
        ['Queued', 'Running'].includes(bootstrapStatus)
    )

	const bootstrapAdvanced = ['setup_checking', 'setup_running', 'setup_required', 'oauth_checking', 'oauth_configuring', 'ready'].includes(provisioningMode.value)
	// const bootstrapDone = !bootstrapFailed && !bootstrapInstalling && (bootstrapStatus === 'Succeeded' || setupStatus === 'Complete' || bootstrapAdvanced)
	const bootstrapDone = usingRealtime
    ? [
        'setup_completing',
        'setup_verifying',
        'oauth_configuring',
        'oauth_verifying',
        'ready',
    ].includes(stage)
    : (
        !bootstrapFailed &&
        !bootstrapInstalling &&
        (
            bootstrapStatus === 'Succeeded' ||
            setupStatus === 'Complete' ||
            bootstrapAdvanced
        )
    )
	const setupFailed = !bootstrapFailed && (setupStatus === 'Failed' || (provisioningMode.value === 'failed' && routeReady))
	// const setupRunning = provisioningMode.value === 'setup_running' || setupStatus === 'Required'
	const setupRunning = usingRealtime
    ? stage === 'setup_completing'
    : (
        provisioningMode.value === 'setup_running' ||
        setupStatus === 'Required'
    )
	// const setupChecking = provisioningMode.value === 'setup_checking'
	const setupChecking = usingRealtime
    ? stage === 'setup_verifying'
    : provisioningMode.value === 'setup_checking'
	const oauthStatus = resultOauthStatus.value
	// const oauthDone = resultOauthConfigured.value || resultReady.value
	const oauthDone = usingRealtime
    ? stage === 'ready'
    : (
        resultOauthConfigured.value ||
        resultReady.value
    )
	const oauthFailed = oauthStatus === 'Failed' || provisioningMode.value === 'oauth_failed'
	// const oauthRunning = ['Running', 'Pending'].includes(oauthStatus) || ['oauth_checking', 'oauth_configuring'].includes(provisioningMode.value)
	const oauthRunning = usingRealtime
    ? [
        'oauth_configuring',
        'oauth_verifying',
    ].includes(stage)
    : (
        ['Running', 'Pending'].includes(oauthStatus) ||
        ['oauth_checking', 'oauth_configuring'].includes(provisioningMode.value)
    )
	return [
		{ label: 'Subscription approved', state: attempted ? 'done' : 'pending', helper: attempted ? 'Your LensCloud service subscription is active.' : 'Waiting for subscription confirmation.' },
		{ label: 'Workspace reserved', state: attempted ? 'done' : 'pending', helper: attempted ? 'Your Workspace address is reserved for you.' : 'Waiting for Workspace reservation.' },
		{ label: 'Preparing workspace', state: resultFailed.value && !runtimeReady ? 'failed' : resultPaused.value ? 'paused' : runtimeReady ? 'done' : resultStarted.value ? 'active' : 'pending', helper: resultFailed.value && !runtimeReady ? 'Setup needs another attempt from Platform.' : resultPaused.value ? 'Live setup is paused until Platform apply is enabled.' : runtimeReady ? 'Workspace preparation is complete.' : resultStarted.value ? 'LensCloud is preparing your workspace.' : 'Waiting to start.' },
		{ label: 'Connecting HTTPS', state: routeFailed ? 'failed' : routeReady ? 'done' : runtimeReady ? 'active' : 'pending', helper: routeFailed ? 'Secure access needs another status check or support review.' : routeReady ? 'Secure access is ready.' : runtimeReady ? 'LensCloud is checking secure access (approx. 3 mins).' : 'This starts after workspace preparation.' },
		{ label: 'Installing default apps', state: bootstrapFailed ? 'failed' : bootstrapDone ? 'done' : bootstrapInstalling || routeReady ? 'active' : 'pending', helper: bootstrapFailed ? 'Default app installation did not complete. Retry or contact support.' : bootstrapDone ? 'Default apps from the Release Group are installed.' : bootstrapInstalling || routeReady ? 'LensCloud is installing the default apps for this Workspace.' : 'This starts after secure access is ready.' },
		{ label: 'Checking setup status', state: setupFailed ? 'failed' : setupDone || setupRunning || setupBlocked ? 'done' : setupChecking || (routeReady && bootstrapDone) ? 'active' : 'pending', helper: setupDone || setupRunning || setupBlocked ? 'First-time setup status was checked.' : routeReady && bootstrapDone ? 'LensCloud checks whether your Workspace needs first-time setup.' : 'This starts after default apps are installed.' },
		{ label: 'Setting Workspace defaults', state: setupFailed || setupBlocked ? 'failed' : setupDone ? 'done' : setupRunning ? 'active' : 'pending', helper: setupBlocked ? 'Required setup defaults are missing. Reopen setup defaults and retry.' : setupFailed ? 'Setup defaults could not be applied. Retry or contact support.' : setupDone ? 'Workspace defaults are applied.' : setupRunning ? 'LensCloud is applying required setup defaults.' : 'This starts if the Workspace needs first-time setup.' },
		{ label: 'Platform access', state: oauthFailed ? 'failed' : oauthDone ? 'done' : setupDone || oauthRunning ? 'active' : 'pending', helper: oauthFailed ? 'Single sign-on could not be configured. Retry or contact support.' : oauthDone ? 'Single sign-on is configured for this Workspace.' : setupDone || oauthRunning ? 'LensCloud is configuring Platform sign-on.' : 'This starts after Workspace defaults are applied.' },
		{ label: 'Ready to open', state: resultReady.value ? 'done' : oauthDone ? 'active' : 'pending', helper: resultReady.value ? 'Your Workspace is ready to open.' : oauthDone ? 'LensCloud is publishing the Open Workspace action.' : 'We will show the Open Workspace action when access is verified.' },
	]
})


const targetProvisioningIndex = computed(() => {
	const steps = rawProvisioningSteps.value
	const blockedIndex = steps.findIndex((item) => ['failed', 'paused'].includes(item.state))
	if (blockedIndex >= 0) return blockedIndex
	const activeIndex = steps.findIndex((item) => item.state === 'active')
	if (activeIndex >= 0) return activeIndex
	let lastDoneIndex = 0
	steps.forEach((item, index) => {
		if (item.state === 'done') lastDoneIndex = index
	})
	return lastDoneIndex
})

const provisioningSteps = computed(() => {
	const steps = rawProvisioningSteps.value
	const targetIndex = targetProvisioningIndex.value
	return steps.map((item, index) => {
		if (!result.value?.site) return item
		if (index < targetIndex) {
			if (['failed', 'paused'].includes(item.state)) return item
			return { ...item, state: 'done' }
		}
		if (index > targetIndex) return { ...item, state: 'pending' }
		return item
	})
})


function flowStepState(index) {
	if (readySiteUrl.value && readySiteUrl.value.trim() !== '') return 'done'
	// 1. If an error occurred at the result stage, mark the step as failed
	if (resultFailed.value && flowSteps.value[index]?.key === 'result') return 'failed'

	if (hasReadySite.value && index <= currentStepIndex.value) return 'done'
	if (index < currentStepIndex.value) return 'done'
	if (index === currentStepIndex.value && progressActive.value) return 'active'
	if (index === currentStepIndex.value) return 'current'
	return 'pending'
}

function shouldAutoOpenSetupDialog() {
	return Boolean(
		step.value === 'setup' &&
		!setupDialogOpen.value &&
		!setupSchemaLoading.value &&
		setupFields.value.length &&
		!setupDefaultsComplete.value &&
		!setupDialogDismissed.value
	)
}

function maybeAutoOpenSetupDialog() {
	if (shouldAutoOpenSetupDialog()) setupDialogOpen.value = true
}

function dismissSetupDialog() {
	setupDialogDismissed.value = true
	setupDialogOpen.value = false
}


function progressResultFromSite(site, subscription = null) {
	if (!site) return null
	let provisioning = 'started'
	if (site.bootstrap_status === 'Failed' || /bootstrap app install failed/i.test(site.setup_error || '')) provisioning = 'bootstrap_failed'
	else if (site.provisioning_status === 'Failed' || site.site_status === 'Failed' || site.route_status === 'Failed' || site.setup_status === 'Failed') provisioning = 'failed'
	else if (site.oauth_status === 'Failed') provisioning = 'oauth_failed'
	else if (['Queued', 'Running'].includes(site.bootstrap_status)) provisioning = 'bootstrap_installing'
	else if (site.setup_status === 'Blocked') provisioning = 'setup_required'
	else if (site.route_status === 'Ready' && site.access_url && site.setup_status === 'Complete' && oauthConfiguredStatuses.has(site.oauth_status)) provisioning = 'ready'
	else if (site.route_status === 'Ready' && site.access_url && site.setup_status === 'Complete') provisioning = site.oauth_status === 'Running' ? 'oauth_configuring' : 'oauth_checking'
	else if (site.route_status === 'Ready' && site.access_url) provisioning = ['Required', 'Running'].includes(site.setup_status) ? 'setup_running' : 'setup_checking'
	else if (site.route_status === 'Pending' && (site.access_url || ['Provisioning', 'Ready', 'Active'].includes(site.site_status) || ['Running', 'Ready'].includes(site.provisioning_status))) provisioning = 'route_pending'
	else if (['Ready', 'Active'].includes(site.site_status) || site.provisioning_status === 'Ready') provisioning = 'route_pending'
	else if (['Pending', 'Not Started'].includes(site.provisioning_status) || ['Requested', 'Draft'].includes(site.site_status)) provisioning = 'paused'
	return {
		subscription: subscription?.name || site.subscription,
		status: subscription?.status,
		site: site.name,
		domain: site.domain,
		hostname: site.title,
		access_url: site.access_url,
		plan: site.plan || subscription?.plan,
		region: site.region || subscription?.region,
		site_status: site.site_status,
		provisioning_status: site.provisioning_status,
		route_status: site.route_status,
		tls_status: site.tls_status,
		setup_status: site.setup_status,
		setup_error: site.setup_error,
		oauth_status: site.oauth_status,
		oauth_error: site.oauth_error,
		bootstrap_status: site.bootstrap_status,
		provisioning,
		retry_available: ['paused', 'failed', 'bootstrap_failed', 'oauth_failed', 'started', 'route_pending', 'bootstrap_installing', 'setup_required', 'setup_checking', 'setup_running', 'oauth_checking', 'oauth_configuring'].includes(provisioning),
	}
}

function hydrateProgressFromRoute() {
	const siteName = route.query.site || route.query.progress
	const subscriptionName = route.query.subscription
	if (!siteName && !subscriptionName) return
	const site = existingSites.value.find((item) => item.name === siteName || item.subscription === subscriptionName)
	const subscription = context.value?.subscriptions?.find((item) => item.name === (subscriptionName || site?.subscription))
	const nextResult = progressResultFromSite(site, subscription)
	if (nextResult) {
		result.value = nextResult
		if (nextResult.plan) selectedPlan.value = nextResult.plan
		if (nextResult.region) form.region = nextResult.region
		step.value = 'result'
	}
}

function progressRouteFor(site, subscription) {
	return { path: '/customer/plans', query: { site: site?.name || site, subscription: subscription?.name || subscription } }
}

function planBadge(plan) {
	return plan.portal_badge || (plan.is_default ? 'Recommended' : plan.availability || 'Plan')
}

function priceLabel(plan) {
	if (plan.is_free) return '$0 / month'
	if (plan.cta_mode === 'request_access') return 'Request access'
	if (!Number(plan.monthly_price)) return 'Custom pricing'
	return `$${Number(plan.monthly_price).toLocaleString('en-IN')} / month`
}

function planCtaLabel(plan) {
	if (!plan) return 'Choose Plan'
	if (!canCreateSubscription.value) return 'Ask Admin'
	if (planDisabled(plan)) return 'Limit reached'
	if (plan.cta_mode === 'self_service') return 'Start Free Plan'
	if (plan.cta_mode === 'request_access') return 'Request access'
	return 'Coming soon'
}

function planDisabled(plan) {
	return Boolean(!canCreateSubscription.value || plan?.cta_disabled || plan?.entitlement?.exhausted)
}

function planDisabledReason(plan) {
	if (!canCreateSubscription.value) return 'Your LensCloud role can browse Plans, but cannot create subscriptions. Ask a Customer admin to start a subscription.'
	return plan?.cta_disabled_reason || plan?.entitlement?.reason || 'Your current entitlement for this Plan is already used.'
}

function featureIconLabel(icon) {
    const icons = {
        rocket: Rocket,
        clock: Clock,
        'shield-check': ShieldCheck,
        'credit-card': CreditCard,
        globe: Globe,
        shield: Shield,
        sparkles: Sparkles,
        layers: Layers,
        users: Users,
        'life-buoy': LifeBuoy,
        workflow: Workflow,
        'check-circle': CircleCheckBig,
        building: Building,
    }

    return icons[icon] || CircleCheckBig
}
function planPlacement(plan) {
	return plan?.privacy === 'Public' ? 'public' : 'private'
}

function placementLabel(value) {
	if (value === 'public') return 'Public'
	if (value === 'private') return 'Private'
	return 'All'
}

function setPlacementFilter(value) {
	placementFilter.value = value
	const nextPlans = plans.value.filter((plan) => value === 'all' || planPlacement(plan) === value)
	if (!nextPlans.some((plan) => plan.name === selectedPlan.value)) {
		selectedPlan.value = nextPlans.find((plan) => plan.is_default && !planDisabled(plan))?.name || nextPlans.find((plan) => !planDisabled(plan))?.name || nextPlans[0]?.name || ''
	}
}

function selectPlan(plan) {
	selectedPlan.value = plan.name
	// posthog analytics
	posthog.capture('plan_selected', {
    plan: plan.name,
    plan_title: plan.title,
    is_free: plan.is_free,
    placement: plan.privacy,
  })
}

async function continueFromPlan() {
	if (membershipPending.value || !canCreateSubscription.value || !selectedPlanRecord.value || planDisabled(selectedPlanRecord.value)) return

	posthog.capture('plan_continue_clicked', {
        plan: selectedPlanRecord.value.name,
    })

	if (selectedPlanRecord.value.cta_mode === 'self_service') {
		step.value = 'setup'
		setupDialogDismissed.value = false
		await loadSetupSchema()
		// maybeAutoOpenSetupDialog() //commented because it open even before giving site name
		return
	}
	if (selectedPlanRecord.value.cta_mode === 'request_access') requestAccess(selectedPlanRecord.value)
}

function applySetupDefaults(defaults, { overwriteDependents = false } = {}) {
	const dependentFields = new Set(['timezone', 'currency', 'chart_of_accounts', 'fiscal_year_start_date'])
	for (const [key, value] of Object.entries(defaults || {})) {
		if (overwriteDependents && dependentFields.has(key)) form.setup_defaults[key] = value || ''
		else if (!form.setup_defaults[key]) form.setup_defaults[key] = value
	}
}

async function loadSetupSchema(country = form.setup_defaults.country, options = {}) {
	if (!selectedPlanRecord.value?.name) return
	setupSchemaLoading.value = true
	try {
		const response = await callMethod('lenscloud.api.orchestration.get_customer_site_setup_schema', { plan: selectedPlanRecord.value.name, country })
		setupSchemaState.value = response.message || response
		applySetupDefaults(setupSchemaState.value?.defaults, options)
	} catch (err) {
		error.value = err?.message || 'Unable to load setup defaults.'
	} finally {
		setupSchemaLoading.value = false
	}
}

async function openSetupDialog() {
	setupDialogDismissed.value = false
	await loadSetupSchema()
	setupDialogOpen.value = true
}

async function refreshSetupDependents() {
	await loadSetupSchema(form.setup_defaults.country, { overwriteDependents: true })
}

async function saveSetupDefaults() {
	if (!setupDefaultsComplete.value) return
	if (result.value?.site && resultSetupRequired.value) {
		submitting.value = true
		error.value = ''
		try {
			const response = await callMethod('lenscloud.api.orchestration.update_customer_site_setup_defaults', { site: result.value.site, setup_data: form.setup_defaults }, 'POST')
			result.value = response.message || response
			setupDialogDismissed.value = true
			setupDialogOpen.value = false
			await refreshProgress()
		} catch (err) {
			error.value = err?.message || 'Unable to save setup defaults.'
		} finally {
			submitting.value = false
		}
		return
	}
	setupDialogDismissed.value = true
	setupDialogOpen.value = false
}

async function goToCheckout() {
	if (!setupDefaultsComplete.value) {
		await openSetupDialog()
		return
	}

	posthog.capture('setup_completed', {
        region: form.region,
    })

	if (setupComplete.value) step.value = 'checkout'
}

async function load() {
	loading.value = true
	error.value = ''
	try {
		const response = await callMethod('lenscloud.api.orchestration.get_customer_portal_context')
		context.value = response.message || response
		if (!selectedPlan.value) selectedPlan.value = context.value.plans?.find((plan) => plan.is_free && !planDisabled(plan))?.name || context.value.plans?.find((plan) => !planDisabled(plan))?.name || context.value.plans?.[0]?.name || ''
		if (!form.region) form.region = context.value.customer?.region || context.value.regions?.find((item) => !item.is_group)?.name || ''
		hydrateProgressFromRoute()
	} catch (err) {
		error.value = err?.message || 'Unable to load Plans.'
	} finally {
		loading.value = false
	}
}


function applyCanonicalProgress(snapshot) {
	if (!snapshot?.site || (result.value?.site && snapshot.site !== result.value.site)) return
	updateDisplayedStage(snapshot)
	canonicalProgress.value = snapshot
	result.value = { ...(result.value || {}), site: snapshot.site, canonical_progress: snapshot }
	// Trigger issue creation directly on failure/blocked state
	if (['failed', 'blocked', 'bootstrap_failed', 'oauth_failed'].includes(snapshot.stage_status)) {
		autoCreateIssueOnFailure()
	} else if (snapshot.can_continue) {
		scheduleAdvance()
	}
}

async function refreshProgress({ silent = false } = {}) {
	if (!result.value?.site || polling.value) return
	polling.value = true
	if (!silent) error.value = ''
	try {
		const response = await callMethod('lenscloud.api.provisioning_progress.get_customer_site_progress', { site: result.value.site })
		applyCanonicalProgress(response.message || response)
	} catch (err) {
		if (!silent) error.value = err?.message || 'Unable to refresh setup progress.'
	} finally {
		polling.value = false
	}
}

async function advanceProgress({ force = false } = {}) {
	if (!result.value?.site || advancing.value || resultReady.value || resultFailed.value) return
	advancing.value = true
	try {
		const response = await callMethod('lenscloud.api.provisioning_progress.advance_customer_site_provisioning', { site: result.value.site, force }, 'POST')
		applyCanonicalProgress(response.message || response)
	} catch (err) {
		error.value = err?.message || 'Unable to continue Site provisioning.'
	} finally {
		advancing.value = false
		if (canonicalProgress.value?.can_continue) scheduleAdvance()
	}
}

function scheduleAdvance(delay = 1500) {
	if (advanceTimer || advancing.value || !canonicalProgress.value?.can_continue) return
	advanceTimer = setTimeout(async () => {
		advanceTimer = null
		await advanceProgress()
	}, delay)
}

function stopProgressPolling() {
	if (progressPoller) clearInterval(progressPoller)
	progressPoller = null
	if (advanceTimer) clearTimeout(advanceTimer)
	advanceTimer = null
}

function startProgressPolling() {
	stopProgressPolling()
	if (!progressActive.value) return
	progressPoller = setInterval(() => refreshProgress({ silent: true }), 30000)
}

function onSiteProgress(snapshot) {
	applyCanonicalProgress(snapshot)
}

async function startFreePlan() {
	if (membershipPending.value || !canCreateSubscription.value || !canStartFree.value) return

	posthog.capture('subscription_creation_started', {
        plan: selectedPlanRecord.value.name,
        region: form.region,
    })

	submitting.value = true
	error.value = ''
	try {
		const response = await callMethod('lenscloud.api.orchestration.request_customer_subscription', {
			plan: selectedPlanRecord.value.name,
			region: form.region,
			site_name: form.site_name,
			company_name: form.setup_defaults.company_name || form.company_name || form.site_name,
			subdomain: normalizedSubdomain.value,
			notes: form.notes,
			setup_data: form.setup_defaults,
		}, 'POST')
		result.value = response.message || response

		posthog.capture('subscription_creation_success', {
			subscription: result.value.subscription,
			site: result.value.site,
		})

		step.value = 'result'
		if (result.value?.site) await router.replace(progressRouteFor(result.value.site, result.value.subscription))
		await load()
		await refreshProgress({ silent: true })
		startProgressPolling()
		scheduleAdvance(0)
	} catch (err) {
		error.value = err?.message || 'Unable to start the Free Plan.'

		posthog.capture('subscription_creation_failed', {
        error: err.message,
    	})

	} finally {
		submitting.value = false
	}
}

async function requestAccess(plan) {
	if (membershipPending.value || !canCreateSubscription.value || !plan || planDisabled(plan) || !form.region) return

	posthog.capture('plan_access_requested', {
        plan: plan.name,
    })

	submitting.value = true
	error.value = ''
	try {
		const response = await callMethod('lenscloud.api.orchestration.request_customer_subscription', { plan: plan.name, region: form.region }, 'POST')
		result.value = response.message || response
		step.value = 'result'
		if (result.value?.site) await router.replace(progressRouteFor(result.value.site, result.value.subscription))
		await load()
		startProgressPolling()
	} catch (err) {
		error.value = err?.message || 'Unable to request access.'
	} finally {
		submitting.value = false
	}
}

async function retrySetup() {
	if (!result.value?.site) return
	error.value = ''
	await advanceProgress({ force: true })
	startProgressPolling()
}

// commented out to stop the modal from opening befor giveing site details
// watch([step, setupFields, setupDefaultsComplete, setupSchemaLoading], maybeAutoOpenSetupDialog, { flush: 'post' })

onMounted(async () => {
	socket?.on('lenscloud_site_progress', onSiteProgress)
	await load()
	if (result.value?.site) await refreshProgress({ silent: true })
	startProgressPolling()
	scheduleAdvance(0)
	posthog.capture('plans_viewed')
})
onBeforeUnmount(() => {
	socket?.off('lenscloud_site_progress', onSiteProgress)
	stopProgressPolling()
})

const issueCreated = ref(false)
const createdIssueName = ref('')

async function autoCreateIssueOnFailure() {
	if (issueCreated.value || !result.value?.site) return
	const siteName = result.value?.site
    if (!siteName) return
	const progress = canonicalProgress.value || {}
	try {
		issueCreated.value = true
		const response = await callMethod('lenscloud.api.issue.create_orchestration_issue', {
			site: result.value.site,
			subscription: result.value.subscription,
			orchestration_action_log: progress.orchestration_action_log || null,
			summary: progress.message || "Failed at Provisioning",
			message_params_json: progress.customer_message || 'Provisioning failed.'
		}, 'POST')
		
		// Capture created issue ID
		createdIssueName.value = response.message?.issue || response.issue || ''

	} catch (err) {
		console.error('Failed to auto-create issue:', err)
		issueCreated.value = false
	}
}

const STAGES = [
  'requested',
  'runtime_reconciling',
  'route_pending',
  'bootstrap_installing',
  'setup_verifying',
  'setup_completing',
  'oauth_configuring',
  'oauth_verifying',
  'ready',
]

const STAGE_GRAPH = {
  requested: ['runtime_reconciling'],

  runtime_reconciling: ['route_pending'],

  route_pending: ['bootstrap_installing'],

  bootstrap_installing: [
    'setup_verifying',
    'failed',
    'blocked_platform_action',
  ],

  setup_verifying: [
    'setup_completing',
    'blocked_customer_input',
    'failed',
  ],

  setup_completing: [
    'oauth_configuring',
    'failed',
  ],

  oauth_configuring: [
    'oauth_verifying',
    'failed',
  ],

  oauth_verifying: [
    'ready',
    'failed',
  ],

  ready: [],
}

function canTransition(from, to) {
    if (!from) return true
    if (from === to) return true

    return STAGE_GRAPH[from]?.includes(to) ?? false
}

const currentStage = ref(null)

function updateDisplayedStage(snapshot) {
    const next = snapshot.stage

    if (canTransition(currentStage.value, next)) {
        currentStage.value = next
    } else {
        console.warn(
            `[Realtime] Ignored transition ${currentStage.value} -> ${next}`
        )
    }
}



</script>

<template>
	<WorkspaceLayout
		title="Plans"
		subtitle="From choice of plans to free checkout, Launch your workspace with a guided approach"
		inspector-kicker="Guided Launch"
		inspector-title="Launch checklist"
		:inspector-subtitle="screenSubtitle"
	>
		<template #main>
			<div class="h-full overflow-y-auto bg-[#f7f9fb] p-4 lg:p-6">
				<!-- <Alert v-if="error" theme="red" title="Plan action failed" :description="error" class="mb-4" /> -->
				 <!-- NEW: Auto-Created Support Issue Alert -->
				 <Alert 
					v-if="createdIssueName" 
					theme="blue" 
					title="Support Ticket has been Created" 
					class="mb-4"
					>
					<template #description>
						<p class="text-ink-gray-6 prose-sm">
						A support issue (<strong>{{ createdIssueName }}</strong>) has been logged. 
						For More Details look into 
						<RouterLink to="/customer/support-tickets" class="font-semibold underline text-ink-blue-3 hover:text-blue-800">
							Support
						</RouterLink>.
						</p>
					</template>
				</Alert>

		<div v-if="setupDialogOpen" class="fixed inset-0 z-[1000] grid place-items-center bg-black/30 px-4 py-6" role="presentation" @mousedown.self="dismissSetupDialog">
			<form class="w-full max-w-2xl rounded-xl bg-white p-6 shadow-xl" @submit.prevent="saveSetupDefaults">
				<div class="flex items-start justify-between gap-4">
					<div>
						<h3 class="text-lg font-semibold text-gray-900">Setup defaults</h3>
						<p class="mt-1 text-sm text-gray-500">Required fields come from the target app setup contract.</p>
					</div>
					<button class="rounded-md p-2 text-gray-500 hover:bg-gray-100" type="button" aria-label="Close" @click="dismissSetupDialog"><XCircle class="size-5" /></button>
				</div>
				<div v-if="setupSchemaLoading" class="mt-6 rounded-lg bg-gray-50 p-4 text-sm text-gray-600">Loading setup fields...</div>
				<div v-else class="mt-6 grid gap-4 sm:grid-cols-2">
					<label v-for="field in setupFields" :key="field.name" class="block text-sm font-medium text-gray-700">
						<span>{{ field.label }} <span v-if="field.required" class="text-red-600">*</span></span>
						<select v-if="field.fieldtype === 'Select'" v-model="form.setup_defaults[field.name]" class="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500" :required="field.required" @change="field.name === 'country' && refreshSetupDependents()">
							<option value="">Select</option>
							<option v-for="option in field.options || []" :key="option.value || option" :value="option.value || option">{{ option.label || option.value || option }}</option>
						</select>
						<input v-else v-model="form.setup_defaults[field.name]" class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500" :required="field.required" :type="field.fieldtype === 'Date' ? 'date' : 'text'" />
					</label>
				</div>
				<div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
					<Button variant="subtle" type="button" @click="dismissSetupDialog">Back</Button>
					<Button variant="solid" type="submit" :disabled="!setupDefaultsComplete || submitting">{{ submitting ? 'Saving...' : 'Save defaults' }}</Button>
				</div>
			</form>
		</div>

				<div v-if="loading" class="grid min-h-[560px] place-items-center rounded-xl border border-outline-gray-2 bg-surface-white p-8 text-center">
					<div>
						<div class="mx-auto grid size-12 place-items-center rounded-full bg-blue-50 text-blue-700"><Sparkles class="size-6" /></div>
						<p class="mt-4 text-sm font-medium text-ink-gray-8">Loading your launch activity...</p>
					</div>
				</div>

				<Alert v-else-if="!canReadPlans" theme="amber" title="Plans need access" description="Your current LensCloud role does not include read access to Plans. Ask a Customer admin or Platform operator to update your Role Profile if you should compare Plans." />
				<Alert v-else-if="membershipPending" theme="amber" title="Your account is waiting for approval" description="Your email domain is already connected to a LensCloud Customer. A Customer admin or Platform operator needs to approve your access before you can start a subscription." />
				<Alert v-if="!loading && !membershipPending && canReadPlans && !canCreateSubscription" theme="amber" title="Subscription creation needs an admin" description="Your current LensCloud role can browse Plans, but it cannot create subscriptions. Ask a Customer admin to start or approve the subscription for this Customer." class="mb-4" />

				<section v-if="!loading && !membershipPending && canReadPlans" class="mx-auto max-w-6xl">
					<div class="rounded-2xl border border-outline-gray-2 bg-surface-white">
						<div class="p-5 lg:p-6">
							<div v-if="step === 'choose'" class="space-y-6">
								<div class="mx-auto max-w-3xl text-center">
									<!-- <p class="text-xs font-semibold text-[#64748B]">Choose Plan</p> -->
									<h3 class="mt-2 text-2xl font-semibold text-[#191c1e]">Free Today and Upgrade Later</h3>
									<p class="mt-3 text-sm leading-6 text-[#505f76]">Pick a Platform Plan. Start free today or request access to higher tiers.</p>
									<div class="mt-5 inline-flex rounded-lg border border-[#EDEDED] bg-[#f2f4f6] p-1">
										<button v-for="option in ['all', 'public', 'private']" :key="option" class="rounded-md px-4 py-2 text-sm font-semibold transition" :class="placementFilter === option ? 'bg-white text-primary shadow-sm' : 'text-[#64748B] hover:text-[#191c1e]'" @click="setPlacementFilter(option)">{{ placementLabel(option) }}</button>
									</div>
								</div>

								<div v-if="!visiblePlans.length" class="rounded-xl border border-dashed border-[#EDEDED] bg-[#f7f9fb] p-8 text-center">
									<p class="text-base font-semibold text-[#191c1e]">No Plans match this selection</p>
									<p class="mt-2 text-sm text-[#64748B]">Choose another placement filter or ask LensCloud support.</p>
								</div>

								<div v-else class="grid items-stretch gap-4 lg:grid-cols-3">
									<article v-for="plan in visiblePlans" :key="plan.name" :aria-disabled="planDisabled(plan)" class="relative flex min-h-[430px] flex-col rounded-2xl border p-5 transition" :class="[plan.is_default ? 'order-first lg:order-none' : '', planDisabled(plan) ? 'cursor-not-allowed border-[#EDEDED] bg-[#f2f4f6] opacity-70' : selectedPlanRecord?.name === plan.name ? 'cursor-pointer border-primary bg-white shadow-[0_12px_30px_rgba(29,78,216,0.12)] hover:-translate-y-0.5' : plan.is_default ? 'cursor-pointer border-primary bg-white hover:-translate-y-0.5' : 'cursor-pointer border-[#EDEDED] bg-[#f2f4f6] hover:-translate-y-0.5']" @click="!planDisabled(plan) && selectPlan(plan)">
										<div v-if="plan.is_default" class="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-white shadow-sm">Recommended</div>
										<div class="flex items-start justify-between gap-3">
											<div>
												<p class="text-lg font-semibold text-[#191c1e]">{{ plan.title }}</p>
												<p class="mt-1 text-sm text-[#64748B]">{{ priceLabel(plan) }}</p>
											</div>
											<Badge :class="plan.is_default ? 'bg-[#dce1ff] text-[#0039b5]' : plan.experimental ? 'bg-amber-50 text-amber-700' : 'bg-white text-[#505f76]'">{{ planBadge(plan) }}</Badge>
										</div>

										<p class="mt-4 min-h-12 text-sm leading-6 text-[#505f76]">{{ plan.description || plan.customer_summary }}</p>
										<div v-if="planDisabled(plan)" class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">{{ planDisabledReason(plan) }}. Manage progress from Subscriptions.</div>

										<!-- First UL: Highlights -->
										<div v-if="plan.features?.highlights?.length" class="mt-5 flex flex-wrap gap-2">
											<div 
											v-for="item in plan.features.highlights" 
											:key="item.highlight"
											class="inline-flex items-center gap-1.5 rounded-md bg-indigo-50 border border-indigo-200/60 px-2.5 py-1 text-xs font-semibold text-indigo-900"
											>
											<span>
												<component :is="featureIconLabel(item.icon)" class="w-4 h-4 text-secondary" />
											</span>
											<span>{{ item.highlight }}</span>
											</div>
										</div>

										<!-- Second UL: Features -->
										<hr class="my-5 border-gray-100" />

										<!-- Features Section -->
										<div class="flex-1">
											<p class="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Includes</p>
											<ul class="space-y-3">
											<li 
												v-for="item in (plan.features?.features || []).slice(0, 5)" 
												:key="item.feature" 
												class="flex items-start gap-2.5 text-sm text-gray-600"
											>
												<!-- Consistent Check Icon or Dynamic Emoji -->
												<span class="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-indigo-700"
												:class="selectedPlanRecord?.name === plan.name ? 'bg-[#EDEDED]' : 'border border-[#EDEDED]'">
													<component :is="featureIconLabel(item.icon)" class="w-3 h-3 text-gray-600" />
												</span>
												<span class="leading-tight">{{ item.feature }}</span>
											</li>
											</ul>
										</div>
										<button class="mt-6 inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2" :disabled="planDisabled(plan)" :class="selectedPlanRecord?.name === plan.name && !planDisabled(plan) ? 'bg-primary text-white hover:bg-primary' : 'border border-[#EDEDED] bg-white text-[#505f76] hover:bg-white'" @click.stop="selectedPlanRecord?.name === plan.name ? continueFromPlan() : selectPlan(plan)"
										@click="
											posthog.capture('plan_selected', {
												plan: plan.name,
												billing_cycle
											});
											selectPlan(plan);
    ">
											{{ selectedPlanRecord?.name === plan.name ? planCtaLabel(plan) : 'Choose Plan' }}
											<Send v-if="selectedPlanRecord?.name === plan.name && plan.cta_mode === 'request_access'" class="size-4" />
											<CheckCircle2 v-else-if="selectedPlanRecord?.name === plan.name" class="size-4" />
										</button>
									</article>
								</div>
							</div>

							<div v-else-if="step === 'setup'" class="flex items-start justify-center p-0 md:p-6 lg:p-10">
								<div class="w-full max-w-3xl overflow-hidden rounded-xl border border-gray-200 bg-white shadow-md" data-purpose="setup-card">
									<div class="border-b border-gray-100 p-8">
										<h3 class="text-2xl font-bold text-gray-900">Setup Your Workspace</h3>
										<p class="mt-1 text-sm text-gray-500">Step 3: Region &amp; Domain</p>
									</div>

									<div class="space-y-12 p-8 md:p-10">
										<section data-purpose="region-selection">
											<h4 class="mb-1 text-base font-semibold text-gray-900">1. Choose Region</h4>
											<p class="mb-4 text-sm text-gray-500">Select the geographic region for your Workspace's data hosting. This cannot be changed later.</p>
											<div class="relative w-full sm:w-80">
												<select v-model="form.region" aria-label="Region" class="block w-full rounded-md border border-gray-300 bg-white py-2 pl-3 pr-10 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500">
													<option v-for="region in selectableRegions" :key="region.name" :value="region.name">{{ region.title || region.name }}</option>
												</select>
											</div>
										</section>

										<section data-purpose="site-address">
											<h4 class="mb-1 text-base font-semibold text-gray-900">2. Your Workspace Address</h4>
											<p class="mb-4 text-sm text-gray-500">Create a unique subdomain for your Workspace. It will end in {{ domainSuffix }}.</p>
											<div class="flex flex-wrap items-center gap-4">
												<div class="flex rounded-md shadow-sm">
													<span class="inline-flex items-center rounded-l-md border border-r-0 border-gray-300 bg-gray-50 px-4 text-sm font-medium text-gray-600">https://</span>
													<input v-model="form.subdomain" aria-label="Subdomain" class="block w-full min-w-0 flex-1 border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-blue-500 sm:w-48" name="subdomain" placeholder="my-subdomain" type="text" />
													<span class="inline-flex items-center rounded-r-md border border-l-0 border-gray-300 bg-gray-50 px-4 text-sm font-medium text-gray-600">{{ domainSuffix }}</span>
												</div>
												<div class="flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-medium" :class="normalizedSubdomain ? 'border-green-200 bg-green-100 text-green-700' : 'border-gray-200 bg-gray-100 text-gray-500'">
													<CheckCircle2 class="size-4" />
													{{ normalizedSubdomain ? 'Available' : 'Required' }}
												</div>
											</div>
										</section>

										<section data-purpose="workspace-setup">
											<h4 class="mb-1 text-base font-semibold text-gray-900">3. Workspace & Defaults Configuration</h4>
											<p class="mb-4 text-sm text-gray-500">Provide a friendly name for internal reference and configure required Workspace defaults.</p>
											
											<div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
												<!-- WORKSPACE NAME INPUT -->
												<div>
													<input 
														v-model="form.site_name" 
														aria-label="Workspace Name" 
														class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500" 
														type="text" 
														placeholder="My Awesome App" 
													/>
												</div>

												<!-- SETUP DEFAULTS ACTION -->
												<div>
													<div class="flex flex-wrap items-center gap-3">
														<button 
															class="rounded-md border border-gray-50 bg-secondary px-4 py-2 text-sm font-semibold text-white hover:bg-primary transition" 
															type="button" 
															@click="openSetupDialog"
														>
															{{ setupDefaultsComplete ? 'Edit setup defaults' : 'Continue Setup' }}
														</button>
														<span 
															class="rounded-full px-3 py-1 text-sm font-medium" 
															:class="setupDefaultsComplete ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-800'"
														>
															{{ setupDefaultsComplete ? 'Ready' : setupSchemaLoading ? 'Loading' : 'Required' }}
														</span>
													</div>
												</div>
											</div>
										</section>
									</div>

									<div class="flex flex-col items-center justify-between gap-4 bg-gray-50 px-8 py-6 sm:flex-row">
										<button class="w-full rounded-md border border-gray-300 bg-white px-16 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 sm:w-auto" @click="step = 'choose'">Back</button>
										<button class="w-full rounded-md border border-transparent bg-secondary px-16 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto" :disabled="!setupComplete" @click="goToCheckout">Continue to Review</button>
									</div>
								</div>
							</div>

							<div v-else-if="step === 'checkout'" class="bg-white p-4 md:p-8 lg:p-10">
								<h3 class="mb-8 text-3xl font-bold text-[#1a1a1a]">Review Subscription</h3>
								<div class="grid max-w-full grid-cols-1 gap-6 lg:grid-cols-2">
									<section class="h-fit rounded-xl border border-gray-200 bg-white p-8" data-purpose="order-summary">
										<h4 class="mb-6 text-xl font-bold text-[#1a1a1a]">Order summary</h4>
										<hr class="mb-6 border-gray-100" />
										<div class="space-y-6">
											<div class="flex items-center gap-4">
												<div class="flex size-12 shrink-0 items-center justify-center rounded-lg bg-gray-100"><Sparkles class="size-6 text-gray-600" /></div>
												<div><p class="font-bold text-gray-800">{{ selectedPlanRecord?.title || 'Free Plan' }}</p><p class="text-xs text-gray-400">{{ selectedPlanRecord?.description || 'Start with Free Plan' }}</p></div>
											</div>

											<div class="flex items-center gap-4">
												<div class="flex size-12 shrink-0 items-center justify-center rounded-lg bg-gray-100"><Globe2 class="size-6 text-gray-600" /></div>
												<div><p class="font-bold text-gray-800">Region: {{ selectedRegion?.title || selectedRegion?.name }}</p><p class="text-xs text-gray-400">Region <span class="font-mono">{{ selectedRegion?.name }}</span>: {{ selectedRegion?.title || selectedRegion?.name }}</p></div>
											</div>

											<div class="flex items-center gap-4">
												<div class="flex size-12 shrink-0 items-center justify-center rounded-lg bg-gray-100"><ExternalLink class="size-6 text-gray-600" /></div>
												<div><p class="break-all font-bold text-gray-800">Subdomain: {{ hostnamePreview }}</p><p class="break-all text-xs text-gray-400">Subdomain: {{ hostnamePreview }}</p></div>
											</div>
										</div>
									</section>

									<section class="flex h-fit flex-col rounded-xl border border-gray-200 bg-white" data-purpose="price-breakdown">
										<div class="p-8">
											<h4 class="mb-6 text-xl font-bold text-[#1a1a1a]">Price breakdown</h4>
											<div class="mb-8 space-y-4">
												<div class="flex items-center justify-between text-gray-600"><span class="text-lg">Plan price</span><span class="text-lg font-medium text-black">$0</span></div>
												<div class="flex items-center justify-between text-gray-600"><span class="text-lg">Taxes</span><span class="text-lg font-medium text-black">$0</span></div>
											</div>
											<hr class="mb-6 border-gray-100" />
											<div class="mb-8 flex items-center justify-between"><span class="text-xl font-bold">Total due today</span><span class="text-xl font-bold">$0</span></div>
										</div>
										<div class="border-y border-gray-200 bg-gray-50 p-6"><p class="text-sm text-gray-500">No payment method required for Free Plan</p></div>
										<div class="flex flex-col items-center gap-3 p-6">
											<button class="w-full rounded-lg bg-primary py-3.5 text-sm font-bold text-white transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50" :disabled="!canStartFree || submitting" @click="startFreePlan">{{ submitting ? 'Starting...' : 'Start Free Subscription' }}</button>
											<button class="w-full rounded-lg bg-gray-100 px-6 py-3.5 text-sm font-bold text-gray-700 transition-colors hover:bg-gray-200" @click="step = 'setup'">Back</button>
										</div>
									</section>
								</div>
							</div>

							<div v-else class="grid gap-5 xl:grid-cols-[1fr_340px]">
								<div class="rounded-xl border border-[#EDEDED] bg-white p-6">
									<Badge :class="resultFailed ? 'bg-red-50 text-red-700' : resultPaused ? 'bg-amber-50 text-amber-800' : resultStarted ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700'">{{ resultFailed ? 'Setup needs retry' : resultPaused ? 'Setup paused' : resultReady ? 'Ready' : resultStarted ? 'Provisioning' : 'Approval pending' }}</Badge>
									<h3 class="mt-3 text-xl font-semibold text-[#191c1e]">{{ resultFailed ? 'Workspace setup needs attention' : resultPaused ? 'Workspace setup is paused' : resultReady ? 'Your Workspace is ready to open' : resultStarted ? 'Setting up your Workspace' : 'Subscription request received' }}</h3>
									<p class="mt-2 text-sm leading-6 text-[#64748B]">{{ resultFailed ? (provisioningMode === 'oauth_failed' ? 'Platform sign-on did not complete. Retry after Platform readiness is restored, or contact support and we will continue from the Platform side.' : 'Setup did not complete. You can retry after Platform readiness is restored, or contact support and we will continue from the Platform side.') : resultPaused ? 'Your Subscription and Workspace reservation are saved. Live setup needs the controlled Platform apply window before it can create the actual Workspace.' : resultReady ? 'Secure access and Platform sign-on are verified. You can open the Workspace from here.' : resultStarted ? 'We are preparing your workspace. You can follow progress from here or refresh status without losing this view.' : 'The LensCloud team will review this request before setup starts.' }}</p>

									<div class="mt-8 space-y-0">
										<div v-for="(item, index) in provisioningSteps" :key="item.label" class="relative flex items-start pb-7 last:pb-0">
											<div v-if="index < provisioningSteps.length - 1" class="absolute left-[11px] top-6 h-full w-0.5" :class="item.state === 'done' ? 'bg-[#10B981]' : 'bg-[#eceef0]'"></div>
											<div class="z-10 grid size-6 shrink-0 place-items-center rounded-full" :class="item.state === 'done' ? 'bg-[#10B981] !text-white' : item.state === 'failed' ? 'bg-red-600 !text-white' : item.state === 'paused' ? 'bg-amber-100 text-amber-700 ring-2 ring-amber-200' : item.state === 'active' ? 'bg-blue-100 text-[#1D4ED8]' : 'border-2 border-[#c4c5d7] bg-[#f7f9fb] text-[#64748B]'">
												<Check v-if="item.state === 'done'" class="size-4" />
												<XCircle v-else-if="item.state === 'failed'" class="size-4" />
												<AlertTriangle v-else-if="item.state === 'paused'" class="size-4" />
												<RefreshCcw v-else-if="item.state === 'active'" class="size-4 animate-spin [animation-direction:reverse]" />
												<Clock3 v-else class="size-4" />
											</div>
											<div class="ml-4">
												<p class="text-sm font-semibold" :class="item.state === 'failed' ? 'text-red-700' : 'text-[#191c1e]'">{{ item.label }}</p>
												<p class="mt-1 text-xs leading-5 text-[#64748B]">{{ item.helper }}</p>
											</div>
										</div>
									</div>

									

									<!-- <div class="mt-6 flex flex-wrap gap-2">
										<Button :as="RouterLink" to="/customer/dashboard">View dashboard</Button>
										<Button v-if="result?.site" :as="RouterLink" :to="result?.subscription ? `/customer/subscriptions?subscription=${encodeURIComponent(result.subscription)}` : '/customer/subscriptions'" variant="subtle">View Subscription</Button>
										<Button v-if="readySiteUrl && hasReadySite" 
										as="a" :href="readySiteUrl" target="_blank" 
										@click="posthog.capture('site_opened', {
											site: result?.site,
											plan: result?.plan,
											region: result?.region,
										})"
										variant="subtle"><ExternalLink class="size-4" />Open Workspace</Button></div> -->
								</div> 
								<aside class="rounded-xl border border-[#EDEDED] bg-[#f7f9fb] p-5">
									<div class="grid size-10 place-items-center rounded-full bg-[#dce1ff] text-[#1D4ED8]">
										<ShieldCheck class="size-5" /></div>
										<h3 class="mt-4 text-base font-semibold text-[#191c1e]">What happens next</h3>
										<p class="mt-2 text-sm leading-6 text-[#64748B]">LensCloud keeps progress visible here and on the dashboard. If setup is delayed, support can continue from the Platform side without exposing infrastructure details.</p>
										<a class="mt-4 inline-flex items-center gap-2 rounded-lg border border-[#EDEDED] bg-white px-3 py-2 text-sm font-semibold text-[#505f76] hover:bg-white" href="mailto:hello@lmnas.com">
										<Headset class="size-4" />Contact support</a>

										<div v-if="resultStarted || resultPaused || resultFailed" class="mt-8 rounded-lg border border-[#EDEDED] bg-[#f2f4f6] p-5">
										<div class="flex flex-col items-start gap-4">
											<div class="flex items-start gap-3">
												<AlertTriangle class="mt-0.5 size-5 shrink-0 text-amber-700" />
												<p class="max-w-md text-sm leading-6 text-[#505f76]">{{ resultFailed ? 'Workspace setup took longer than expected. Our team can inspect the Platform evidence while you retry safely.' : resultPaused ? 'Your request is saved. Ask the Platform operator to open the controlled live apply window, then retry setup.' : 'LensCloud is checking setup progress automatically. You can refresh status now without leaving this page.' }}</p>
											</div>
											<div class="flex flex-col items-start gap-3 w-full">
												<!-- <a class="inline-flex items-center justify-center rounded-lg border border-[#EDEDED] bg-white px-4 py-2 text-sm font-bold text-[#505f76] hover:bg-[#f7f9fb]" href="mailto:support@lmnas.com">Contact Support</a> -->
												<button v-if="resultSetupRequired" class="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-bold text-white hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60" :disabled="submitting || polling" @click="openSetupDialog">Update defaults</button>
												<button v-else-if="resultRetryable" class="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-white hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60" :disabled="submitting || polling" @click="resultStarted ? refreshProgress() : retrySetup()">
													<RefreshCcw class="size-4" :class="submitting || polling ? 'animate-spin [animation-direction:reverse]' : ''" />
													{{ submitting || polling ? 'Checking...' : resultStarted ? 'Refresh status' : 'Retry Setup' }}</button>
												<a v-if="resultReady && hasReadySite" 
													:href="readySiteUrl.access_url" target="_blank" 
													class="bg-primary hover:bg-secondary text-white inline-flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold"
													@click="posthog.capture('site_opened', {
														site: result?.site,
														plan: result?.plan,
														region: result?.region,
													})"
													variant="subtle">
													
														<ExternalLink class="size-4" />
													
												Open Workspace</a>
											</div>
										</div>
									</div>
								</aside>
							</div>
						</div>
					</div>
				</section>
			</div>
		</template>

		<template #inspector>
			<div v-if="step === 'checkout'" class="space-y-4">
				<div class="rounded-xl border border-gray-200 bg-white p-6">
					<div class="flex items-start justify-between">
						<div><p class="text-[10px] font-semibold text-gray-400">Your service</p><h3 class="text-base font-bold text-gray-900">Checkout details</h3></div>
						<div class="text-gray-400"><Check class="size-5" /></div>
					</div>
					<div class="mt-6 space-y-4">
						<h4 class="text-sm font-bold text-gray-800">Your subscription is ready to start.</h4>
						<p class="text-xs leading-relaxed text-gray-500">The Free Plan is self-provisioned and does not require a payment method. You can upgrade later for more capacity.</p>
					</div>
				</div>
			</div>
			<div v-else class="space-y-4">
				<div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
					<p class="text-sm font-semibold text-ink-gray-9">Launch Progress</p>
					<div class="mt-4 space-y-3">
						<div v-for="(item, index) in flowSteps" :key="item.key" class="flex gap-3">
							<div class="flex size-7 shrink-0 items-center justify-center rounded-full leading-none" 
							:class="{
								'text-green-600': flowStepState(index) === 'done',
								'text-secondary': ['active', 'current'].includes(flowStepState(index)),
								'text-red-600' : flowStepState(index) === 'failed',
								'bg-surface-gray-2 text-ink-gray-5': flowStepState(index) === 'pending'
							}">
  								<CheckCircle2 v-if="flowStepState(index) === 'done'" class="size-6" />
								<RefreshCcw v-else-if="flowStepState(index) === 'active'" class="size-6 animate-spin [animation-direction:reverse]" />
								<XCircle v-else-if="flowStepState(index) === 'failed'" class="size-6" />
								<Clock3 v-else class="size-6" />
							</div>
							<div>
								<p class="text-sm font-medium text-ink-gray-9">{{ item.label }}</p>
								<p class="text-xs leading-5 text-ink-gray-5 mt-1">{{ item.helper }}</p>
							</div>
						</div>
					</div>
				</div>
				<!-- <div class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-3">
					<p class="text-sm font-medium text-ink-gray-9">Current selection</p>
					<div class="mt-2 space-y-2 text-sm text-ink-gray-5"><p>Plan: {{ plans.find((plan) => plan.name === result?.plan)?.title || selectedPlanRecord?.title || result?.plan || 'Required' }}</p><p>Region: {{ result?.region || selectedRegion?.title || selectedRegion?.name || 'Required' }}</p><p class="truncate">Site: {{ selectedSiteLabel || 'Required' }}</p></div>
				</div> -->
				<div class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-4">
					<p class="mb-3 text-sm font-semibold text-ink-gray-9">Current Selection</p>

					<div class="space-y-3">
						<div class="flex items-start justify-between gap-4">
							<span class="text-sm text-ink-gray-5">Plan</span>
							<span class="text-right text-sm font-medium text-ink-gray-9">
								{{ plans.find((plan) => plan.name === result?.plan)?.title || selectedPlanRecord?.title || result?.plan || 'Required' }}
							</span>
						</div>

						<div class="flex items-start justify-between gap-4">
							<span class="text-sm text-ink-gray-5">Region</span>
							<span class="text-right text-sm font-medium text-ink-gray-9">
								{{ result?.region || selectedRegion?.title || selectedRegion?.name || 'Required' }}
							</span>
						</div>

						<div class="flex items-start justify-between gap-4">
							<span class="text-sm text-ink-gray-5">Workspace</span>
							<span class="max-w-[60%] truncate text-right text-sm font-medium text-ink-gray-9">
								{{ selectedSiteLabel || 'Required' }}
							</span>
						</div>
					</div>
				</div>
			</div>
		</template>

	</WorkspaceLayout>
</template>
