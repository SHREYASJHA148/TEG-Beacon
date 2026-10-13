"""Optional newline-delimited JSON serial adapter. No firmware protocol is assumed."""
import argparse, json, os
import httpx, serial

parser=argparse.ArgumentParser(description='Forward version-1 normalized JSON from a serial port')
parser.add_argument('--port',required=True)
parser.add_argument('--baud',type=int,default=115200)
parser.add_argument('--url',default='http://127.0.0.1:8000')
args=parser.parse_args()
token=os.getenv('THERMOTRACK_ADMIN_TOKEN')
headers={'Authorization':f'Bearer {token}'} if token else {}
with serial.Serial(args.port,args.baud,timeout=2) as device, httpx.Client(timeout=10,headers=headers) as client:
    print('Gateway active. Create the matching measured experiment first. Ctrl+C to stop.')
    while True:
        raw=device.readline(65537)
        if not raw: continue
        if len(raw)>65536: print('Rejected oversized serial line'); continue
        try:
            data=json.loads(raw)
            if data.get('source')!='measured': raise ValueError('Serial samples must declare measured provenance')
            endpoint='/beacon/events' if 'event_id' in data else '/telemetry'
            response=client.post(args.url+'/api/v1'+endpoint,json=data)
            response.raise_for_status()
            print(response.json())
        except (ValueError,httpx.HTTPError) as error:
            print('Gateway rejected record:',error)
