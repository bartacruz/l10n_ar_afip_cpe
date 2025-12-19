##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AfipwsConnection(models.Model):
    _inherit = "afipws.connection"

    # TODO use _get_afip_ws_selection to add values to this selection
    afip_ws = fields.Selection(
        selection_add=[
            ("wscpe", "Carta de Porte"),
        ],
        ondelete={
            "wscpe": "set default",
        },
    )

    @api.model
    def _get_ws(self, afip_ws):
        """
        Method to be inherited
        """
        ws = super(AfipwsConnection, self)._get_ws(afip_ws)
        if afip_ws == "wscpe":
            from pyafipws.wscpe import WSCPE
            ws = WSCPE()
            ws.HOMO = self.type == "homologation"
        return ws

    @api.model
    def get_afip_ws_url(self, afip_ws, environment_type):
        afip_ws_url = super(AfipwsConnection, self).get_afip_ws_url(
            afip_ws, environment_type
        )
        if afip_ws_url:
            return afip_ws_url
        elif afip_ws == "wscpe":
            if environment_type == "production":
                afip_ws_url = "https://cpea-ws.afip.gob.ar/wscpe/services/soap?wsdl"
                #afip_ws_url = "https://serviciosjava.afip.gob.ar/wscpe/services/soap?wsdl"
            else:
                afip_ws_url = "https://cpea-ws-qaext.afip.gob.ar/wscpe/services/soap?wsdl"
                #afip_ws_url = "https://fwshomo.afip.gov.ar/wscpe/services/soap?wsdl"
    
        return afip_ws_url
