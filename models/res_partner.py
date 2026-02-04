from odoo import fields, models
import re

class ResPartner(models.Model):
    _inherit = "res.partner"

    cpe_location = fields.Integer(string="CPE location")
    cpe_ids = fields.Many2many('afip.cpe',compute='_compute_cpe_ids')
    cpe_ids_count = fields.Integer(compute="_compute_cpe_ids",readonly=True,store=True)

    def _compute_cpe_ids(self):
        for record in self:
            record.cpe_ids = self.env['afip.cpe'].search([ ('participants_ids','in',[record.id])])
            record.cpe_ids_count = len(record.cpe_ids)
            
    def action_cpe_plantas_lookup(self):
        ws = self.env.user.company_id.get_connection("wscpe").connect()
        def to_degrees(val):
            r = re.search("(-?\d+).*\s(\d+).*\s(\d+)",val)
            return int(r.group(1))+int(r.group(2))/60+int(r.group(3))/3600
            
        for record in self:
            ret = ws.ConsultarPlantas(record.vat, sep=None)
            print(ws.xml_request)
            print("===============================")
            print(ws.xml_response)
            if not ret:
                continue
            ret.pop(0)
            for loc in ret:
                code = loc.get('nroPlanta')
                
                location_name = "Planta %s" % code
                location = self.env["res.partner"].search([('cpe_location','=',code)],limit=1)
                
                if not location:
                    location = self.env["res.partner"].create({
                        'parent_id': record.id,
                        'name': location_name,
                        'tms_location': True,
                        'is_company': True,
                    })
                location.cpe_location = code
                location.street = loc.get('ubicacionGeoreferencial','').strip()
                location.type = 'delivery'
                
                province_id = loc.get('codProvincia')
                location.state_id = self.env['afip.state'].search([('afip_code','=',province_id)],limit=1).state_id
                
                locality_id = loc.get('codLocalidad')
                location.city = self.env['afip.locality'].search([('afip_code','=',locality_id)],limit=1).name.title()
                
                location.country_id = self.env.user.company_id.country_id
                
                location.partner_latitude = to_degrees(loc.get('latitud'))
                location.partner_longitude = to_degrees(loc.get('longitud'))
            
            
    def action_cpe_locations_lookup(self):
        ws = self.env.user.company_id.get_connection("wscpe").connect()
        def to_degrees(val):
            return int(val.get('grados'))+int(val.get('minutos'))/60+int(val.get('segundos'))/3600
        
        for record in self:
            ret = ws.ConsultarLocalidadesProductor(cuit_productor=record.vat, sep=None)
            print(ws.xml_request)
            print("===============================")
            print(ws.xml_response)
            for loc in ret:
                code = loc.get('codigo')
                location = self.env["res.partner"].search([('cpe_location','=',code)],limit=1)
                desc = loc.get("descripcion")
                results = re.search('(.*) \(ID Provincia: (\d+)\)', desc)
                location_name = results.group(1)
                province_id = results.group(2)
                if not location:
                    location = self.env["res.partner"].create({
                        'parent_id': record.id,
                        'name': location_name,
                        'tms_location': True,
                        'is_company': True,
                    })
                location.name = location_name
                location.cpe_location = code
                location.comment = loc.get('')
                coords = loc.get('coordenadas')
                if coords:
                    location.partner_latitude = to_degrees(coords[0].get('latitud'))
                    location.partner_longitude = to_degrees(coords[0].get('longitud'))
                print("saving ",location, location.name,location.cpe_location,location.partner_latitude,location.partner_longitude)
                # location.save()

    