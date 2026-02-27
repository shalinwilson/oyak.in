# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
	"name":"Most Sold Product Odoo App",
	"version":"16.0.0.2",
	"category":"Sale",
	"summary":"print most sold products pdf and xls report most sales product report top sold product category report download top sold product pdf report top selling products sold xls report sales product report sold product report",
	"description":"""The Most Sold Products Report Odoo app helps businesses to generate a comprehensive PDF and XLS report on the most sold products and look insights into their sales performance. This app allows businesses to analyze sales trends, identify top-performing products between selected start and end dates and make informed decisions to optimize their sales strategies. User have option to limit the record for report. User can also generate most sold report By Product, By Product Category, and By Sales Amount.""",
	"license": "OPL-1",
	"author": "BROWSEINFO",
	"website" : "https://www.browseinfo.com/demo-request?app=bi_most_sold_product&version=16&edition=Community",
	"depends":["base",
			   "sale",
			   "sale_management",
			  ],
	"data":[
			"security/ir.model.access.csv",
			"wizard/most_sold_product_wizard_form.xml",
			"wizard/excel_report_wizard_form.xml",
			"views/sale_order_view.xml",
			"report/most_sold_product_report_button.xml",
			"report/most_sold_product_report_template_view.xml",
			],
	"auto_install": False,
	"application": True,
	"installable": True,
	"images":['static/description/Most-Sold-Product-Banner.gif'],
	'live_test_url':'https://www.browseinfo.com/demo-request?app=bi_most_sold_product&version=16&edition=Community',
}
