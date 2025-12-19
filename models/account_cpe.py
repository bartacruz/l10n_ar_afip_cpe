# Copyright (C) 2025 Julio Santa Cruz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from random import randint
from datetime import datetime, timedelta
from odoo import _, api, fields, models

class AccountCPE(models.Model):
    _name = "account.cpe"
    _description = "Carta de Porte"
    
    name = fields.Char("Name", required=True)
    status = fields.Selection([
        ('AC','Activada'),
        ('AN', 'Anulada'),
        ('BR', 'Borrador'),
        ('CF', 'Activa con confirmacion de arribo'),
        ('CN', 'Confirmada'),
        ('CO', 'Activa con contingencia'),
        ('DE', 'Desactivada'),
        ('RE', 'Rechazada'),
        ('PA', 'Pendiente de Aceptacion por el Productor'),
        ('AP', 'Anulación por el Productor'),
        ('DD', 'Descargado en destino'),
        ('PE', 'Pendiente de emisión'),
        ('IN', 'Inactiva'),
        ('PO', 'Pendiente de Aceptacion por el Origen'),
        ],
        _("Status"),
        required=True,
        default='BR'
    )
    origin = fields.Many2one('res.partner',_("Origin"),domain="[('tms_location','=',True)]" )
    destination = fields.Many2one('res.partner',_("Destination"),domain="[('tms_location','=',True)]" )
    
    cpe = fields.Char("CPE Number")
    license_plate = fields.Char("License Plate")

        
    def get_connection(self):
        ws = self.env.user.company_id.get_conection("wscpe").connect()
        msg = "AppServerStatus: %s DbServerStatus: %s AuthServerStatus: %s" % (
            ws.AppServerStatus,
            ws.DbServerStatus,
            ws.AuthServerStatus,
        )
        print(msg)
        return ws
        