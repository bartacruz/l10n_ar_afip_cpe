# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    recs = env['afip.cpe.transport'].search([('vehicle_id', '!=', False)])
    
    for rec in recs:
        if rec.vehicle_id.license_plate:
            rec.vehicle = rec.vehicle_id.license_plate
        if rec.trailer_id and rec.trailer_id.license_plate:
            rec.trailer = rec.trailer_id.license_plate
            