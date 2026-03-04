from flask import Flask, jsonify, request
import time

app = Flask(__name__)

# 7 đơn vị cố định
DON_VI_LIST = [f"Đơn vị bầu cử số {i}" for i in range(1, 8)]
data = {dv: {} for dv in DON_VI_LIST}


@app.route("/api/update", methods=["POST"])
def update_data():
    """API nhận dữ liệu từ client"""
    payload = request.get_json(force=True)
    don_vi = payload.get("don_vi")
    khu_vuc = payload.get("khu_vuc")
    da_bau = int(payload.get("da_bau", 0))
    con_lai = int(payload.get("con_lai", 0))
    tong = int(payload.get("tong", da_bau + con_lai))
    ty_le = round(da_bau / tong * 100, 1) if tong else 0
    cap_nhat = time.strftime("%H:%M:%S")

    don_vi_name = f"Đơn vị bầu cử số {don_vi}"
    if don_vi_name not in data:
        data[don_vi_name] = {}

    data[don_vi_name][f"Khu vực {khu_vuc}"] = {
        "da_bau": da_bau,
        "con_lai": con_lai,
        "tong": tong,
        "ty_le": ty_le,
        "cap_nhat": cap_nhat,
    }

    return jsonify(
        {
            "status": "ok",
            "message": f"Đã cập nhật {don_vi_name} - Khu vực {khu_vuc}",
        }
    )


@app.route("/api/status")
def api_status():
    """API cho web hiển thị tiến độ"""
    return jsonify(data)


@app.route("/")
def index():
    """Giao diện tổng hợp"""
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
    body { font-family: Arial; background: #f6f9ff; margin: 0; }
    header { background: #b30000; color: #fff; text-align: center; padding: 10px; font-size: 22px; font-weight: bold; }
    .summary { background: #fff; margin: 12px auto; width: 95%; padding: 10px; text-align: center; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); font-size: 16px; }
    .unit { background: #fff; width: 95%; margin: 15px auto; padding: 10px 15px; border-radius: 8px; box-shadow: 0 0 6px rgba(0,0,0,0.1); }
    .unit h3 { margin: 8px 0; color: #b30000; font-size: 18px; }
    .kv-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
    .kv { background: #fafafa; border-radius: 8px; border: 1px solid #ddd; padding: 10px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .kv canvas { width: 120px; height: 120px; margin-bottom: 6px; }
    .footer { text-align: center; color: #777; font-size: 13px; margin: 20px 0; }
  </style>
</head>
<body>
  <header>UBBC XÃ TÂN BIÊN - TIẾN ĐỘ BỎ PHIẾU</header>
  <div id="content"></div>

<script>
async function fetchStatus(){
  const r = await fetch('/api/status');
  return await r.json();
}
function clearChildren(el){ while(el.firstChild) el.removeChild(el.firstChild); }

function render(prog){
  const content = document.getElementById('content');
  clearChildren(content);

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

  const donViList = ["Đơn vị bầu cử số 1","Đơn vị bầu cử số 2","Đơn vị bầu cử số 3","Đơn vị bầu cử số 4","Đơn vị bầu cử số 5","Đơn vị bầu cử số 6","Đơn vị bầu cử số 7"];
  for(const dv of donViList){
    const unitDiv = document.createElement('div');
    unitDiv.className = 'unit';
    const title = document.createElement('h3');
    title.textContent = dv;
    unitDiv.appendChild(title);

    const kvGrid = document.createElement('div');
    kvGrid.className = 'kv-grid';
    const dvData = prog[dv] || {};

    if(Object.keys(dvData).length === 0){
      const emptyDiv = document.createElement('div');
      emptyDiv.textContent = "(chưa có dữ liệu)";
      emptyDiv.style.color = "#888";
      kvGrid.appendChild(emptyDiv);
    } else {
      for(const kv in dvData){
        const info = dvData[kv];
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
          data: { labels: ['Đã bầu', 'Còn lại'], datasets: [{ data: [info.da_bau||0, info.con_lai||0], backgroundColor: ['#0074D9','#FF4136'] }] },
          options: { plugins: { legend: { display:false } }, cutout: '60%' }
        });
      }
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
