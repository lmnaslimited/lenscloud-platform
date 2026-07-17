import frappeUIPreset from 'frappe-ui/tailwind'

export default {
	presets: [frappeUIPreset],
	content: [
		'./index.html',
		'./src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
		'../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
		'../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
	],
	safelist: [{ pattern: /!(text|bg)-/, variants: ['hover', 'active'] }],
	theme: {
		extend: {
			colors: {
				primary: "#225AA0",
				secondary: "#4bade9",
				tertiary: "#1a3c5d"
			  }
		},
	},
	plugins: [],
}
