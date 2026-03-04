from flask import Flask, jsonify
import time

app = Flask(__name__)

# Dữ liệu mẫu: bạn có thể cập nhật từ client gửi về thực tế
# Cấu trúc: { "Đơn vị bầu cử số 1": { "Khu vực 1": {...}, ... }, ... }
data = {
    "Đơn vị bầu cử số 1": {
        "Khu vực 1": {"da_bau": 220, "con_lai": 30, "tong": 250, "ty_le": 88, "cap_nhat": "09:30"},
        "Khu vực 2": {"da_bau": 180, "con_lai": 70, "tong": 250, "ty_le": 72, "cap_nhat": "09:31"},
        "Khu vực 3": {"da_bau": 190, "con_lai": 60, "tong": 250, "ty_le": 76, "cap_nhat": "09:33"},
        "Khu vực 4": {"da_bau": 230, "con_lai": 20, "tong": 250, "ty_le": 92, "cap_nhat": "09:35"},
    },
    "Đơn vị bầu cử số 2": {
        "Khu vực 5": {"da_bau": 200, "con_lai": 50, "tong": 250, "ty_le": 80, "cap_nhat": "09:36"},
        "Khu vực 6": {"da_bau": 150, "con_lai": 100, "tong": 250, "ty_le": 60, "cap_nhat": "09:38"},
    },
    "Đơn vị bầu cử số 3": {
        "Khu vực 7": {"da_bau": 160, "con_lai": 90, "tong": 250, "ty_le": 64, "cap_nhat": "09:40"},
        "Khu vực 8": {"da_bau": 210, "con_lai": 40, "tong": 250, "ty_le": 84, "cap_nhat": "09:41"},
    },
    "Đơn vị bầu cử số 4": {
        "Khu vực 9": {"da_bau": 140, "con_lai": 110, "tong": 250, "ty_le": 56, "cap_nhat": "09:42"},
        "Khu vực 10": {"da_bau": 220, "con_lai": 30, "tong": 250, "ty_le": 88, "cap_nhat": "09:44"},
    },
    "Đơn vị bầu cử số 5": {
        "Khu vực 11": {"da_bau": 230, "con_lai": 20, "tong": 250, "ty_le": 92, "cap_nhat": "09:45"},
        "Khu vực 12": {"da_bau": 180, "con_lai": 70, "tong": 250, "ty_le": 72, "cap_nhat": "09:46"},
    },
    "Đơn vị bầu cử số 6": {
        "Khu vực 13": {"da_bau": 200, "con_lai": 50, "tong": 250, "ty_le": 80, "cap_nhat": "09:47"},
        "Khu vực 14": {"da_bau": 190, "con_lai": 60, "tong": 250, "ty_le": 76, "cap_nhat": "09:48"},
    },
    "Đơn vị bầu cử số 7": {
        "Khu vực 15": {"da_bau": 180, "con_lai": 70, "tong": 250, "ty_le": 72, "cap_nhat": "09:49"},
        "Khu vực 16": {"da_bau": 170, "con_lai": 80, "tong": 250, "ty_le": 68, "cap_nhat": "09:50"},
    },
}


@app.route("/api/status")
def api_status():
    return jsonify(data)


@app.route("/")
def index():
    return DASH_HTML


DASH_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>UBBC XÃ TÂN BIÊN - TỔNG QUAN</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {
      font-family: Arial, Helvetica, sans-serif;
      background: #f6f9ff;
      margin: 0;
      padding: 0;
    }
    header {
      background: #b30000;
      color: #fff;
      padding: 10px 16px;
      text-align: center;
      font-size: 22px;
      font-weight: bold;
    }
    .summary {
      background: #fff;
      margin: 12px auto;
      width: 95%;
      padding: 10px;
      text-align: center;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      font-size: 16px;
    }
    .unit {
      background: #fff;
      width: 95%;
      margin: 15px auto;
      padding: 10px 15px;
      border-radius: 8px;
      box-shadow: 0 0 6px rgba(0,0,0,0.1);
    }
    .unit h3 {
      margin: 8px 0;
      color: #b30000;
      font-size: 18px;
    }
    .kv-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 10px;
    }
    .kv {
      background: #fafafa;
      border-radius: 8px;
      border: 1px solid #ddd;
      padding: 10px;
      text-align: center;
      box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .kv canvas {
      width: 120px;
      height: 120px;
      margin-bottom: 6px;
    }
    .footer {
      text-align: center;
      color: #777;
      font-size: 13px;
      margin: 20px 0;
    }
  </style>
</head>
<body>
  <header>UBBC XÃ TÂN BIÊN - TIẾN ĐỘ BỎ PHIẾU</header>
  <div id="content"></div>

<script>
async function fetchStatus(){
  try {
    const r = await fetch('/api/status');
    return await r.json();
  } catch(e){
    console.error(e);
    return {};
  }
}

function clearChildren(el){ while(el.firstChild) el.removeChild(el.firstChild); }

function render(prog){
  const content = document.getElementById('content');
  clearChildren(content);

  // Tổng toàn xã
  let total_all = 0, voted_all = 0;
  for(const dv in prog){
    for(const kv in prog[dv]){
      total_all += (prog[dv][kv].tong || 0);
      voted_all += (prog[dv][kv].da_bau || 0);
    }
  }
  const pct = total_all ? (voted_all/total_all*100).toFixed(1) : 0;
  const summaryDiv = document.createElement('div');
  summaryDiv.className = 'summary';
  summaryDiv.innerHTML = `<b>🔵 Tổng toàn xã:</b> Đã bầu <b>${voted_all}/${total_all}</b> (${pct}%) &nbsp;&nbsp; 🔴 Còn lại: <b>${total_all - voted_all}/${total_all}</b>`;
  content.appendChild(summaryDiv);

  // Theo đơn vị
  for(const dv in prog){
    const unitDiv = document.createElement('div');
    unitDiv.className = 'unit';
    const title = document.createElement('h3');
    title.textContent = dv;
    unitDiv.appendChild(title);

    const kvGrid = document.createElement('div');
    kvGrid.className = 'kv-grid';

    for(const kv in prog[dv]){
      const info = prog[dv][kv];
      const kvDiv = document.createElement('div');
      kvDiv.className = 'kv';
      const canvas = document.createElement('canvas');
      const cid = 'c_'+dv.replace(/\\s+/g,'_')+'_'+kv.replace(/\\s+/g,'_')+'_'+Math.random().toString(36).slice(2,7);
      canvas.id = cid;
      const txt = document.createElement('div');
      txt.innerHTML = `<b>${kv}</b><br>Đã bầu: ${info.da_bau}/${info.tong} (${info.ty_le}%)<br>Còn lại: ${info.con_lai}/${info.tong}<br><small>${info.cap_nhat || ''}</small>`;
      kvDiv.appendChild(canvas);
      kvDiv.appendChild(txt);
      kvGrid.appendChild(kvDiv);

      const ctx = canvas.getContext('2d');
      new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['Đã bầu', 'Còn lại'],
          datasets: [{
            data: [info.da_bau||0, info.con_lai||0],
            backgroundColor: ['#0074D9','#FF4136']
          }]
        },
        options: { plugins: { legend: { display:false } }, cutout: '60%' }
      });
    }

    unitDiv.appendChild(kvGrid);
    content.appendChild(unitDiv);
  }

  const footer = document.createElement('div');
  footer.className = 'footer';
  footer.textContent = 'Cập nhật: ' + new Date().toLocaleString();
  content.appendChild(footer);
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
