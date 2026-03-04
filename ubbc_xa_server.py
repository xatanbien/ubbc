# ubbc_xa_server.py
# Run: pip install flask flask_cors
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os, json, time
app = Flask(__name__)
CORS(app)

DATA_FILE = "progress.json"
API_KEY = None  # set a string to require key, or None to disable

def load_progress():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_progress(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.get_json(force=True)
    if API_KEY:
        key = data.get("api_key") or request.headers.get("X-API-KEY")
        if key != API_KEY:
            return jsonify({"error":"invalid api_key"}), 403
    # expected fields
    don_vi = data.get("don_vi","unknown")
    khu_vuc = data.get("khu_vuc","unknown")
    tong = int(data.get("tong") or 0)
    da_bau = int(data.get("da_bau") or 0)
    con_lai = int(data.get("con_lai") or (tong - da_bau))
    ty_le = float(data.get("ty_le") or ( (da_bau/tong*100) if tong>0 else 0 ))
    cap_nhat = data.get("cap_nhat") or time.strftime("%H:%M:%S")
    prog = load_progress()
    # structure: prog[don_vi][khu_vuc] = {...}
    if don_vi not in prog:
        prog[don_vi] = {}
    prog[don_vi][khu_vuc] = {
        "tong": tong,
        "da_bau": da_bau,
        "con_lai": con_lai,
        "ty_le": round(ty_le,1),
        "cap_nhat": cap_nhat
    }
    save_progress(prog)
    return jsonify({"ok": True})

@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(load_progress())

# Simple dashboard page using Chart.js for small pies and totals
DASH_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>UBBC Xa - Tong quan</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body{font-family: Arial, Helvetica, sans-serif; background:#f8fbff; padding:16px;}
    header{background:#b30000;color:#fff;padding:10px 16px;border-radius:6px;}
    .unit{border:1px solid #ddd;padding:10px;margin:8px;border-radius:6px;background:#fff;}
    .kv{display:inline-block;width:220px;margin:6px;vertical-align:top;}
    .smallchart{width:120px;height:120px;}
    .summary{font-size:18px;margin:8px 0;}
  </style>
</head>
<body>
  <header>
    <h2>UBBC XÃ TÂN BIÊN - TỔNG QUAN TIẾN ĐỘ BỎ PHIẾU</h2>
    <div id="updated" style="font-size:14px;opacity:0.9"></div>
  </header>
  <div id="content"></div>

<script>
async function fetchStatus(){
  const r = await fetch('/api/status');
  return await r.json();
}

function mkPieCanvas(id, voted, remain, label){
  const canvas = document.createElement('canvas');
  canvas.id = id;
  canvas.className = 'smallchart';
  return canvas;
}

function render(prog){
  const content = document.getElementById('content');
  content.innerHTML = '';
  let total_all=0, voted_all=0;
  for(let don_vi in prog){
    const unitDiv = document.createElement('div');
    unitDiv.className='unit';
    const title = document.createElement('h3');
    title.textContent = don_vi;
    unitDiv.appendChild(title);
    const kvs = prog[don_vi];
    const kvWrap = document.createElement('div');
    for(let kv in kvs){
      const info = kvs[kv];
      const kvDiv = document.createElement('div');
      kvDiv.className='kv';
      const h = document.createElement('div');
      h.innerHTML = `<strong>${kv}</strong>`;
      kvDiv.appendChild(h);
      const canvas = document.createElement('canvas');
      const cid = `c_${don_vi}_${kv}`.replace(/\\s+/g,'_');
      canvas.id = cid;
      canvas.width=120; canvas.height=120;
      kvDiv.appendChild(canvas);
      const text = document.createElement('div');
      text.innerHTML = `Đã bầu: ${info.da_bau}/${info.tong} (${info.ty_le}%)<br>Còn lại: ${info.con_lai}/${info.tong}`;
      kvDiv.appendChild(text);
      kvWrap.appendChild(kvDiv);

      // draw chart
      const ctx = canvas.getContext('2d');
      new Chart(ctx, {
        type:'pie',
        data:{
          labels:['Đã bầu','Còn lại'],
          datasets:[{data:[info.da_bau, info.con_lai], backgroundColor:['#0074D9','#FF4136']}]
        },
        options:{plugins:{legend:{display:false}},maintainAspectRatio:false}
      });

      total_all += info.tong;
      voted_all += info.da_bau;
    }
    unitDiv.appendChild(kvWrap);
    content.appendChild(unitDiv);
  }
  // overall
  const summary = document.createElement('div');
  summary.className='summary';
  const percent = total_all>0? (voted_all/total_all*100).toFixed(1):0;
  summary.innerHTML = `<strong>Tổng toàn xã:</strong> Đã bầu ${voted_all}/${total_all}  ${percent}%  &nbsp;&nbsp; Còn lại: ${ (total_all - voted_all) }/${total_all} ${ (100 - percent).toFixed(1) }%`;
  content.insertBefore(summary, content.firstChild);
  document.getElementById('updated').textContent = 'Cập nhật: ' + new Date().toLocaleString();
}

async function loop(){
  try{
    const p = await fetchStatus();
    render(p||{});
  }catch(e){
    console.error(e);
  }
}
loop();
setInterval(loop, 10000);
</script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def page_index():
    return render_template_string(DASH_HTML)

if __name__ == "__main__":
    # run server on 0.0.0.0 so accessible externally (if port forwarded / public IP)
    app.run(host="0.0.0.0", port=5000, debug=False)