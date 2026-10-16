"""EcoNova AI demo dashboard. Live campus sensors are not configured."""
from datetime import datetime, timezone
from pathlib import Path
import csv, io, logging, os
import sys
from flask import Flask, jsonify, render_template, request, Response
from werkzeug.utils import secure_filename

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / 'uploads'
UPLOADS.mkdir(exist_ok=True)
PROJECT_ROOT = BASE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from database import database as campus_db
campus_db.init_db()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
logging.basicConfig(level=logging.INFO)

def get_alerts():
    rows=campus_db.get_all_alerts()
    levels={'Critical':'High','Warning':'Medium','Info':'Low'}
    states={'Active':'Open','Acknowledged':'Acknowledged','Resolved':'Resolved'}
    return [{'id':r['alert_id'],'title':r['title'],'facility':r['facility'],'category':r['category'],
             'severity':levels.get(r['severity'],r['severity']),'time':r['timestamp'],'description':r['description'],
             'action':r['recommended_action'],'status':states.get(r['status'],r['status'])} for r in rows]
def err(message, status): return jsonify(error=message), status

@app.get('/')
def home(): return render_template('index.html')
@app.get('/api/health')
def health():
    model=os.getenv('YOLO_MODEL','yolov8n.pt')
    try:
        import ultralytics
        yolo=Path(model).exists()
    except Exception: yolo=False
    return jsonify(ok=True,app='EcoNova AI',data_mode='demo',database='connected',integrations={'yolo':yolo,'ollama_configured':bool(os.getenv('OLLAMA_MODEL'))},timestamp=datetime.now(timezone.utc).isoformat())
@app.get('/api/energy')
def energy():
    data=campus_db.get_energy_analytics(); overview=campus_db.get_overview_metrics()
    return jsonify(demo=True,unit='kWh',total=overview['energy_consumption_kwh'],daily=data['daily']['grid'],labels=data['daily']['labels'],solar=data['daily']['solar'],facilities=dict(zip(data['facilities']['labels'],data['facilities']['used'])),facility_labels=data['facilities']['labels'],facility_values=data['facilities']['used'])
@app.get('/api/water')
def water():
    data=campus_db.get_water_analytics(); overview=campus_db.get_overview_metrics()
    return jsonify(demo=True,unit='kL',total=round(overview['water_consumption_l']/1000,1),daily=[round(x/1000,1) for x in data['daily']['consumed']],labels=data['daily']['labels'],recycled=[round(x/1000,1) for x in data['daily']['recycled']],facilities={k:round(v/1000,1) for k,v in zip(data['facilities']['labels'],data['facilities']['consumed'])},facility_labels=data['facilities']['labels'],facility_values=[round(x/1000,1) for x in data['facilities']['consumed']],review_flags=['Demo values only; review meter records before investigating possible wastage.'])
@app.get('/api/waste')
def waste():
    data=campus_db.get_waste_analytics(); overview=campus_db.get_overview_metrics()
    return jsonify(demo=True,item_count=overview['waste_items_analyzed'],quantity_kg=sum(data['quantities']),categories=data['types'],quantities=data['quantities'],recent_detections=data['recent_detections'])
@app.get('/api/alerts')
def alerts(): return jsonify(demo=True,alerts=get_alerts())
@app.patch('/api/alerts/<int:alert_id>')
def update_alert(alert_id):
    status=(request.get_json(silent=True) or {}).get('status')
    if status not in ('Open','Acknowledged','Resolved'): return err('status must be Open, Acknowledged, or Resolved',400)
    new_status={'Open':'Active','Acknowledged':'Acknowledged','Resolved':'Resolved'}[status]
    if not any(a['alert_id']==alert_id for a in campus_db.get_all_alerts()): return err('Alert not found',404)
    campus_db.update_alert(alert_id,new_status)
    return jsonify(ok=True,alert_id=alert_id,status=status,demo=True)
