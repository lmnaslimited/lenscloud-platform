import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import frappeUI from 'frappe-ui/vite'

const backendUrl = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

export default defineConfig({
	plugins: [
		frappeUI({
			frappeProxy: true,
			lucideIcons: true,
			jinjaBootData: true,
			buildConfig: {
				indexHtmlPath: '../lenscloud/www/lenscloud.html',
				emptyOutDir: true,
				sourcemap: true,
			},
		}),
		vue(),
	],
	base: '/assets/lenscloud/frontend/',
	resolve: {
		alias: {
			'@': path.resolve(__dirname, 'src'),
		},
	},
	optimizeDeps: {
		exclude: ['frappe-ui'],
	},
	server: {
		host: '0.0.0.0',
		port: 5173,
		strictPort: true,
		proxy: {
			'/api': {
				target: backendUrl,
				changeOrigin: true,
				secure: false,
			},
			'/assets': {
				target: backendUrl,
				changeOrigin: true,
				secure: false,
			},
			'/files': {
				target: backendUrl,
				changeOrigin: true,
				secure: false,
			},
			'/private': {
				target: backendUrl,
				changeOrigin: true,
				secure: false,
			},
			'/login': {
				target: backendUrl,
				changeOrigin: true,
				secure: false,
			},
			'/logout': {
				target: backendUrl,
				changeOrigin: true,
				secure: false,
			},
		},
	},
	build: {
		outDir: '../lenscloud/public/frontend',
		emptyOutDir: true,
		cssCodeSplit: false,
		rollupOptions: {
			input: 'index.html',
			output: {
				entryFileNames: 'assets/lenscloud-[hash].js',
				chunkFileNames: 'assets/chunks/[name]-[hash].js',
				assetFileNames: 'assets/[name]-[hash][extname]',
			},
		},
	},
})
