# 🌌 Holica AI — Uncensored Multi-Studio
### AI Chat (LLM) • Create Picture (Diffusion) • Create Video (AnimateDiff)
> **Fully Uncensored Web Studio powered by Google Colab GPU (NVIDIA T4 15GB VRAM)**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Google Colab](https://img.shields.io/badge/Google_Colab-T4_GPU-orange.svg)](https://colab.research.google.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 🌟 จุดเด่นของระบบ (Key Features)

1. **💬 Uncensored AI Chat (สนทนาแบบไร้ตัวกรอง)**:
   - ขับเคลื่อนด้วยโมเดล **Dolphin-Mistral 7B (GGUF Q4_K_M)** ผ่าน `llama-cpp-python` พร้อม GPU Offload
   - สนทนาได้ทุกเรื่อง ทั้ง Roleplay, นิยายผู้ใหญ่, บทความเชิงลึก และโค้ดดิ้ง ไร้การปฏิเสธ (Zero Refusals)
   - ส่งข้อความตอบกลับแบบ **Real-time SSE Streaming** (พิมพ์ทีละตัวอักษร)
   - มี Persona หลากหลาย: *Uncensored Assistant, Dark Storyteller, Affectionate Companion, Elite Hacker*

2. **🎨 Uncensored Image Studio (สร้างภาพแบบไร้ขีดจำกัด)**:
   - ใช้โมเดล **CyberRealistic / Realistic Vision (SD 1.5)** ปิด Safety Checker 100%
   - สร้างได้ทั้ง **Text-to-Image** และ **Image-to-Image**
   - มีปุ่มปรับสัดส่วนภาพอัตโนมัติ: จัตุรัส (1:1), แนวตั้ง (9:16), แนวนอน (16:9)
   - โหมดสไตล์ภาพ: *Photorealistic 8K, Anime & 2D, Cinematic Film, Raw Unfiltered*
   - ปุ่มลัด **"🎬 Animate into Video"** ส่งภาพที่เพิ่งเจนไปขยับเป็นคลิปวิดีโอต่อได้ในคลิกเดียว

3. **🎬 Uncensored Video Studio (สร้างคลิปวิดีโอสั้น)**:
   - ใช้โมเดล **AnimateDiff v3** สังเคราะห์การเคลื่อนไหวที่ลื่นไหล
   - รองรับ **Text-to-Video** และ **Image-to-Video**
   - กำหนดความยาวเฟรมได้ (8, 16, 24 เฟรม) พร้อมปรับความเร็ว FPS
   - เล่นวนลูปบนเว็บและดาวน์โหลดไฟล์ MP4 ได้ทันที

4. **⚡ Smart VRAM Manager สำหรับ Colab T4 (15.3 GB VRAM)**:
   - ระบบบริหารจัดการ Memory อัตโนมัติ สลับโมเดลและเคลียร์ CUDA Cache ไม่ให้เกิดปัญหา CUDA Out of Memory (OOM)

5. **🌐 Cloudflare Tunnel (One-Click Public URL)**:
   - ไม่ต้อง Forward Port ไม่ต้องสมัคร ngrok หรือกรอก Auth Token
   - ได้ URL ปลอดภัยแบบ HTTPS (เช่น `https://xxxx.trycloudflare.com`) เปิดใช้งานผ่านมือถือหรือคอมพิวเตอร์ได้ทันที

---

## 🚀 วิธีการใช้งานบน Google Colab (Step-by-Step)

### ขั้นตอนที่ 1: เปิด Colab Notebook
1. เข้าไปที่ [Google Colab](https://colab.research.google.com/)
2. อัปโหลดไฟล์ [`colab/holica_uncensored_colab.ipynb`](colab/holica_uncensored_colab.ipynb) ขึ้น Colab
3. ไปที่เมนู **Runtime** -> **Change runtime type** -> เลือก **T4 GPU** แล้วกด **Save**

### ขั้นตอนที่ 2: กดรันเซลล์
รันเซลล์ในโน้ตบุ๊กตามลำดับ:
1. **Step 1**: ตรวจสอบ GPU (พบ Tesla T4)
2. **Step 2**: ติดตั้ง Dependencies และ Cloudflare Tunnel
3. **Step 3**: รัน Holica AI Server

### ขั้นตอนที่ 3: เปิดใช้งาน Web Studio
เมื่อรัน Step 3 หน้าจอ Colab จะแสดงข้อความ:
```text
======================================================================
           HOLICA AI - UNCENSORED MULTI-STUDIO
      Chat (LLM) | Image (Diffusion) | Video (AnimateDiff)
======================================================================
 [GPU System]   : Tesla T4 (15.3 GB VRAM)
 [Local URL]    : http://127.0.0.1:8000
 [PUBLIC WEB URL]: https://random-subdomain.trycloudflare.com

 >>> Click or copy the PUBLIC WEB URL above to access the app! <<<
======================================================================
```
คลิกลิงก์ **`https://...trycloudflare.com`** เพื่อเริ่มใช้งานเว็บ AI Studio ได้ทันที!

---

## 💻 วิธีการรันในเครื่องตัวเอง (Local Development)

### 1. ติดตั้ง Dependencies
```bash
cd Holica
pip install -r backend/requirements.txt
```

### 2. รันเซิร์ฟเวอร์
```bash
python backend/run_colab.py
```
เปิดเบราว์เซอร์ไปที่: `http://localhost:8000`

### 3. รันการทดสอบ (Automated Tests)
```bash
pytest tests/test_backend_routes.py
```

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
Holica/
├── .gitignore
├── README.md
├── colab/
│   └── holica_uncensored_colab.ipynb       # Colab Notebook แบบ 1-Click
├── backend/
│   ├── requirements.txt                    # Python dependencies
│   ├── run_colab.py                        # Entrypoint script รันเซิร์ฟเวอร์ + Tunnel
│   ├── app/
│   │   ├── main.py                         # FastAPI App & Routing
│   │   ├── config.py                       # Configuration & Paths
│   │   ├── core/
│   │   │   └── vram_manager.py             # Smart GPU Memory & Cache Manager
│   │   ├── services/
│   │   │   ├── chat_service.py             # Uncensored LLM Chat Engine
│   │   │   ├── image_service.py            # Stable Diffusion (Safety Filter Off)
│   │   │   └── video_service.py            # AnimateDiff Video Synthesis
│   │   └── utils/
│   │       └── tunnel.py                   # Cloudflare Tunnel integration
│   └── static/                             # Web Frontend Assets สำหรับ Colab
│       ├── index.html
│       ├── css/style.css
│       └── js/{app,chat,image,video}.js
├── frontend/                               # Standalone Web App Source
│   ├── index.html
│   ├── css/style.css
│   └── js/{app,chat,image,video}.js
└── tests/
    └── test_backend_routes.py              # Automated Unit Tests
```

---

## 💡 ทริคป้องกัน Google Colab หลุด (Anti-Disconnect)

เมื่อใช้งาน Google Colab อาจมีการตัดการเชื่อมต่อหากไม่มีการกดหน้าเว็บนานๆ สามารถเปิด **Developer Console** (กด `F12` ในหน้าต่าง Colab) แล้วนำโค้ดนี้ไปวางใน Console แล้วกด `Enter`:

```javascript
function ClickConnect(){
    console.log("Holica: Keeping Colab session alive...");
    document.querySelector("colab-connect-button")?.click();
}
setInterval(ClickConnect, 60000);
```

---

## 🔒 ข้อกำหนดและลิขสิทธิ์
ซอฟต์แวร์นี้จัดทำขึ้นเพื่อการวิจัยและการใช้งานส่วนตัว (Creative & Personal Experimentation) ผู้ใช้งานควรตระหนักถึงกฎหมายและข้อบังคับในพื้นที่ของตนเองเกี่ยวกับการสร้างสื่อดิจิทัล
