from odoo import models, fields, api
import requests
import datetime
import logging

_logger = logging.getLogger(__name__)

class PatientSync(models.Model):
    _name = 'patient.sync'
    _description = 'Patient Synchronization'

    record_id = fields.Char(string='Record ID')
    name = fields.Char(string='Patient Name')
    log_messages = fields.Html(string='Log Messages') 
    # Add other relevant fields here

    def sync_patients(self):
        """
        Scheduled method to synchronize patient records.
        """
        try:
            # Make an HTTP request to the REST web service
            response = requests.post('https://sistema.sirexe.com/api/1.1/wf/atenciones_abiertas', headers = { "authorization" : "Bearer 51afb1eb9906f51d259319e960caff80" })
            if response.status_code == 200:
                patient_records = response.json()
                for record in patient_records:
                    matricula_expediente = record.get('Matricula')
                    contact = self.env['res.partner'].search([('matricula_expediente', '=', matricula_expediente)])
                    if not contact:
                        # Create a new contact if not found
                        contact = self.env['res.partner'].create({
                            'matricula_expediente': matricula_expediente,
                            'name': record.get('NombrePaciente'),
                            'curp': record.get('CURP'),
                            'url_expediente': record.get('Perfil'),
                            # Add other relevant fields
                        })
                        _logger.info(f"New contact created for record ID {matricula_expediente}")
                    else:
                        _logger.info(f"Contact already exists for record ID {matricula_expediente}")
                    fecha = datetime.datetime.strptime(record.get('Fecha'), '%d/%m/%Y')
                    evento = self.env['smm_eventos_medicos'].search([('paciente_id', '=', contact.id), ('fecha_inicio', '=', fecha)])
                    if not evento:
                        # Create new event if not found
                        contact = self.env['smm_eventos_medicos'].create({
                            'paciente_id': contact.id,
                            'fecha_inicio' : fecha
                        })
                    break
            else:
                _logger.error(f"Failed to fetch patient records. Status code: {response.status_code}")
        except Exception as e:
            _logger.error(f"Error during synchronization: {str(e)}")
