"""Isolated local browser-review server. Never uses the user's application DB."""
import json
from pathlib import Path
from uuid import uuid4

import uvicorn

from qualityos.api import create_app

root=Path(__file__).resolve().parents[1]
directory=root/'var/ui-checks'/uuid4().hex
directory.mkdir(parents=True)
session={'base_url':'http://127.0.0.1:8112','database':str(directory/'review.sqlite'),'credentials_path':str(directory/'private-credentials.json'),'output_path':str(directory)}
(root/'var/qa-session.json').write_text(json.dumps(session,indent=2),encoding='utf-8')
app=create_app(session['database'],session['credentials_path'])
print('Isolated browser review on 127.0.0.1:8112; the user application database is not used.',flush=True)
uvicorn.run(app,host='127.0.0.1',port=8112,workers=1,log_level='warning')
