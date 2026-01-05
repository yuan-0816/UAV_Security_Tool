"""
照片上傳伺服器模組
提供手機拍照上傳功能的 Flask 伺服器
"""

import os
import socket
import threading
import uuid
from datetime import datetime

from flask import Flask, request, jsonify, render_template_string
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn
from PySide6.QtCore import QObject, Signal


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """支援多執行緒的 WSGI Server"""

    daemon_threads = True


from constants import PHOTO_ANGLES_NAME

# ==============================================================================
# 手機端 HTML 模板
# ==============================================================================

MOBILE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
    <title>Photo Helper</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background: #f8f9fa; color: #333; overscroll-behavior-y: contain; }
        .container { max-width: 100%; padding: 15px; padding-bottom: 60px; box-sizing: border-box; }
        h3 { margin-top: 0; text-align: center; font-size: 1.2rem; }
        .btn { display: block; width: 100%; padding: 12px; margin: 8px 0; font-size: 16px; font-weight: bold; color: white; border: none; border-radius: 8px; cursor: pointer; text-align: center; }
        .btn-primary { background-color: #007bff; }
        .btn-success { background-color: #28a745; }
        .btn-danger { background-color: #dc3545; }
        .btn-secondary { background-color: #6c757d; }
        .btn-outline { background-color: transparent; border: 1px solid #666; color: #666; }
        .btn:disabled { background-color: #ccc; cursor: not-allowed; }
        .btn-row { display: flex; gap: 10px; margin-bottom: 10px; }
        .btn-row .btn { margin: 0; }
        select { width: 100%; padding: 10px; font-size: 16px; border-radius: 6px; border: 1px solid #ccc; background: white; margin-bottom: 15px; }
        .controls-panel { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; gap: 10px; }
        .control-item { display: flex; align-items: center; gap: 5px; font-size: 14px; font-weight: bold; }
        input[type="color"] { border: none; width: 40px; height: 35px; cursor: pointer; background: none; }
        input[type="range"] { width: 100px; }
        #step1-crop, #step2-draw { display: none; }
        .img-container { width: 100%; height: 55vh; background-color: #333; overflow: hidden; border-radius: 8px; margin-bottom: 10px; }
        #image-to-crop { max-width: 100%; display: block; }
        .canvas-wrapper { width: 100%; overflow: hidden; border: 2px solid #ddd; border-radius: 8px; background-color: #fff; margin-bottom: 10px; display: flex; justify-content: center; }
        #status { text-align: center; font-weight: bold; margin-bottom: 10px; color: #666; min-height: 20px; }
        .hint { font-size: 12px; color: #888; text-align: center; margin-bottom: 5px; }
    </style>
</head>
<body>
<div class="container">
    <h3 id="page-title">Loading...</h3>
    <div id="status"></div>
    <div id="step0-select">
        <div id="category-section" style="display:none;">
            <label>視角 (View):</label>
            <select id="category-select">
                <option value="front">正面 (Front)</option>
                <option value="back">背面 (Back)</option>
                <option value="side1">側面1 (Side 1)</option>
                <option value="side2">側面2 (Side 2)</option>
                <option value="top">上方 (Top)</option>
                <option value="bottom">下方 (Bottom)</option>
            </select>
        </div>
        <input type="file" id="file-input" accept="image/*" style="display:none;">
        <button class="btn btn-primary" onclick="document.getElementById('file-input').click()">📷 拍照或選取照片</button>
    </div>
    <div id="step1-crop">
        <div class="hint">請縮放或拖曳圖片以進行裁切</div>
        <div class="img-container"><img id="image-to-crop" src=""></div>
        <div class="btn-row">
            <button class="btn btn-secondary" onclick="resetAll()">取消</button>
            <button class="btn btn-primary" onclick="finishCrop()">下一步: 標記 ➡️</button>
        </div>
    </div>
    <div id="step2-draw">
        <div class="controls-panel">
            <div class="control-item">顏色: <input type="color" id="line-color" value="#ff0000"></div>
            <div class="control-item">粗細: <input type="range" id="line-width" min="1" max="15" value="5"><span id="width-val">5</span></div>
        </div>
        <div class="canvas-wrapper"><canvas id="fabric-canvas"></canvas></div>
        <div class="btn-row">
            <button class="btn btn-danger" onclick="addRect()">+ 加入框線</button>
            <button class="btn btn-outline" onclick="removeActiveObject()">刪除選取</button>
        </div>
        <div class="btn-row" style="margin-top: 20px;">
            <button class="btn btn-secondary" onclick="backToCrop()">⬅️ 重裁</button>
            <button class="btn btn-success" id="btn-upload" onclick="uploadResult()">☁️ 確認上傳</button>
        </div>
    </div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
<script>
    const UPLOAD_TOKEN = "{{ token }}";
    const TARGET_NAME = "{{ target_name }}";
    const IS_REPORT_MODE = {{ 'true' if is_report else 'false' }};
    const statusEl = document.getElementById('status');
    const step0 = document.getElementById('step0-select');
    const step1 = document.getElementById('step1-crop');
    const step2 = document.getElementById('step2-draw');
    const imgElement = document.getElementById('image-to-crop');
    const colorInput = document.getElementById('line-color');
    const widthInput = document.getElementById('line-width');
    const widthVal = document.getElementById('width-val');
    document.getElementById('page-title').innerText = TARGET_NAME;
    if (IS_REPORT_MODE) { document.getElementById('category-section').style.display = 'block'; }
    let cropper = null; let fabricCanvas = null; let originalImageWidth = 0;
    widthInput.addEventListener('input', function() { widthVal.innerText = this.value; updateActiveObject(); });
    colorInput.addEventListener('input', function() { updateActiveObject(); });
    function updateActiveObject() { if (!fabricCanvas) return; const activeObj = fabricCanvas.getActiveObject(); if (activeObj) { activeObj.set({ stroke: colorInput.value, strokeWidth: parseInt(widthInput.value, 10) }); fabricCanvas.requestRenderAll(); } }
    document.getElementById('file-input').addEventListener('change', function(e) { const file = e.target.files[0]; if (file) { statusEl.innerText = "讀取中..."; const reader = new FileReader(); reader.onload = function(evt) { imgElement.src = evt.target.result; startCropMode(); statusEl.innerText = ""; }; reader.readAsDataURL(file); } this.value = ''; });
    function startCropMode() { step0.style.display = 'none'; step1.style.display = 'block'; step2.style.display = 'none'; if (cropper) { cropper.destroy(); } setTimeout(() => { cropper = new Cropper(imgElement, { viewMode: 1, dragMode: 'move', autoCropArea: 0.9, restore: false, guides: true, center: true, highlight: false, cropBoxMovable: true, cropBoxResizable: true, toggleDragModeOnDblclick: false, }); }, 100); }
    function finishCrop() { if (!cropper) return; statusEl.innerText = "處理中..."; const croppedCanvas = cropper.getCroppedCanvas({ maxWidth: 4096, maxHeight: 4096, imageSmoothingQuality: 'high', }); if (!croppedCanvas) { alert("裁切失敗"); return; } originalImageWidth = croppedCanvas.width; const croppedImageURL = croppedCanvas.toDataURL('image/jpeg', 0.95); startDrawMode(croppedImageURL, croppedCanvas.width, croppedCanvas.height); }
    function startDrawMode(imageURL, w, h) { step1.style.display = 'none'; step2.style.display = 'block'; statusEl.innerText = ""; const containerWidth = document.querySelector('.container').clientWidth - 34; const scaleFactor = containerWidth / w; const finalWidth = containerWidth; const finalHeight = h * scaleFactor; if (fabricCanvas) { fabricCanvas.dispose(); } const canvasEl = document.getElementById('fabric-canvas'); canvasEl.width = finalWidth; canvasEl.height = finalHeight; fabricCanvas = new fabric.Canvas('fabric-canvas', { width: finalWidth, height: finalHeight, selection: false }); fabric.Image.fromURL(imageURL, function(img) { img.set({ originX: 'left', originY: 'top', scaleX: scaleFactor, scaleY: scaleFactor, selectable: false }); fabricCanvas.setBackgroundImage(img, fabricCanvas.renderAll.bind(fabricCanvas)); addRect(); }); fabricCanvas.on('selection:created', syncControls); fabricCanvas.on('selection:updated', syncControls); }
    function syncControls(e) { const obj = e.selected[0]; if (obj) { colorInput.value = obj.stroke; widthInput.value = obj.strokeWidth; widthVal.innerText = obj.strokeWidth; } }
    function addRect() { if (!fabricCanvas) return; const rect = new fabric.Rect({ left: fabricCanvas.width / 4, top: fabricCanvas.height / 4, width: fabricCanvas.width / 3, height: fabricCanvas.height / 3, fill: 'transparent', stroke: colorInput.value, strokeWidth: parseInt(widthInput.value, 10), cornerColor: 'blue', cornerSize: 20, transparentCorners: false, strokeUniform: true }); fabricCanvas.add(rect); fabricCanvas.setActiveObject(rect); }
    function removeActiveObject() { const activeObj = fabricCanvas.getActiveObject(); if (activeObj) { fabricCanvas.remove(activeObj); } }
    function backToCrop() { step2.style.display = 'none'; step1.style.display = 'block'; }
    function resetAll() { if (confirm("重新選取照片？")) { step1.style.display = 'none'; step2.style.display = 'none'; step0.style.display = 'block'; if (cropper) cropper.destroy(); cropper = null; document.getElementById('file-input').value = ''; } }
    function uploadResult() { if (!fabricCanvas) return; fabricCanvas.discardActiveObject(); fabricCanvas.renderAll(); const multiplier = originalImageWidth / fabricCanvas.getWidth(); const dataURL = fabricCanvas.toDataURL({ format: 'jpeg', quality: 1.0, multiplier: multiplier }); statusEl.innerText = "上傳中..."; document.getElementById('btn-upload').disabled = true; const blob = dataURLtoBlob(dataURL); const formData = new FormData(); formData.append('photo', blob, 'upload.jpg'); formData.append('token', UPLOAD_TOKEN); if (IS_REPORT_MODE) { formData.append('category', document.getElementById('category-select').value); } fetch('/upload_endpoint', { method: 'POST', body: formData }).then(response => response.json()).then(data => { if (data.status === 'success') { statusEl.innerText = "✅ 成功"; statusEl.style.color = "green"; setTimeout(() => { alert("上傳成功！"); resetToStart(); }, 500); } else { alert("失敗: " + data.message); statusEl.innerText = ""; document.getElementById('btn-upload').disabled = false; } }).catch(err => { alert("網路錯誤"); statusEl.innerText = ""; document.getElementById('btn-upload').disabled = false; }); }
    function resetToStart() { step1.style.display = 'none'; step2.style.display = 'none'; step0.style.display = 'block'; statusEl.innerText = ""; document.getElementById('btn-upload').disabled = false; document.getElementById('file-input').value = ''; }
    function dataURLtoBlob(dataurl) { var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1], bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n); while(n--){ u8arr[n] = bstr.charCodeAt(n); } return new Blob([u8arr], {type:mime}); }
</script>
</body>
</html>
"""


# ==============================================================================
# PhotoServer 類別
# ==============================================================================


class PhotoServer(QObject):
    """照片上傳伺服器 - 提供手機拍照上傳功能"""

    photo_received = Signal(str, str, str)  # target_id, category, full_path

    def __init__(self, port=8000):
        super().__init__()
        self.app = Flask(__name__)
        self.port = port
        self.save_dir = ""
        self.active_tokens = {}
        self.server = None
        self.server_thread = None
        self.app.add_url_rule(
            "/upload", "upload_page", self.upload_page, methods=["GET"]
        )
        self.app.add_url_rule(
            "/upload_endpoint",
            "upload_endpoint",
            self.upload_endpoint,
            methods=["POST"],
        )

    def start(self):
        if self.server is not None:
            return
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
            except Exception as e:
                print(f"Error stopping server: {e}")
        if self.server_thread:
            self.server_thread.join(timeout=1.0)
            self.server_thread = None

    def _run_server(self):
        try:
            # 使用 ThreadingWSGIServer 支援多執行緒
            self.server = make_server(
                "0.0.0.0", self.port, self.app, server_class=ThreadingWSGIServer
            )
            self.server.serve_forever()
        except OSError as e:
            print(f"Web Server Error: {e}")
        except Exception as e:
            print(f"Web Server Start Failed: {e}")
        finally:
            # 確保 Socket 被正確關閉釋放
            if self.server:
                self.server.server_close()
            self.server = None

    def is_running(self):
        return self.server is not None

    def set_save_directory(self, path):
        self.save_dir = path
        if path and not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    def generate_token(self, target_id, target_name, is_report=False):
        token = str(uuid.uuid4())[:8]
        self.active_tokens[token] = {
            "id": target_id,
            "name": target_name,
            "is_report": is_report,
            "timestamp": datetime.now(),
        }
        return token

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def upload_page(self):
        token = request.args.get("token")
        if token not in self.active_tokens:
            return "連結已失效或錯誤", 404
        data = self.active_tokens[token]
        return render_template_string(
            MOBILE_HTML_TEMPLATE,
            token=token,
            target_name=data["name"],
            is_report=data["is_report"],
        )

    def upload_endpoint(self):
        token = request.form.get("token")
        if token not in self.active_tokens:
            return jsonify({"status": "error", "message": "無效 Token"}), 400
        file = request.files.get("photo")
        if not file:
            return jsonify({"status": "error", "message": "無檔案"}), 400
        task_info = self.active_tokens[token]
        category = request.form.get("category", "default")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_id = task_info["id"].replace(".", "_")
        filename = f"{safe_id}_{category}_{ts}.jpg"
        if not self.save_dir:
            return jsonify({"status": "error", "message": "伺服器儲存路徑未設定"}), 500
        save_path = os.path.join(self.save_dir, filename)
        try:
            file.save(save_path)
            self.photo_received.emit(task_info["id"], category, save_path)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
