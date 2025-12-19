# Copyright (C) 2025 - Julio Santa Cruz 
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"
    # # TMS Type
    cpe_location = fields.Integer(string="CPE location")

    # def action_cpe_locations_lookup(self):
    #     ws = self.company_id.get_conection("wscpe").connect()
    #     def to_degrees(val):
    #         return int(val.get('grados'))+int(val.get('minutos'))/60+int(val.get('segundos'))/3600
        
    #     for record in self:
    #         ret = ws.ConsultarLocalidadesProductor(cuit_productor=record.vat)
    #         for loc in ret:
    #             code = loc.get('codigo')
    #             location = self.env["res.partner"].search([('afip_location_code','=',code)],limit=1)
    #             desc = loc.get("descripcion")
    #             results = re.search('(.*)\s+\(ID Provincia: (\d+)\)')
    #             location_name = results.group(1)
    #             province_id = results.group(2)
    #             if not location:
    #                 location = self.env["res.partner"].create({
    #                     'parent_id': record.id,
    #                     'name': location_name,
    #                     'tms_location': True
    #                 })
    #             location.name = location_name
    #             location.afip_location_code = code
    #             location.comment = loc.get('')
    #             location.partner_latitude = to_degrees(loc.get('coordenadas')[0].get('latitud'))
    #             location.partner_longitude = to_degrees(loc.get('coordenadas')[0].get('longitud'))
    #             print("saving ",location.name,location.afip_location_code,location.partner_latitude,location.partner_latitude)
    #             location.save()
                
    #     return True
                
                
            