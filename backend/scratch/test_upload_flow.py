import urllib.request
import json

def post_multipart(url, fields, files):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = bytearray()
    for k, v in fields.items():
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode('utf-8'))
    for k, (filename, content, content_type) in files.items():
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode('utf-8'))
        body.extend(content)
        body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
    req = urllib.request.Request(url, data=bytes(body), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

with open(r'e:/Firemoney/floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf', 'rb') as f:
    pdf_bytes = f.read()

res = post_multipart('http://127.0.0.1:8000/projects/project-al-noor/drawings',
    {'occupancy_type': 'Business - Regular office areas', 'sprinklered': 'true', 'scale': '100'},
    {'file': ('Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf', pdf_bytes, 'application/pdf')}
)
print('Uploaded drawing response:', res)
drawing_id = res['drawing_id']

# Check image endpoint
img_url = f'http://127.0.0.1:8000/drawings/{drawing_id}/image?page=0'
try:
    with urllib.request.urlopen(img_url) as img_res:
        img_data = img_res.read()
        print('Image endpoint status:', img_res.status, 'Bytes:', len(img_data))
except Exception as e:
    print('Image fetch error:', e)

# Check elements endpoint
elem_url = f'http://127.0.0.1:8000/drawings/{drawing_id}/elements'
try:
    with urllib.request.urlopen(elem_url) as elem_res:
        elem_data = json.loads(elem_res.read().decode('utf-8'))
        print('Elements count:', len(elem_data.get('features', [])))
except Exception as e:
    print('Elements fetch error:', e)

# Check violations endpoint
viol_url = f'http://127.0.0.1:8000/drawings/{drawing_id}/violations'
try:
    with urllib.request.urlopen(viol_url) as viol_res:
        viol_data = json.loads(viol_res.read().decode('utf-8'))
        print('Violations count:', len(viol_data))
except Exception as e:
    print('Violations fetch error:', e)
