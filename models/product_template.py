import json

import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    mile_id = fields.Char(string='Mile ID')

    @api.model_create_multi
    def create(self, vals):
        products = super().create(vals)
        for product in products:
            product.mile_id = product.create_product_in_milenow()
        return products

    def write(self, vals):
        result = super(ProductTemplate, self).write(vals)
        for product in self:
            product.update_product_in_milenow(vals)
        return result

    def milenow_request(self, method, url, data):
        data = json.dumps(data)
        payload = {'user': 'api_user@whoosh.com', 'password': 'password'}
        response = requests.request(method, "https://lastmile.milenow.com/api/v1/partners/login", data=data, params=payload)
        result = response.json()
        if not result.get('access_token'):
            raise ValidationError(_("There some error occurred while authenticating the milenow server."))
        url += "?access_token=" + result['access_token']
        response = requests.request(method, url, data=data)
        response.raise_for_status()
        return response.json()

    def get_product_payload(self):
        self.ensure_one()
        return {
            'name': self.name,
            'sku': '121212',
            'description': self.description if self.description else ' ',
            'category_name': 'test',
            'brand_name': 'test_new',
            'in_stock': self.qty_available if self.qty_available else 0,
            'volume': self.volume,
            'weight': self.weight,
            'base_price': '5',
            'bar_code': self.barcode if self.barcode else ' ',
            'tax_percentage': '2',
            'external_item_code': '1222323',
            'external_id': '454'
        }

    def create_product_in_milenow(self):
        url = "https://lastmile.milenow.com/api/v1/partners/product/brand-category/create"
        payload = self.get_product_payload()
        result = self.milenow_request(method="POST", url=url, data=payload)
        if not result.get('data', {}).get('id'):
            raise ValidationError(_("There some error occurred while creating product on milenow server."))
        return result['data']['id']

    def update_product_in_milenow(self, vals):
        url = "https://lastmile.milenow.com/api/v1/partners/product/edit"
        payload = self.get_product_payload()
        payload['id'] = self.mile_id
        self.milenow_request(method="POST", url=url, data=payload)


