from odoo import fields, models
import re

class ResPartner(models.Model):
    _inherit = "res.partner"

    cpe_location = fields.Integer(string="CPE location")

    def action_cpe_locations_lookup(self):
            ws = self.env.user.company_id.get_connection("wscpe").connect()
            def to_degrees(val):
                return int(val.get('grados'))+int(val.get('minutos'))/60+int(val.get('segundos'))/3600
            
            for record in self:
                ret = ws.ConsultarLocalidadesProductor(cuit_productor=record.vat, sep=None)
                
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
                            'tms_location': True
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
                    
            