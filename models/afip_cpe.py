# Copyright (C) 2025 Julio Santa Cruz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from random import randint
from datetime import datetime, timedelta
from odoo import _, api, fields, models
import xml.etree.ElementTree as ET
from datetime import datetime
import base64
import sys
import io

class AfipCPETransport(models.Model):
    _name = "afip.cpe.transport"
    _description = "Transporte de Carta de Porte"
    cpe_id = fields.Many2one('afip.cpe')
    
    partner_id = fields.Many2one('res.partner',_("Transport Company"),domain="[('tms_location','=',False), ('is_company','=',True)]")
    customer_id = fields.Many2one("res.partner", _("Customer"), domain="[('tms_location','=',False), ('is_company','=',True)]")
    
    driver_id = fields.Many2one('res.partner', _("Driver"))
    vehicle_id = fields.Many2one('fleet.vehicle',_("Vehicle"))
    trailer_id = fields.Many2one("fleet.vehicle",_("Trailer"))
    
    start_date = fields.Datetime(_("Start Date"))
    distance = fields.Integer(_("Distance"),help=_("Travelled distance (in Kms)"))
    currency_id = fields.Many2one(related='partner_id.company_id.currency_id')
    price = fields.Monetary(_("Price"),currency_field="currency_id")
    fumigated_goods = fields.Boolean(_("Fumigated Goods"))
    