@app.post('/api/analyze-waste')
def analyze_waste():
    f=request.files.get('image')
    if not f or not f.filename: return err('Choose an image to analyze.',400)
    filename=secure_filename(f.filename); ext=filename.rsplit('.',1)[-1].lower() if '.' in filename else ''
    if ext not in {'png','jpg','jpeg','webp'} or (f.mimetype and not f.mimetype.startswith('image/')): return err('Upload a PNG, JPG, JPEG, or WebP image.',415)
    data=f.read()
    if not data: return err('The selected image is empty.',400)
    if len(data)>8*1024*1024: return err('Image must be 8 MB or smaller.',413)
    try:
        from PIL import Image
        Image.open(io.BytesIO(data)).verify()
    except Exception: return err('This file could not be read as a valid image.',400)
    model=os.getenv('YOLO_MODEL','yolov8n.pt')
    try:
        from ultralytics import YOLO
        if not Path(model).exists(): return err('Image detection is unavailable: install ultralytics and provide a YOLO model file (YOLO_MODEL). No results were fabricated.',503)
        temp=UPLOADS/(datetime.now().strftime('%Y%m%d%H%M%S%f')+'_'+filename); temp.write_bytes(data)
        try:
            result=YOLO(model)(str(temp),verbose=False)[0]; detections=[]
            for box in result.boxes:
                cls=int(box.cls[0]); detections.append({'label':result.names[cls],'confidence':round(float(box.conf[0]),3)})
            return jsonify(ok=True,demo=False,model=Path(model).name,detections=detections,note='General object detection only. Recycling or hazardous classification requires human verification.')
        finally: temp.unlink(missing_ok=True)
    except ImportError: return err('Image detection is unavailable. Install ultralytics and configure a YOLO model. No results were fabricated.',503)
    except Exception:
        app.logger.exception('Image inference failed'); return err('Image analysis failed. Check the model file and server log.',500)
@app.post('/api/ai-recommendations')
def recommendations():
    model=os.getenv('OLLAMA_MODEL','deepseek-r1:latest'); base=os.getenv('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
    try:
        import requests
        r=requests.post(base+'/api/generate',json={'model':model,'prompt':'Give three short campus sustainability actions using only these demo indicators: energy 4280 kWh, water 186 kL, review labs energy and hostel water. State indicators are demo data.','stream':False},timeout=12)
        if r.ok:
            answer=r.json().get('response','').strip()
            if answer: return jsonify(ok=True,source='Ollama '+model,demo=False,recommendations=answer)
        app.logger.warning('Ollama returned HTTP %s',r.status_code)
    except Exception: app.logger.info('Ollama unavailable; returning labelled demo guidance')
    return jsonify(ok=True,source='Demo guidance',demo=True,recommendations='Review laboratory operating schedules against actual meter data.\nCheck hostel water readings and inspect high-use fixtures.\nAdd clear sorting instructions at cafeteria collection points.',message='Ollama is unavailable. These are general demo suggestions, not generated AI results.')
@app.get('/api/report.csv')
def report():
    metrics=campus_db.get_overview_metrics(); waste_data=campus_db.get_waste_analytics()
    s=io.StringIO(); w=csv.writer(s); w.writerow(['EcoNova AI Sustainability Report','DEMO DATA']); w.writerow(['Campus','DSU — Harohalli']); w.writerow(['Generated',datetime.now().astimezone().isoformat()]); w.writerow([]); w.writerow(['Metric','Value','Unit']); w.writerow(['Energy consumption',metrics['energy_consumption_kwh'],'kWh']); w.writerow(['Water consumption',round(metrics['water_consumption_l']/1000,1),'kL']); w.writerow(['Waste collected',round(sum(waste_data['quantities']),1),'kg']); w.writerow(['Waste items analyzed',metrics['waste_items_analyzed'],'demo detections']); w.writerow(['Alerts',len(get_alerts()),'demo alerts']); w.writerow([]); w.writerow(['Alert','Facility','Category','Severity','Status','Recommended action'])
    for a in get_alerts(): w.writerow([a['title'],a['facility'],a['category'],a['severity'],a['status'],a['action']])
    return Response('\ufeff'+s.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=econova-demo-report.csv'})
@app.errorhandler(413)
def too_large(_): return err('Image must be 8 MB or smaller.',413)
@app.errorhandler(404)
def not_found(_): return err('API route not found',404) if request.path.startswith('/api/') else ('Not found',404)
if __name__=='__main__': app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=False)
