from odoo import _, api, fields, models

class AfipState(models.Model):
    _name = 'afip.state'
    _order = "afip_code,id"
    _rec_name = 'afip_name'
    
    state_id = fields.Many2one('res.country.state')
    country_id = fields.Many2one('res.country',related = 'state_id.country_id', readonly=True)
    afip_code = fields.Integer()
    afip_name = fields.Char()
    
    def _guess_state(self):
        for record in self:
            s = self.env['res.country.state'].search([ ('name','ilike',record.afip_name) , ('country_id.code','=','AR') ],limit=1)
            if s:
                record.state_id = s
                
    def action_import_states(self):
        ws = self.env['afip.cpe'].get_connection()
        states = ws.ConsultarProvincias(sep=None)
        for p in states:
            state = self.create({
                'afip_code':p.get('codigo'),
                'afip_name': p.get('descripcion'),
            })
            state._guess_state()
            print(state.id,state.afip_code,state.afip_name,state.state_id.name)

class AfipLocality(models.Model):
    _name = 'afip.locality'
    _order = "afip_state_id,name"
    name = fields.Char()
    state_id = fields.Many2one('res.country.state')
    afip_code = fields.Integer()
    afip_state_id = fields.Many2one('afip.state', compute='_compute_afip_state', store=True)
    
    @api.depends('state_id')
    def _compute_afip_state(self):
        for record in self:
            record.afip_state_id = self.env['afip.state'].search([('state_id','=',record.state_id.id)], limit=1)
        
    
    
    def action_import_localities(self):
        ws = self.env['afip.cpe'].get_connection()
        for state in self.env['afip.state'].search([]):
            
            localities = ws.ConsultarLocalidadesPorProvincia(state.afip_code,sep=None)
            for l in localities:
                loc = self.create({
                    'state_id': state.state_id.id,
                    'afip_code':l.get('codigo'),
                    'name': l.get('descripcion'),
                })
                print(loc.state_id.name,loc.afip_code,loc.name)
            
    
    
    