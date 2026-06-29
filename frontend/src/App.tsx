import { useState, useEffect, useRef } from 'react';
import './index.css';

const API = 'http://127.0.0.1:7875';

const TASKS = [
  { id: 'create', name: 'New Image', icon: '✨', desc: 'Generate from description' },
  { id: 'face', name: 'Portrait', icon: '👤', desc: 'Keep face, new scene' },
  { id: 'pose', name: 'Pose', icon: '🕺', desc: 'Transfer to new pose' },
  { id: 'wardrobe', name: 'Wardrobe', icon: '👗', desc: 'Change clothing' },
  { id: 'retouch', name: 'Retouch', icon: '🎨', desc: 'Edit body/skin' },
  { id: 'refine', name: 'Refine', icon: '🔧', desc: 'Vary or upscale' },
];

const RATIOS = [
  { label: '1:1', w: 1024, h: 1024 },
  { label: '9:16', w: 576, h: 1024, hint: 'Mobile portrait' },
  { label: '16:9', w: 1024, h: 576, hint: 'Widescreen' },
  { label: '2:3', w: 768, h: 1344, hint: 'Portrait' },
  { label: '3:2', w: 1344, h: 768, hint: 'Landscape' },
  { label: '3:4', w: 1024, h: 1344, hint: 'Portrait' },
  { label: '4:3', w: 1344, h: 1024, hint: 'Landscape' },
];

