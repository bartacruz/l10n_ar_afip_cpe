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
import logging
import pytz

_logger = logging.getLogger(__name__)

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
    origin_code = fields.Integer()
    origin_id = fields.Many2one('res.partner',_("Origin"),domain="[('tms_location','=',True)]" )
    origin_locality_id = fields.Many2one('afip.locality')
    origin_state_id = fields.Many2one('res.country.state', compute='_compute_origin', store=True)
    
    origin_city = fields.Char( compute='_compute_origin', store=True)
    order_number = fields.Integer()
    ctg_number = fields.Char(_("CTG Number"))
    emmited_date = fields.Datetime() # fechaEmision
    status_date = fields.Datetime() # fechaInicioEstado 
    due_date = fields.Datetime() # fechaVencimiento
    observations = fields.Char(_("Observations"))
    
    load_gross = fields.Integer()
    load_tare = fields.Integer()
    load_net = fields.Integer(compute='_compute_load_net')
    unload_gross = fields.Integer()
    unload_tare = fields.Integer()
    unload_net = fields.Integer(compute='_compute_unload_net')
    
    destination_code = fields.Integer()
    destination_partner_id = fields.Many2one("res.partner", _("Destination Partner"), domain="[('tms_location','=',False), ('is_company','=',True)]")
    destination_id = fields.Many2one('res.partner',_("Destination"),domain="[('tms_location','=',True)]" )
    destination_locality_id = fields.Many2one('afip.locality')
    destination_state_id = fields.Many2one('res.country.state', compute='_compute_destination', store="True")
    destination_city = fields.Char(compute='_compute_destination', store="True")
    
    
    customer_id = fields.Many2one("res.partner", _("Customer"), domain="[('tms_location','=',False), ('is_company','=',True)]", compute='_compute_customer_id', store=True)
    transport_ids = fields.One2many('afip.cpe.transport','cpe_id',_("Transports"))
    pdf = fields.Binary()
    pdf2 = fields.Binary()
    pdf3 = fields.Many2one('ir.attachment')
    
    drivers = fields.Char(readonly=True,compute='_compute_drivers')
    license_plates = fields.Char(readonly=True,compute='_compute_licenses')
    participants_ids = fields.Many2many('res.partner',compute='_compute_participants', store=True)
    afip_xml_response = fields.Text(
        string="AFIP XML Response",
        copy=False,
    )
        
    
    def _localize_datetime(self, dt_value):
        """
        Convierte un string ISO o un datetime naive a un datetime 
        localizado según la zona horaria del usuario.
        """
        if not dt_value:
            return False
            
        if isinstance(dt_value, str):
            dt_value = datetime.fromisoformat(dt_value)
        
        if dt_value.tzinfo:
            return dt_value    
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        if dt_value.tzinfo:
            dt_utc = dt_value.astimezone(pytz.utc)
        else:
            dt_localized = user_tz.localize(dt_value)
            dt_utc = dt_localized.astimezone(pytz.utc)
        return dt_utc.replace(tzinfo=None)
    
    @api.depends('load_gross','load_tare')
    def _compute_load_net(self):
        for record in self:
            record.load_net = record.load_gross - record.load_tare
    
    @api.depends('unload_gross','unload_tare')
    def _compute_unload_net(self):
        for record in self:
            record.unload_net = record.unload_gross - record.unload_tare
    
    @api.depends('origin_id')
    def _compute_origin(self):
        for record in self:
            if record.origin_id:
                record.origin_state_id = record.origin_id.state_id
                record.origin_city = record.origin_id.city
            else:
                record.origin_state_id = False
                record.origin_city = None

    @api.depends('destination_id')
    def _compute_destination(self):
        for record in self:
            if record.destination_id:
                record.destination_state_id = record.destination_id.state_id
                record.destination_city = record.destination_id.city
            else:
                record.destination_state_id = False
                record.destination_city = None
                                
    @api.depends('origin_partner_id','customer_id','destination_partner_id','transport_ids')
    def _compute_participants(self):
        for record in self:
            record.participants_ids = record.customer_id | record.origin_partner_id | record.destination_partner_id
            for t in record.transport_ids:
                record.participants_ids |= t.customer_id
                record.participants_ids |= t.driver_id
            
        
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
                l.append(x.vehicle_id.license_plate or '')
                l.append(x.trailer_id.license_plate or '')
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

    def _get_vehicle(self,license_plate, trailer=False):
        v = self.env['fleet.vehicle'].search([ ('license_plate','=',license_plate)],limit=1)
        model_id = 49 if trailer else 48
        vals = {
            'model_id':model_id,
            'state_id': 2,
            'operation': 'trailer' if trailer else 'cargo',
            'license_plate':license_plate
        }
        if not v:    
            v = self.env['fleet.vehicle'].create(vals)
            print("vehiculo creado",v,v.license_plate)
        else:
            v.update(vals)
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
            trailer = self._get_vehicle(dominios[1], trailer=True) if len(dominios) > 1 else None
            driver = self._get_driver(t.find('cuitChofer').text)
            print("vehicles",vehicle,trailer,driver,driver.tms_driver_id)
            if vehicle and driver:
                vehicle.tms_driver_id = driver
                vehicle.driver_id = driver.partner_id
            if trailer:
                # TODO: check if this doesn't override vehicle driver
                # TODO: Trailer logic in fleet.vehicle
                vehicle.trailer_id = trailer
            
            vals = {
                'cpe_id': cpe.id,
                'partner_id': self._get_partner(t.find('cuitTransportista').text).id,
                'customer_id': self._get_partner(t.find('cuitPagadorFlete').text).id,
                'driver_id': driver.partner_id.id,
                'vehicle_id': vehicle.id,
                'trailer_id': trailer.id if trailer else None,
                'start_date': self._localize_datetime(t.find("fechaHoraPartida").text),
                'distance': t.find("kmRecorrer").text,
                'fumigated_goods': t.find("mercaderiaFumigada").text
            }
            price = t.find('tarifa')
            if price:
                vals['price'] = price.text
            
            print(vals)
            self.env['afip.cpe.transport'].search([('cpe_id','=',self.id)]).unlink()
            self.env['afip.cpe.transport'].create(vals)
    
    def action_check_pending(self):
        ws = self.get_connection()
        pending = ws.ConsultarCPEPendientesDeResolucion(perfil="S")

    @api.model
    def _cron_update_active_records(self):
        actives = self.search([('status','in',['AC','BR','CF','CO','PA','PE','PO'])])
        for record in actives:
            record.action_update_cpe()
        
    def action_update_cpe(self,force=False):
        vat = self.env.user.company_id.partner_id.vat
        ret = False
        if '-' in self.name:
            if self.origin_partner_id:
                vat = self.origin_partner_id.vat
            origin,number = self.name.split('-')
            ret = self.import_cpe(vat,origin=int(origin),order_number=int(number),force=force)
        else:
            ret = self.import_cpe(vat,ctg=self.name, force=force)
        return ret
        
    def import_cpe(self,cuit_solicitante, ctg=None,origin=None,order_number=None, force=False):
        old_status = self.status
        old_status_date = self.status_date
        ws = self.get_connection()
        print(ctg,origin,order_number)
        if ctg:
            result = ws.ConsultarCPEAutomotor(cuit_solicitante=cuit_solicitante,nro_ctg=ctg,archivo="/dev/null")
        elif origin and order_number:
            result = ws.ConsultarCPEAutomotor(cuit_solicitante=cuit_solicitante,sucursal=origin,nro_orden=order_number, tipo_cpe=74, archivo="/dev/null")
        else:
            result = None
        print(result, ws.errores)
        if not result or ws.errores:
            print("Error")
            print(ws.xml_request)
            print(ws.xml_response)
            return None
        print(ws.xml_response)
        cabecera = ws.ret.get('cabecera')
        vals = {
            #'name': ws.NroCTG,
            'status': ws.Estado,
            'type': cabecera.get('tipoCartaPorte'),
            'origin_number':cabecera.get('sucursal'),
            'order_number': cabecera.get('nroOrden'),
            'ctg_number': ws.NroCTG,
            'emmited_date': self._localize_datetime(ws.FechaEmision),
            'status_date': self._localize_datetime(ws.FechaInicioEstado),
            'due_date': self._localize_datetime(ws.FechaVencimiento),
            'observations': ws.Observaciones,
        }
        if self.id:
            cpe = self
            cpe.afip_xml_response = ws.xml_response
            
            _logger.info("Checking CPE %s updated: %s %s %s %s %s",self.name,vals.get('status'),old_status,vals.get('status_date'), self.status_date,force)
            if vals.get('status') == old_status and vals.get('status_date') == self.status_date and not force:
                print("ignoring non-updated CPE",cpe.name)
                return False
            cpe.update(vals)
            cpe.message_post(body=_("Carta de Porte actualizada desde ARCA"))
        else:
            cpe = self.search([('ctg_number','=',ws.NroCTG)], limit=1)
            if cpe:
                cpe.update(vals)
                cpe.message_post(body=_("Carta de Porte actualizada desde ARCA"))
            else:
                vals['name'] = vals.get('name',ws.NroCTG)
                cpe = self.create(vals)
                cpe.message_post(body=_("Carta de Porte creada desde ARCA"))
                print("cpe creada",cpe.id, vals)
                cpe.afip_xml_response = ws.xml_response
        if not force:
            cpe_bytes = ws.PDF
            if sys.version_info[0] >= 3 and isinstance(cpe_bytes, str):
                cpe_bytes = cpe_bytes.encode("utf-8")
            
            cpe.pdf = base64.b64encode(cpe_bytes).decode()
            cpe.pdf2 = base64.b64encode(cpe_bytes)
            attachment = cpe.env['ir.attachment'].create({
                'name': 'CPE - %s.pdf' % cpe.name,
                'type': 'binary',
                'datas': base64.b64encode(cpe_bytes),
                'res_model': 'afip.cpe',
                'res_id': cpe.id,
                'mimetype': 'application/pdf',
            })
            body = _("PDF Descargado desde ARCA")
            cpe.message_post(body=body, attachment_ids=[attachment.id])
            #cpe.pdf = cpe_bytes
            cpe.pdf3 = attachment
        
        origen = ws.ret.get('origen')
        cpe.origin_partner_id = cpe._get_partner(origen.get('cuit'),fetch_locations=True)
        print("origin_partner",origen.get('cuit'),cpe.origin_partner_id)
        
        cpe.origin_code = origen.get('planta',False)
        print("Origen",origen.get('planta'),origen.get('codProvincia'),origen.get('codLocalidad'))
        cpe.origin_locality_id = self.env['afip.locality'].search([('afip_code','=',origen.get('codLocalidad'))],limit=1)
        if cpe.origin_code:
            cpe.origin_id = self.env['res.partner'].search([ ('cpe_location','=',cpe.origin_code)],limit=1)
            if cpe.origin_id:
                cpe.origin_id.cpe_locality = cpe.origin_locality_id
        else:
            cpe.origin_state_id = self.env['afip.state'].search([('afip_code','=',origen.get('codProvincia'))],limit=1).state_id
            cpe.origin_city = cpe.origin_locality_id.name.title()
        destino = ws.ret.get('destino')
        cpe.destination_partner_id = cpe._get_partner(destino.get('cuit'),fetch_locations=True)
        print("destination_partner",cpe.destination_partner_id)
        
        cpe.destination_locality_id = self.env['afip.locality'].search([('afip_code','=',destino.get('codLocalidad'))],limit=1)
        cpe.destination_code = destino.get('planta',False)
        if cpe.destination_code:
            cpe.destination_id = self.env['res.partner'].search([ ('cpe_location','=',cpe.destination_code)])
            if cpe.destination_id:
                cpe.destination_id.cpe_locality = cpe.destination_locality_id
        else:
            cpe.destination_state_id = self.env['afip.state'].search([('afip_code','=',destino.get('codProvincia'))],limit=1).state_id
            cpe.destination_city = cpe.destination_locality_id.name.title()
        load_data = ws.ret.get('datosCarga')
        cpe.load_gross = load_data.get('pesoBruto',0)
        cpe.load_tare = load_data.get('pesoTara',0)
        cpe.unload_gross = load_data.get('pesoBrutoDescarga',0)
        cpe.unload_tare = load_data.get('pesoTaraDescarga',0)
        cpe._get_transport(ws,cpe)
        return cpe

    def _get_driver(self,cuit,name=None):
        sanitized_cuit = '%s' % cuit
        driver = self.env['tms.driver'].search([ ('vat','=',sanitized_cuit) ],limit=1)
        if not driver:
            # The ident type "CUIT"
            cuit_code = self.env['l10n_latam.identification.type'].search([ ('l10n_ar_afip_code','=',80)])
            
            driver = self.env['tms.driver'].create({
                'name': name or sanitized_cuit,
                'vat': sanitized_cuit,
                'is_company':False,
                'l10n_latam_identification_type_id':cuit_code.id,
            })
            try:
                vals = driver.partner_id.get_data_from_padron_afip()
                vals.pop('imp_iva_padron',None)
                vals.pop('imp_ganancias_padron',None)
                driver.country_id = self.env.user.company_id.country_id
                driver.partner_id.update(vals)
                driver.name = driver.name.title()
            except:
                pass
        return driver
        
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
            partner.name = partner.name.title()
            print("created partner",partner,partner.name,partner.vat)
            if fetch_locations:
                partner.action_cpe_locations_lookup()
                partner.action_cpe_plantas_lookup()
        
        return partner