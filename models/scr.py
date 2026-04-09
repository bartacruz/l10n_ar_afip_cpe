Cuit = 30712465804
env = []
def tests():
    env = []
    cpe = env['afip.cpe'].import_cpe(30618705672,ctg=10128030983)
    cpe = env['afip.cpe'].import_cpe(30618705672,)
    cpe = env['afip.cpe'].import_cpe(30559800879,origin=1,order_number=652)


    ws = env['afip.cpe'].get_connection()
    result = ws.ConsultarCPEAutomotor(cuit_solicitante=30618705672,nro_ctg=10128030983)
import time
def import_cpe(file):
    Cuit = 30712465804
    with open(file) as f:
        while True:
            line=f.readline()
            if not line:
                break
            sline = line.split(';')
            tag = sline[0].split('-')
            #print(line)
            
            if len(tag) > 1:
                ctg = int(tag[1])
                
                if ctg > 10000000000 and ctg <20000000000 :
                    
                    #print("env['afip.cpe'].import_cpe(%s,ctg=%s)" % (Cuit,ctg,))
                    
                    cpe = env['afip.cpe'].import_cpe(Cuit,ctg=ctg)
                    env.cr.commit()
                    time.sleep(1)
                else:
                    print("t1",ctg)
            else:
                print("t",tag)
                
def scr():
    ws = env['afip.cpe'].get_connection()

    for state in env['afip.state'].search([]):
        locs = ws.ConsultarLocalidadesPorProvincia(state.afip_code)
        for l in locs:
            pass
    #env['afip.locality'].action_import_localities()
        
    import_cpe("/home/julio/Descargas/cpes.csv")
    env['mail.message'].search([ ('body','ilike','Rechazar') ])
    env['whatsapp.composer'].with_context(active_model='tms.order',active_id=135).create({'template_id':9,'res_model':'res.partner','res_id':4185,'number_field_name':'phone'})._action_send_whatsapp()

    {
        'value': {
            'messaging_product': 'whatsapp', 
            'metadata': {
                'display_phone_number': '5493329516272', 
                'phone_number_id': '929126623616793'}, 
            'contacts': [
                {
                    'profile': {'name': 'Julio Santa Cruz'}, 
                    'wa_id': '5491154970938'
                    }
                ], 
            'messages': [
                {
                    'context': {
                        'from': '5493329516272', 
                        'id': 'wamid.HBgNNTQ5MTE1NDk3MDkzOBUCABEYEkQ3QTYwRENCODQ4MTlFM0M1RgA='
                        }, 
                    'from': '5491154970938', 
                    'id': 'wamid.HBgNNTQ5MTE1NDk3MDkzOBUCABIYIEE1NzA4RDlDMzlDNzg0MDQ5NTUyQjJGRkQ4OUY1Q0QxAA==', 
                    'timestamp': '1772130567', 
                    'type': 'button', 
                    'button': {
                        'payload': 'Rechazar', 
                        'text': 'Rechazar'
                    }
                }
            ]
        },
        'field': 'messages'
    }
def read_barcode(file):
    from PIL import Image
    from pyzbar.pyzbar import decode
    image = Image.open(file)
    s = decode(image)
    print(s)

import sys
if __name__ == '__main__':
    print(sys.argv)
    read_barcode(sys.argv[1])
    