export default function App() {
  const [task, setTask] = useState('create');
  const [prompt, setPrompt] = useState('');
  const [width, setWidth] = useState(1024);
  const [height, setHeight] = useState(1024);
  const [steps, setSteps] = useState(25);
  const [cfg, setCfg] = useState(7);
  const [seed, setSeed] = useState(-1);
  const [anatomy, setAnatomy] = useState(false);
  const [model, setModel] = useState('juggernautXL_v8Rundiffusion.safetensors');
  const [models, setModels] = useState([]);
  const [loras, setLoras] = useState([]);
  const [lora, setLora] = useState('None');
  const [loraStrength, setLoraStrength] = useState(1.0);
  const [refImage, setRefImage] = useState('');
  const [poseImage, setPoseImage] = useState('');
  const [maskImage, setMaskImage] = useState('');
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Ready');
  const [resultUrl, setResultUrl] = useState('');
  const [backendReady, setBackendReady] = useState(false);
  const pollRef = useRef(null);

  // Detect body keywords for UI feedback
  const BODY_KEYWORDS = ['full body', 'head to toe', 'feet', 'legs', 'nude', 'naked', 'topless', 'breasts', 'nipples', 'vagina', 'pussy', 'genitals', 'shaved', 'trimmed', 'pubic hair', 'dildo', 'masturbating'];
  const hasBodyKeywords = BODY_KEYWORDS.some(kw => prompt.toLowerCase().includes(kw));

  useEffect(() => {
    fetch(`${API}/api/health`).then(r => r.json()).then(d => setBackendReady(d.comfyui)).catch(() => setBackendReady(false));
    fetch(`${API}/api/models`).then(r => r.json()).then(d => { if (d.length) setModels(d); }).catch(() => {});
    fetch(`${API}/api/loras`).then(r => r.json()).then(d => setLoras(d || [])).catch(() => setLoras([]));
  }, []);

  const needsRef = task !== 'create';
  const needsPose = task === 'pose';
  const needsMask = task === 'wardrobe' || task === 'retouch';

  const upload = async (file, setter) => {
    const f = new FormData();
    f.append('file', file);
    const r = await fetch(`${API}/api/upload`, { method: 'POST', body: f });
    const d = await r.json();
    setter(d.filename);
  };

  const generate = async () => {
    if (!prompt.trim()) return;
    if (needsRef && !refImage) { alert('Upload reference image'); return; }
    if (needsPose && !poseImage) { alert('Upload pose image'); return; }
    if (needsMask && !maskImage) { alert('Upload mask'); return; }

    setGenerating(true);
    setProgress(0);
    setResultUrl('');
    setStatus('Submitting...');

    const f = new FormData();
    f.append('task', task);
    f.append('prompt', prompt);
    f.append('width', String(width));
    f.append('height', String(height));
    f.append('steps', String(steps));
    f.append('cfg', String(cfg));
    f.append('seed', String(seed));
    f.append('model', model);
    f.append('anatomy', String(anatomy));
    if (lora && lora !== 'None') {
      f.append('lora', lora);
      f.append('lora_strength', String(loraStrength));
    }
    if (refImage) f.append('reference_image', refImage);
    if (poseImage) f.append('pose_image', poseImage);
    if (maskImage) f.append('mask_image', maskImage);

    try {
      const r = await fetch(`${API}/api/generate`, { method: 'POST', body: f });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Failed');
      const jobId = d.job_id;
      setStatus('Generating...');

      pollRef.current = setInterval(async () => {
        const pr = await fetch(`${API}/api/progress/${jobId}`);
        const pd = await pr.json();
        if (pd.status === 'completed') {
          setProgress(100);
          setStatus('Done');
          clearInterval(pollRef.current);
          const rr = await fetch(`${API}/api/result/${jobId}`);
          const blob = await rr.blob();
          setResultUrl(URL.createObjectURL(blob));
          setGenerating(false);
        } else if (pd.error) {
          setStatus('Error: ' + pd.error);
          clearInterval(pollRef.current);
          setGenerating(false);
        } else {
          setProgress(Math.round((pd.progress / 100) * 100) || 5);
          setStatus('Generating...');
        }
      }, 1500);
    } catch (e) {
      setStatus('Error: ' + e.message);
      setGenerating(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="logo">◈</span>
          <div>
            <h1>Studio Pro</h1>
            <span className="tagline">Portrait & Image Editor</span>
          </div>
        </div>
        <div className={`status ${backendReady ? 'ok' : 'down'}`}>
          {backendReady ? 'Ready' : 'Offline'}
        </div>
      </header>

      <div className="layout">
        <nav className="sidebar">
          <div className="section">Create</div>
          {TASKS.filter(t => t.id === 'create').map(t => (
            <button key={t.id} className={task === t.id ? 'active' : ''} onClick={() => setTask(t.id)}>
              <span>{t.icon}</span><div><b>{t.name}</b><small>{t.desc}</small></div>
            </button>
          ))}
          <div className="section" style={{marginTop:16}}>Edit</div>
          {TASKS.filter(t => t.id !== 'create').map(t => (
            <button key={t.id} className={task === t.id ? 'active' : ''} onClick={() => setTask(t.id)}>
              <span>{t.icon}</span><div><b>{t.name}</b><small>{t.desc}</small></div>
            </button>
          ))}
        </nav>

        <main className="editor">
          <h2>{TASKS.find(t => t.id === task)?.name}</h2>
          <p className="sub">{TASKS.find(t => t.id === task)?.desc}</p>

          {needsRef && <DropZone label="Reference Image" onFile={f => upload(f, setRefImage)} name={refImage} />}
          {needsPose && <DropZone label="Pose Reference" onFile={f => upload(f, setPoseImage)} name={poseImage} />}
          {needsMask && <DropZone label="Mask (white = edit area)" onFile={f => upload(f, setMaskImage)} name={maskImage} />}

          <div className="field">
            <label>Description</label>
            <textarea rows={3} value={prompt} onChange={e => setPrompt(e.target.value)} placeholder={task === 'create' ? 'Describe the image you want to create...' : 'Describe what you want to change...'} />
            {hasBodyKeywords && <div className="tag body">Full body detected — anti-crop enabled</div>}
            {task === 'pose' && <div className="tag hint">Upload a person photo and a pose reference. The person keeps their face, body takes the new pose.</div>}
            {task === 'face' && <div className="tag hint">Upload a face photo. The person keeps their face, everything else changes to match your description.</div>}
            {task === 'wardrobe' && <div className="tag hint">Upload a photo and a mask (white = area to change). Describe the new clothing.</div>}
            {task === 'retouch' && <div className="tag hint">Upload a photo and a mask (white = area to edit). Describe the retouch you want.</div>}
            {task === 'refine' && <div className="tag hint">Upload a photo to refine, vary, or upscale.</div>}
          </div>

          <div className="field">
            <label>Model</label>
            <select value={model} onChange={e => setModel(e.target.value)}>
              {models.map(m => <option key={m} value={m}>{m.replace('.safetensors', '')}</option>)}
            </select>
          </div>

          {loras.length > 0 && (
            <>
              <div className="field">
                <label>LoRA</label>
                <select value={lora} onChange={e => setLora(e.target.value)}>
                  <option value="None">None</option>
                  {loras.map(l => <option key={l} value={l}>{l.replace('.safetensors', '')}</option>)}
                </select>
              </div>
              {lora !== 'None' && (
                <div className="field row">
                  <label>LoRA Strength: {loraStrength.toFixed(1)}</label>
                  <input type="range" min={0.1} max={2.0} step={0.1} value={loraStrength} onChange={e => setLoraStrength(Number(e.target.value))} />
                </div>
              )}
            </>
          )}

          <div className="field">
            <label>Aspect Ratio</label>
            <div className="ratios">
              {RATIOS.map(r => (
                <button key={r.label} className={width === r.w && height === r.h ? 'active' : ''} onClick={() => { setWidth(r.w); setHeight(r.h); }} title={`${r.w}x${r.h}${r.hint ? ' - ' + r.hint : ''}`}>
                  {r.label}
                </button>
              ))}
            </div>
          </div>

          <div className="field row">
            <label>Steps: {steps}</label>
            <input type="range" min={15} max={50} value={steps} onChange={e => setSteps(Number(e.target.value))} />
          </div>

          <div className="field row">
            <label>Guidance: {cfg}</label>
            <input type="range" min={3} max={12} step={0.5} value={cfg} onChange={e => setCfg(Number(e.target.value))} />
          </div>

          <div className="field row">
            <label>Seed</label>
            <input type="number" value={seed} onChange={e => setSeed(Number(e.target.value))} style={{width:100}} />
            <button className="icon" onClick={() => setSeed(-1)} title="Random">🎲</button>
          </div>

          <div className="field">
            <label className="check">
              <input type="checkbox" checked={anatomy} onChange={e => setAnatomy(e.target.checked)} />
              Enhanced realism (natural skin texture)
            </label>
          </div>

          <button className="generate" onClick={generate} disabled={generating || !backendReady}>
            {generating ? 'Generating...' : '✨ Generate'}
          </button>
        </main>

        <aside className="preview">
          <h3>Preview</h3>
          <div className="canvas">
            {!resultUrl && !generating && <div className="placeholder"><span>🖼️</span><div>Images appear here</div></div>}
            {resultUrl && <img src={resultUrl} alt="Result" />}
            {generating && (
              <div className="progress">
                <div className="bar" style={{width: `${progress}%`}} />
                <span>{status}</span>
              </div>
            )}
          </div>
          {resultUrl && (
            <div className="actions">
              <button onClick={() => { setRefImage(''); setResultUrl(''); setTask('refine'); }}>Refine</button>
              <button onClick={() => { const a = document.createElement('a'); a.href = resultUrl; a.download = `studiopro_${Date.now()}.png`; a.click(); }}>Save</button>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function DropZone({ label, onFile, name }) {
  const inputRef = useRef(null);
  return (
    <div className="dropzone" onClick={() => inputRef.current?.click()}>
      <input ref={inputRef} type="file" accept="image/*" hidden onChange={e => e.target.files?.[0] && onFile(e.target.files[0])} />
      {!name ? <><span>📷</span><div>{label}<small>Click or drop</small></div></> : <span>{name}</span>}
    </div>
  );
}
