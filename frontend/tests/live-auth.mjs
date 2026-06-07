import { chromium } from 'playwright'
import { readFileSync } from 'node:fs'

const baseURL = process.env.LENSCLOUD_BASE_URL || 'http://dev.localhost:8000'
const contextOptions = process.env.LENSCLOUD_VIEWPORT === 'mobile'
	? { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }
	: { viewport: { width: 1440, height: 900 } }
const credentials = process.env.LENSCLOUD_CREDENTIAL_FILE
	? JSON.parse(readFileSync(process.env.LENSCLOUD_CREDENTIAL_FILE, 'utf8'))
	: process.env

async function login(page, user, password) {
	await page.goto(`${baseURL}/login`)
	await page.locator('#login_email').fill(user)
	await page.locator('#login_password').fill(password)
	await page.locator('button.btn-login').click()
	await page.waitForFunction(() => !window.location.pathname.startsWith('/login'))
}

async function assertPage(page, path, heading) {
	const errors = []
	page.on('pageerror', (error) => errors.push(error.message))
	page.on('console', (message) => {
		if (message.type() === 'error') errors.push(message.text())
	})
	await page.goto(`${baseURL}${path}`)
	await page.getByRole('heading', { name: heading, exact: true }).waitFor()
	if (errors.some((message) => /403|forbidden|not permitted/i.test(message))) {
		throw new Error(`Permission error on ${path}: ${errors.join('; ')}`)
	}
}

const browser = await chromium.launch({ headless: true })
try {
	const platform = await browser.newContext(contextOptions)
	const platformPage = await platform.newPage()
	await login(
		platformPage,
		credentials.platform_user || credentials.LENSCLOUD_PLATFORM_USER,
		credentials.platform_password || credentials.LENSCLOUD_PLATFORM_PASSWORD,
	)
	await assertPage(platformPage, '/lenscloud/platform/dashboard', 'Dashboard')
	await platform.close()

	const customer = await browser.newContext(contextOptions)
	const customerPage = await customer.newPage()
	await login(
		customerPage,
		credentials.customer_user || credentials.LENSCLOUD_CUSTOMER_USER,
		credentials.customer_password || credentials.LENSCLOUD_CUSTOMER_PASSWORD,
	)
	await assertPage(customerPage, '/lenscloud/customer/create-site', 'Create Site')
	await customerPage.getByText('Free Plan', { exact: false }).first().waitFor()
	if (process.env.LENSCLOUD_SUBMIT_SITE === '1') {
		await customerPage.getByLabel('Site name').fill('Playwright acceptance')
		await customerPage.getByLabel('Company or project').fill('LensCloud Acceptance')
		await customerPage.getByLabel('Preferred subdomain').fill(process.env.LENSCLOUD_TEST_SUBDOMAIN)
		const submit = customerPage.getByRole('button', { name: 'Submit site request' })
		if (await submit.isDisabled()) {
			const diagnostic = {
				site: await customerPage.getByLabel('Site name').inputValue(),
				company: await customerPage.getByLabel('Company or project').inputValue(),
				subdomain: await customerPage.getByLabel('Preferred subdomain').inputValue(),
				alerts: await customerPage.locator('[role="alert"]').allTextContents(),
				review: await customerPage.getByRole('heading', { name: 'Review' }).locator('..').innerText(),
			}
			throw new Error('Create Site form incomplete: ' + JSON.stringify(diagnostic))
		}
		await submit.click()
		await customerPage.getByText('Site request captured', { exact: true }).waitFor()
	}
	await customer.close()

	console.log('Authenticated LensCloud Playwright smoke passed.')
} finally {
	await browser.close()
}
