# ubbc_xa_server_v2.py
# -*- coding: utf-8 -*-
"""
UBBC XA - Server (Flask)
- Nhận báo cáo từ client (POST /api/report)
- Trả status tổng hợp (GET /api/status)
- Trang dashboard hiển thị tiến độ (GET /)
- Lưu tiến độ vào progress.json
- Option: API_KEY để hạn chế gửi
"""
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os, json, time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Config: đổi nếu muốn
DATA_FILE = "progress.json"
API_KEY = None  # Nếu muốn bảo mật, gán chuỗi, ví dụ "mabimat123"
# Nếu bạn đặt API_KEY, client phải gửi field "api_key" trong JSON hoặc header X-API-KEY.

# Utility: load & save progress
def load_progress():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_progress(prog):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(prog, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# Endpoint nhận báo cáo từ client
@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400

    # API key check (nếu bật)
    if API_KEY:
        key = data.get("api_key") or request.headers.get("X-API-KEY")
        if key != API_KEY:
            return jsonify({"error": "invalid api_key"}), 403

    don_vi = str(data.get("don_vi", "")).strip() or "unknown"
    khu_vuc = str(data.get("khu_vuc", "")).strip() or "unknown"
    try:
        tong = int(data.get("tong") or 0)
    except Exception:
        tong = 0
    try:
        da_bau = int(data.get("da_bau") or 0)
    except Exception:
        da_bau = 0
    con_lai = int(data.get("con_lai") or (tong - da_bau))
    try:
        ty_le = float(data.get("ty_le") or ( (da_bau / tong * 100) if tong>0 else 0 ))
    except Exception:
        ty_le = round((da_bau / tong * 100) if tong>0 else 0, 1)
    cap_nhat = data.get("cap_nhat") or datetime.now().strftime("%H:%M:%S %d/%m/%Y")

    prog = load_progress()
    # structure: prog[don_vi][khu_vuc] = {...}
    if don_vi not in prog:
        prog[don_vi] = {}
    prog[don_vi][khu_vuc] = {
        "tong": tong,
        "da_bau": da_bau,
        "con_lai": con_lai,
        "ty_le": round(ty_le, 1),
        "cap_nhat": cap_nhat
    }
    save_progress(prog)
    return jsonify({"ok": True})

# Endpoint trả toàn bộ status (JSON)
@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(load_progress())

# Dashboard HTML (đơn giản, responsive, dùng Chart.js)
DASH_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>UBBC XÃ TÂN BIÊN - TỔNG QUAN</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body{font-family: Arial, Helvetica, sans-serif; background:#f8fbff; margin:0; padding:12px;}
    header{background:#b30000;color:#fff;padding:10px 16px;border-radius:6px;}
    header h1{margin:0;font-size:20px}
    .topinfo{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px}
    .card{background:#fff;border-radius:8px;padding:10px;box-shadow:0 1px 4px rgba(0,0,0,0.08);}
    .unit{margin-top:12px;padding:10px;border-radius:8px;background:#fff;border:1px solid #eee}
    .kv{display:inline-block;vertical-align:top;width:220px;margin:8px}
    .kv canvas{width:120px;height:120px}
    .summary{font-size:16px}
    .footer{margin-top:12px;color:gray;font-size:13px}
    @media (max-width:700px){ .kv{width:48%} }
  </style>
</head>
<body>
  <header>
    <h1>UBBC XÃ TÂN BIÊN - TIẾN ĐỘ BỎ PHIẾU</h1>
    <div id="updated" style="font-size:13px;opacity:0.95;margin-top:6px"></div>
  </header>

  <div id="content"></div>

<script>
async function fetchStatus(){
  try{
    const r = await fetch('/api/status');
    return await r.json();
  }catch(e){
    console.error(e);
    return {};
  }
}

function clearChildren(el){ while(el.firstChild) el.removeChild(el.firstChild); }

function render(prog){
  const content = document.getElementById('content');
  clearChildren(content);
  // compute totals
  let total_all = 0, voted_all = 0;
  for(const dv in prog){
    for(const kv in prog[dv]){
      total_all += (prog[dv][kv].tong || 0);
      voted_all += (prog[dv][kv].da_bau || 0);
    }
  }
  const summaryDiv = document.createElement('div');
  summaryDiv.className='card summary';
  const pct = total_all ? (voted_all/total_all*100).toFixed(1) : 0;
  summaryDiv.innerHTML = `<strong>🔵 Tổng toàn xã:</strong> Đã bầu <b>${voted_all}/${total_all}</b> (${pct}%) &nbsp;&nbsp; 🔴 Còn lại <b>${total_all - voted_all}/${total_all}</b>`;
  content.appendChild(summaryDiv);

  // per unit
  for(const dv in prog){
    const unitDiv = document.createElement('div');
    unitDiv.className = 'unit';
    const title = document.createElement('h3');
    title.textContent = dv;
    unitDiv.appendChild(title);

    const kvWrap = document.createElement('div');
    for(const kv in prog[dv]){
      const info = prog[dv][kv];
      const kvDiv = document.createElement('div');
      kvDiv.className = 'kv card';
      const canvas = document.createElement('canvas');
      const cid = 'c_'+dv.replace(/\s+/g,'_')+'_'+kv.replace(/\s+/g,'_')+'_'+Math.random().toString(36).slice(2,7);
      canvas.id = cid;
      const txt = document.createElement('div');
      txt.innerHTML = `<b>${kv}</b><br>Đã bầu: ${info.da_bau}/${info.tong} (${info.ty_le}%)<br>Còn lại: ${info.con_lai}/${info.tong}<br><small>(${info.cap_nhat || ''})</small>`;
      kvDiv.appendChild(canvas);
      kvDiv.appendChild(txt);
      kvWrap.appendChild(kvDiv);
      // draw chart
      const ctx = canvas.getContext('2d');
      new Chart(ctx, {
        type:'pie',
        data:{
          labels:['Đã bầu','Còn lại'],
          datasets:[{data:[info.da_bau||0, info.con_lai||0], backgroundColor:['#0074D9','#FF4136'] }]
        },
        options:{plugins:{legend:{display:false}},maintainAspectRatio:false}
      });
    }
    unitDiv.appendChild(kvWrap);
    content.appendChild(unitDiv);
  }

  document.getElementById('updated').textContent = 'Cập nhật: ' + new Date().toLocaleString();
}

async function loop(){
  const prog = await fetchStatus();
  render(prog || {});
}
loop();
setInterval(loop, 10000);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(DASH_HTML)

if __name__ == "__main__":
    # Port 5000 là chuẩn; Render sẽ chạy file này
    app.run(host="0.0.0.0", port=5000)
