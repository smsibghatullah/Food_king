# -*- coding: utf-8 -*-
# from odoo import http


# class FoodKing(http.Controller):
#     @http.route('/food_king/food_king', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/food_king/food_king/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('food_king.listing', {
#             'root': '/food_king/food_king',
#             'objects': http.request.env['food_king.food_king'].search([]),
#         })

#     @http.route('/food_king/food_king/objects/<model("food_king.food_king"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('food_king.object', {
#             'object': obj
#         })

