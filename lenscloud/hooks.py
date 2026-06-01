app_name = "lenscloud"
app_title = "Lenscloud"
app_publisher = "LMNAs Cloud Solutions"
app_description = "Advanced Cloud Management for Frappe LENS Apps"
app_email = "hello@lmnas.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "lenscloud",
# 		"logo": "/assets/lenscloud/logo.png",
# 		"title": "Lenscloud",
# 		"route": "/lenscloud",
# 		"has_permission": "lenscloud.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lenscloud/css/lenscloud.css"
# app_include_js = "/assets/lenscloud/js/lenscloud.js"

# include js, css files in header of web template
# web_include_css = "/assets/lenscloud/css/lenscloud.css"
# web_include_js = "/assets/lenscloud/js/lenscloud.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lenscloud/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lenscloud/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Keep the LensCloud SPA route stable on refresh and deep links.
website_route_rules = [
	{"from_route": "/lenscloud", "to_route": "lenscloud"},
	{"from_route": "/lenscloud/<path:path>", "to_route": "lenscloud"},
]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lenscloud.utils.jinja_methods",
# 	"filters": "lenscloud.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "lenscloud.install.before_install"
# after_install = "lenscloud.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lenscloud.uninstall.before_uninstall"
# after_uninstall = "lenscloud.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lenscloud.utils.before_app_install"
# after_app_install = "lenscloud.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lenscloud.utils.before_app_uninstall"
# after_app_uninstall = "lenscloud.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "lenscloud.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lenscloud.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"lenscloud.tasks.all"
# 	],
# 	"daily": [
# 		"lenscloud.tasks.daily"
# 	],
# 	"hourly": [
# 		"lenscloud.tasks.hourly"
# 	],
# 	"weekly": [
# 		"lenscloud.tasks.weekly"
# 	],
# 	"monthly": [
# 		"lenscloud.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "lenscloud.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "lenscloud.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lenscloud.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lenscloud.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lenscloud.utils.before_request"]
# after_request = ["lenscloud.utils.after_request"]

# Job Events
# ----------
# before_job = ["lenscloud.utils.before_job"]
# after_job = ["lenscloud.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lenscloud.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

