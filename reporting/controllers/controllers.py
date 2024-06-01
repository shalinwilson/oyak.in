# -*- coding: utf-8 -*-
# from odoo import http


# class Reporting(http.Controller):
#     @http.route('/reporting/reporting', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/reporting/reporting/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('reporting.listing', {
#             'root': '/reporting/reporting',
#             'objects': http.request.env['reporting.reporting'].search([]),
#         })

#     @http.route('/reporting/reporting/objects/<model("reporting.reporting"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('reporting.object', {
#             'object': obj
#         })
