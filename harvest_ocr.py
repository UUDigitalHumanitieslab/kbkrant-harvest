import os
import os.path as op
import sys
import traceback

from lxml import etree
import requests

OCR_XPATH = "//didl:Resource[../didl:Descriptor/didl:Statement/text()='ocr']"


directory = sys.argv[1]
metafiles = os.listdir(directory)

for filename in metafiles:
    if op.splitext(filename)[1] != '.xml':
        continue
    suffix = filename.split(':')[2][-2:]
    target_dir = op.join(directory, suffix)
    os.makedirs(target_dir, exist_ok=True)
    xml = etree.parse(op.join(directory, filename))
    ns = xml.getroot().nsmap.copy()
    ns.pop(None, None)
    resources = xml.xpath(OCR_XPATH, namespaces=ns)
    for res in resources:
        try:
            target_fname = res.xpath('@dcx:filename', namespaces=ns)[0]
            url = res.get('ref')
            response = requests.get(url, stream=True, timeout=1)
            response.raise_for_status()
            target_path = op.join(target_dir, target_fname)
            if response.headers.get('Content-Encoding') not in (None, 'identity') and response.headers.get('Transfer-Encoding') not in (None, 'chunked', 'identity'):
                target_path += '.gz'
            with open(target_path, 'wb') as outfile:
                outfile.write(response.raw.read())
        except:
            print(target_fname)
            traceback.print_exc()
            print()