class AfipCPE(models.Model):
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _name = "afip.cpe"
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
    type = fields.Integer()
    origin_number=fields.Integer() # saved for reference only
    origin_partner_id = fields.Many2one("res.partner", _("Origin Partner"), domain="[('tms_location','=',False), ('is_company','=',True)]")
    origin_id = fields.Many2one('res.partner',_("Origin"),domain="[('tms_location','=',True)]" )
    order_number = fields.Integer()
    ctg_number = fields.Char(_("CTG Number"))
    emmited_date = fields.Datetime() # fechaEmision
    status_date = fields.Datetime() # fechaInicioEstado
    due_date = fields.Datetime() # fechaVencimiento
    observations = fields.Char(_("Observations"))
    
    destination_partner_id = fields.Many2one("res.partner", _("Destination Partner"), domain="[('tms_location','=',False), ('is_company','=',True)]")
    destination_id = fields.Many2one('res.partner',_("Destination"),domain="[('tms_location','=',True)]" )
    customer_id = fields.Many2one("res.partner", _("Customer"), domain="[('tms_location','=',False), ('is_company','=',True)]", compute='_compute_customer_id', store=True)
    transport_ids = fields.One2many('afip.cpe.transport','cpe_id',_("Transports"))
    pdf = fields.Binary()
    pdf_filename = fields.Char(compute = '_compute_pdf_filename')
    pdf2 = fields.Binary()
    pdf3 = fields.Many2one('ir.attachment')
    drivers = fields.Char(readonly=True,compute='_compute_drivers')
    license_plates = fields.Char(readonly=True,compute='_compute_licenses')
        
    # @api.depends('pdf','pdf_filename')
    # def _encode_pdf(self):
    #     for record in self:
    #         if record.pdf:
    #             record.pdf2 = base64.b64encode(record.pdf)
    #         else:
    #             record.pdf2 = None
            
    @api.depends('name')
    def _compute_pdf_filename(self):
        for record in self:
            record.pdf_filename = 'CPG - %s.pdf' % record.name
    
    @api.depends('transport_ids')
    def _compute_drivers(self):
        for record in self:
            record.drivers = ','.join( [x.driver_id.name for x in record.transport_ids])
    
    @api.depends('transport_ids')
    def _compute_licenses(self):
        for record in self:
            l = []
            for x in record.transport_ids:
                l.append(x.vehicle_id.license_plate)
                l.append(x.trailer_id.license_plate)
            record.license_plates = ','.join(l)
    @api.depends('transport_ids')
    def _compute_customer_id(self):
        for record in self:
            if record.transport_ids:
                record.customer_id = record.transport_ids[0].customer_id
            else:
                record.customer_id = None
                
    def get_connection(self):
        ws = self.env.user.company_id.get_connection("wscpe").connect()
        msg = "AppServerStatus: %s DbServerStatus: %s AuthServerStatus: %s" % (
            ws.AppServerStatus,
            ws.DbServerStatus,
            ws.AuthServerStatus,
        )
        print(msg)
        return ws
    
    def action_get_cpe(self):
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/afip.cpe/%s/pdf?download=true",
            
            'close': True,  # close the wizard
        }

    def _get_vehicle(self,license_plate):
        v = self.env['fleet.vehicle'].search([ ('license_plate','=',license_plate)],limit=1)
        if not v:
            vals = {
                'model_id':1,
                'license_plate':license_plate
            }
            v = self.env['fleet.vehicle'].create(vals)
            print("vehiculo creado",v,v.license_plate)
        return v

    def _get_transport(self,ws,cpe):
        root = ET.fromstring(ws.XmlResponse)
        resp = root.find('{http://schemas.xmlsoap.org/soap/envelope/}Body').find('{https://serviciosjava.afip.gob.ar/wscpe/}ConsultarCPEAutomotorResp').find("respuesta")
        for t in resp.findall("transporte"):
            ET.indent(t)
            print(ET.tostring(t))
            dominios = [x.text for x in t.findall("dominio")]
            print(dominios)
            vehicle = self._get_vehicle(dominios[0])
            trailer = self._get_vehicle(dominios[1]) if len(dominios) > 1 else None
            driver = self._get_partner(t.find('cuitChofer').text)
            if vehicle and driver:
                vehicle.driver_id = driver
            if trailer and driver:
                # TODO: check if this doesn't override vehicle driver
                # TODO: Trailer logic in fleet.vehicle
                trailer.driver_id = driver
            vals = {
                'cpe_id': cpe.id,
                'partner_id': self._get_partner(t.find('cuitTransportista').text).id,
                'customer_id': self._get_partner(t.find('cuitPagadorFlete').text).id,
                'driver_id': driver.id,
                'vehicle_id': vehicle.id,
                'trailer_id': trailer.id if trailer else None,
                'start_date': datetime.fromisoformat(t.find("fechaHoraPartida").text),
                'distance': t.find("kmRecorrer").text,
                'price': t.find('tarifa').text,
                'fumigated_goods': t.find("mercaderiaFumigada").text
            }
            print(vals)
            self.env['afip.cpe.transport'].create(vals)
    
    def action_update_cpe(self):
        if '-' in self.name:
            origin,number = self.name.split('-')
            self.import_cpe(self.origin_partner_id.vat,origin=int(origin),order_number=int(number))
        else:
            self.import_cpe(self.origin_partner_id.vat,ctg=self.name)
        
    def import_cpe(self,cuit_solicitante, ctg=None,origin=None,order_number=None):
        ws = self.get_connection()
        print(ctg,origin,order_number)
        if ctg:
            result = ws.ConsultarCPEAutomotor(cuit_solicitante=cuit_solicitante,nro_ctg=ctg)
        elif origin and order_number:
            result = ws.ConsultarCPEAutomotor(cuit_solicitante=cuit_solicitante,sucursal=origin,nro_orden=order_number, tipo_cpe=74)
        else:
            result = None
        cabecera = ws.ret.get('cabecera')
        vals = {
            #'name': ws.NroCTG,
            'status': ws.Estado,
            'type': cabecera.get('tipoCartaPorte'),
            'origin_number':cabecera.get('sucursal'),
            'order_number': cabecera.get('nroOrden'),
            'ctg_number': ws.NroCTG,
            'emmited_date': ws.FechaEmision,
            'status_date': ws.FechaInicioEstado,
            'due_date': ws.FechaVencimiento,
            'observations': ws.Observaciones,
        }
        # cpe = self.env['afip.cpe'].search([ ('ctg_number','=',ctg) ],limit=1)
        # if cpe:
        #     cpe.update(vals)
        # else:
        #     cpe = cpe.create(vals)
        #     print("cpe creada",cpe.id, vals)
        self.update(vals)
        self.message_post(body=_("Carta de Porte importada desde ARCA"))
        
        cpe_bytes = ws.PDF
        print("LEN CPE", len(cpe_bytes))
        if sys.version_info[0] >= 3 and isinstance(cpe_bytes, str):
            cpe_bytes = cpe_bytes.encode("utf-8")
        
        print("LEN CPE2", len(cpe_bytes))
        self.pdf = base64.b64encode(cpe_bytes).decode()
        self.pdf2 = base64.b64encode(cpe_bytes)
        attachment = self.env['ir.attachment'].create({
            'name': 'CPE - %s.pdf' % self.name,
            'type': 'binary',
            'datas': base64.b64encode(cpe_bytes),
            'res_model': 'afip.cpe',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        print("LEN CPE3", len(cpe_bytes),len(attachment.datas),len(self.pdf),len(self.pdf2))
        body = _("PDF Descargado desde ARCA")
        self.message_post(body=body, attachment_ids=[attachment.id])
        #cpe.pdf = cpe_bytes
        self.pdf3 = attachment
        
        origen = ws.ret.get('origen')
        self.origin_partner_id = self._get_partner(origen.get('cuit'),fetch_locations=True)
        print("origin_partner",origen.get('cuit'),self.origin_partner_id)
        destino = ws.ret.get('destino')
        destination = self._get_partner(destino.get('cuit'),fetch_locations=True)
        destination_plant = destino.get('planta',False)
        self.destination_partner_id = destination
        print("destination_partner",self.destination_partner_id)
        self.destination_id = self.env['res.partner'].search([ ('cpe_location','=',destination_plant)])
        self._get_transport(ws,self)
        return self

        
    def _get_partner(self,cuit,name=None, is_company=True,fetch_locations=False):
        sanitized_cuit = '%s' % cuit
        partner = self.env['res.partner'].search([ ('vat','=',sanitized_cuit) ],limit=1)
        if not partner:
            # The ident type "CUIT"
            cuit_code = self.env['l10n_latam.identification.type'].search([ ('l10n_ar_afip_code','=',80)])
            
            partner = self.env['res.partner'].create({
                'name': name or sanitized_cuit,
                'vat': sanitized_cuit,
                'is_company':is_company,
                 'l10n_latam_identification_type_id':cuit_code.id,
                
            })
            
            vals = partner.get_data_from_padron_afip()
            vals.pop('imp_iva_padron',None)
            vals.pop('imp_ganancias_padron',None)
            partner.update(vals)
            print("created partner",partner,partner.name,partner.vat)
            if fetch_locations:
                partner.action_cpe_locations_lookup()
                
        
        return partner