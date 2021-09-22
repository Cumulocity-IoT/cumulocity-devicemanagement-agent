import requests
import json
import urllib
import time
from base64 import b64encode

def test_device_exists(options):
  agent_mo = get_agent_mo(**options)
  assert agent_mo['c8y_IsDevice'] == {}

def test_upload_logfile(options):
  # test maximumLines option
  assert delete_existing_logfile(**options)
  agent_mo = get_agent_mo(**options)
  assert "c8y_LogfileRequest" in agent_mo['c8y_SupportedOperations']
  device_id = agent_mo['id']
  maximum_lines = 4
  operation_maxlines = {
    "description": "execution from pytest",
    "c8y_LogfileRequest": {
      "logFile": "agentlog",
      "dateFrom": "2000-01-27T13:45:24+0100",
      "dateTo": "2099-01-28T13:45:24+0100",
      "searchText": "",
      "maximumLines": maximum_lines
    },
    "deviceId": device_id
  }
  assert create_operation(device_id, operation_maxlines, **options)
  time.sleep(1)
  logs = list_logfile(**options)['managedObjects']
  assert len(logs) == 1
  log = get_logfile(logs[0]['id'], **options)
  assert log.count('\n') == maximum_lines

  # test searchText option
  assert delete_existing_logfile(**options)
  phrase = "connected"
  operation_search_text = {
    "description": "execution from pytest",
    "c8y_LogfileRequest": {
      "logFile": "agentlog",
      "dateFrom": "2000-01-27T13:45:24+0100",
      "dateTo": "2099-01-28T13:45:24+0100",
      "searchText": phrase,
      "maximumLines": 100
    },
    "deviceId": device_id
  }
  assert create_operation(device_id, operation_search_text, **options)
  time.sleep(1)
  logs = list_logfile(**options)['managedObjects']
  assert len(logs) == 1
  log = get_logfile(logs[0]['id'], **options)
  first_line = log.split('\n')[0]
  assert phrase in first_line

def get_agent_mo(serial, url, tenant, username, password):
  headers = get_headers(tenant, username, password)
  params = urllib.parse.urlencode({'q': '(c8y_Hardware.serialNumber eq {})'.format(serial)})
  full_url = 'https://{}/inventory/managedObjects?{}'.format(url, params)
  response = requests.request("GET", full_url, headers=headers)
  res = json.loads(response.text)
  assert len(res['managedObjects']) == 1
  return res['managedObjects'][0]

def create_operation(device_id, operation, serial, url, tenant, username, password):
  path = '/devicecontrol/operations'
  headers = get_headers(tenant, username, password)
  params = {'deviceId': device_id}
  data = json.dumps(operation)
  res = req(url, path, 'POST', params, headers, data)
  assert res.status_code == 201
  return True

def list_logfile(serial, url, tenant, username, password):
  path = '/inventory/managedObjects'
  headers = get_headers(tenant, username, password)
  params = {'query': f'(name eq logfile{serial})'}
  res = req(url, path, 'GET', params, headers)
  assert res.status_code == 200
  return json.loads(res.text)

def get_logfile(id, serial, url, tenant, username, password):
  path = f'/inventory/binaries/{id}'
  headers = get_headers(tenant, username, password)
  res = req(url, path, 'GET', {}, headers)
  assert res.status_code == 200
  return res.text

def delete_existing_logfile(serial, url, tenant, username, password):
  mos = list_logfile(serial, url, tenant, username, password)['managedObjects']
  ids = [mo['id'] for mo in mos]
  path = '/inventory/binaries'
  headers = get_headers(tenant, username, password)
  [req(url, f'{path}/{id}', 'DELETE', {}, headers) for id in ids]
  assert [] == list_logfile(serial, url, tenant, username, password)['managedObjects']
  return True

def get_headers(tenant, username, password):
  auth_string = f'{tenant}/{username}:{password}'
  encoded_auth_string = b64encode(bytes(auth_string, 'utf-8')).decode('ascii')
  headers = {'Authorization': 'Basic ' + encoded_auth_string,
             'Content-Type': 'application/json'}
  return headers

def req(url, path, method, params, headers, data=None):
  params['pageSize'] = 2000
  params_enc = urllib.parse.urlencode(params)
  full_url = 'https://{}{}?{}'.format(url, path, params_enc)
  res = requests.request(method, full_url, headers=headers, data=data)
  return res
