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

const UPSCALES = [
  { label: 'Off', value: 1.0 },
  { label: '1.5x', value: 1.5 },
  { label: '2.0x', value: 2.0 },
];

const BODY_FEATURES = [
  { id: 'large_areolas', label: 'Large areolas', pos: 'large areolas, prominent nipples, natural nipple detail', neg: 'small areolas, tiny nipples' },
  { id: 'sagging', label: 'Natural sagging', pos: 'sagging natural breasts, breast ptosis, soft pendulous tissue, gravity-affected', neg: 'perky, lifted, firm, silicone, implants' },
  { id: 'uneven', label: 'Slightly uneven', pos: 'slightly asymmetrical breasts, one breast larger, natural unevenness', neg: 'symmetrical, perfectly matched, identical breasts' },
  { id: 'mature', label: 'Mature / aged', pos: 'mature woman, aged soft skin, natural aging, lived-in body', neg: 'young, teen, youthful, smooth flawless skin' },
  { id: 'veins', label: 'Visible veins', pos: 'visible veins on breasts, translucent skin, vascular detail', neg: 'smooth skin, no veins, opaque skin' },
  { id: 'stretch_marks', label: 'Stretch marks', pos: 'stretch marks on skin, natural skin texture, lived-in body', neg: 'flawless skin, perfect smooth skin, no blemishes' },
];

const SESSION_KEY = 'studiopro_last_session';

function getStageText(progress: number, status: string) {
  if (status === 'error') return 'Failed';
  if (progress < 5) return 'Submitting...';
  if (progress < 15) return 'Loading model...';
  if (progress < 85) return `Generating... ${progress}%`;
  if (progress < 100) return 'Finalizing...';
  return 'Done';
}

export default function App() {
  const [task, setTask] = useState('create');
  const [prompt, setPrompt] = useState('');
  const [width, setWidth] = useState(1024);
  const [height, setHeight] = useState(1024);
  const [steps, setSteps] = useState(25);
  const [cfg, setCfg] = useState(7);
  const [seed, setSeed] = useState(-1);
  const seedRef = useRef(seed);
  useEffect(() => { seedRef.current = seed; }, [seed]);
  const [anatomy, setAnatomy] = useState(false);
  const [realism, setRealism] = useState(false);
  const [features, setFeatures] = useState<Record<string, boolean>>({});
  const [model, setModel] = useState('juggernautXL_v8Rundiffusion.safetensors');
  const [models, setModels] = useState<string[]>([]);
  const [loras, setLoras] = useState<string[]>([]);
  const [loraSlots, setLoraSlots] = useState<{ name: string; strength: number }[]>([
    { name: 'None', strength: 1.0 },
    { name: 'None', strength: 1.0 },
    { name: 'None', strength: 1.0 },
  ]);
  const [upscale, setUpscale] = useState(1.0);
  const [refImage, setRefImage] = useState('');
  const [refPreview, setRefPreview] = useState('');
  const [poseImage, setPoseImage] = useState('');
  const [posePreview, setPosePreview] = useState('');
  const [maskImage, setMaskImage] = useState('');
  const [maskPreview, setMaskPreview] = useState('');
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Ready');
  const [resultUrl, setResultUrl] = useState('');
  const [resultMeta, setResultMeta] = useState<any>(null);
  const [backendReady, setBackendReady] = useState(false);
  const [lastSession, setLastSession] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const pollRef = useRef<number | null>(null);

  const PORTRAIT_KEYWORDS = ['close up', 'close-up', 'portrait', 'headshot', 'face only', 'upper body', 'bust', 'torso', 'waist up', 'chest up', 'shoulders up', 'head and shoulders', 'profile', 'selfie'];
  const isPortrait = PORTRAIT_KEYWORDS.some(kw => prompt.toLowerCase().includes(kw));

  useEffect(() => {
    fetch(`${API}/api/health`).then(r => r.json()).then(d => setBackendReady(d.comfyui)).catch(() => setBackendReady(false));
    fetch(`${API}/api/models`).then(r => r.json()).then(d => { if (Array.isArray(d) && d.length) setModels(d); }).catch(() => {});
    fetch(`${API}/api/loras`).then(r => r.json()).then(d => setLoras(d || [])).catch(() => setLoras([]));
    loadHistory();

    const saved = localStorage.getItem(SESSION_KEY);
    if (saved) {
      try {
        setLastSession(JSON.parse(saved));
      } catch {}
    }
  }, []);

  const toggleFeature = (id: string) => {
    setFeatures(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const buildPrompt = () => {
    let positive = prompt.trim();
    let negative = '';

    if (realism) {
      positive += positive ? ', ' : '';
      positive += 'natural imperfect body, realistic proportions, amateur photography, unposed, candid, authentic skin, no makeup, no retouching';
      negative += 'perfect body, idealized, symmetrical, centerfold, playboy, glamour, magazine retouch, smooth skin, botox, implants, plastic surgery, barbie, doll, mannequin';
    }

    BODY_FEATURES.forEach(f => {
      if (features[f.id]) {
        if (f.pos) positive += positive ? ', ' + f.pos : f.pos;
        if (f.neg) negative += negative ? ', ' + f.neg : f.neg;
      }
    });

    return { positive, negative };
  };

  const activeLoras = () => loraSlots.filter(s => s.name && s.name !== 'None');

  const loadHistory = async () => {
    try {
      const r = await fetch(`${API}/api/history`);
      const d = await r.json();
      setHistory(d.history || []);
    } catch {}
  };

  const upload = async (file: File, setter: (name: string) => void, previewSetter: (url: string) => void) => {
    previewSetter(URL.createObjectURL(file));
    const f = new FormData();
    f.append('file', file);
    const r = await fetch(`${API}/api/upload`, { method: 'POST', body: f });
    const d = await r.json();
    setter(d.filename);
  };

  const saveSession = () => {
    const session = {
      task, prompt, width, height, steps, cfg, seed, anatomy, realism, features, model,
      loraSlots, upscale, refImage, poseImage, maskImage,
    };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    setLastSession(session);
  };

  const restoreSession = () => {
    if (!lastSession) return;
    setTask(lastSession.task || 'create');
    setPrompt(lastSession.prompt || '');
    setWidth(lastSession.width || 1024);
    setHeight(lastSession.height || 1024);
    setSteps(lastSession.steps || 25);
    setCfg(lastSession.cfg || 7);
    setSeed(lastSession.seed ?? -1);
    setAnatomy(lastSession.anatomy || false);
    setRealism(lastSession.realism || false);
    setFeatures(lastSession.features || {});
    setModel(lastSession.model || model);
    if (lastSession.loraSlots) setLoraSlots(lastSession.loraSlots);
    setUpscale(lastSession.upscale ?? 1.0);
    setRefImage(lastSession.refImage || '');
    setPoseImage(lastSession.poseImage || '');
    setMaskImage(lastSession.maskImage || '');
    // Previews can't be restored from filenames alone; clear them
    setRefPreview('');
    setPosePreview('');
    setMaskPreview('');
  };

  const generate = async () => {
    if (!prompt.trim()) return;
    if (needsRef && !refImage) { alert('Upload reference image'); return; }
    if (needsPose && !poseImage) { alert('Upload pose image'); return; }
    if (needsMask && !maskImage) { alert('Upload mask'); return; }

    const { positive, negative } = buildPrompt();
    const effectiveCfg = realism ? 10 : cfg;

    setGenerating(true);
    setProgress(0);
    setResultUrl('');
    setResultMeta(null);
    setStatus('Submitting...');

    const f = new FormData();
    f.append('task', task);
    f.append('prompt', positive);
    if (negative) f.append('negative_prompt', negative);
    f.append('width', String(width));
    f.append('height', String(height));
    f.append('steps', String(steps));
    f.append('cfg', String(effectiveCfg));
    f.append('seed', String(seedRef.current));
    f.append('model', model);
    f.append('anatomy', String(anatomy));
    f.append('upscale', String(upscale));

    const lorasJson = JSON.stringify(activeLoras());
    f.append('loras', lorasJson);

    if (refImage) f.append('reference_image', refImage);
    if (poseImage) f.append('pose_image', poseImage);
    if (maskImage) f.append('mask_image', maskImage);

    try {
      const r = await fetch(`${API}/api/generate`, { method: 'POST', body: f });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Failed');
      const jobId = d.job_id;
      setStatus('Generating...');
      saveSession();

      pollRef.current = window.setInterval(async () => {
        const pr = await fetch(`${API}/api/progress/${jobId}`);
        const pd = await pr.json();
        const pct = Math.round(pd.progress) || 0;
        setProgress(pct);
        setStatus(getStageText(pct, pd.status));

        if (pd.status === 'completed') {
          clearInterval(pollRef.current!);
          const rr = await fetch(`${API}/api/result/${jobId}`);
          const blob = await rr.blob();
          setResultUrl(URL.createObjectURL(blob));
          setResultMeta({ task, prompt, seed: seedRef.current === -1 ? 'random' : seedRef.current, upscale, model, cfg: effectiveCfg });
          setGenerating(false);
          loadHistory();
        } else if (pd.status === 'error') {
          clearInterval(pollRef.current!);
          setStatus('Error: ' + (pd.error || 'Generation failed'));
          setGenerating(false);
        }
      }, 1200);
    } catch (e: any) {
      setStatus('Error: ' + e.message);
      setGenerating(false);
    }
  };

  const needsRef = task !== 'create';
  const needsPose = task === 'pose';
  const needsMask = task === 'wardrobe' || task === 'retouch';

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

          {lastSession && (
            <div className="session-restore">
              <button className="rerun-btn" onClick={restoreSession}>
                🔄 Re-run last session
              </button>
            </div>
          )}
        </nav>

        <main className="editor">
          <h2>{TASKS.find(t => t.id === task)?.name}</h2>
          <p className="sub">{TASKS.find(t => t.id === task)?.desc}</p>

          {needsRef && <DropZone label="Reference Image" preview={refPreview} onFile={f => upload(f, setRefImage, setRefPreview)} name={refImage} />}
          {needsPose && <DropZone label="Pose Reference" preview={posePreview} onFile={f => upload(f, setPoseImage, setPosePreview)} name={poseImage} />}
          {needsMask && <DropZone label="Mask (white = edit area)" preview={maskPreview} onFile={f => upload(f, setMaskImage, setMaskPreview)} name={maskImage} />}

          <div className="field">
            <label>Description</label>
            <textarea rows={3} value={prompt} onChange={e => setPrompt(e.target.value)} placeholder={task === 'create' ? 'Describe the image you want to create...' : 'Describe what you want to change...'} />
            {isPortrait ? <div className="tag portrait">Portrait mode — close-up framing</div> : <div className="tag body">Full body default — entire figure</div>}
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
            <div className="field">
              <label>LoRAs <small>(up to 3)</small></label>
              {loraSlots.map((slot, idx) => (
                <div key={idx} className="lora-slot">
                  <select value={slot.name} onChange={e => {
                    const next = [...loraSlots];
                    next[idx].name = e.target.value;
                    setLoraSlots(next);
                  }}>
                    <option value="None">None</option>
                    {loras.map(l => <option key={l} value={l}>{l.replace('.safetensors', '')}</option>)}
                  </select>
                  {slot.name !== 'None' && (
                    <div className="lora-strength">
                      <span>Strength: {slot.strength.toFixed(1)}</span>
                      <input type="range" min={0.1} max={1.5} step={0.1} value={slot.strength} onChange={e => {
                        const next = [...loraSlots];
                        next[idx].strength = Number(e.target.value);
                        setLoraSlots(next);
                      }} />
                    </div>
                  )}
                </div>
              ))}
            </div>
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

          <div className="field">
            <label>Hi-Res Fix</label>
            <div className="ratios">
              {UPSCALES.map(u => (
                <button key={u.label} className={upscale === u.value ? 'active' : ''} onClick={() => setUpscale(u.value)}>
                  {u.label}
                </button>
              ))}
            </div>
          </div>

          <div className="field row">
            <label>Steps: {steps}</label>
            <input type="range" min={15} max={50} value={steps} onChange={e => setSteps(Number(e.target.value))} />
          </div>

          <div className="field row">
            <label>Guidance: {realism ? `${cfg} → 10 (Realism)` : cfg}</label>
            <input type="range" min={3} max={12} step={0.5} value={cfg} onChange={e => setCfg(Number(e.target.value))} disabled={realism} />
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

          <div className="realism-panel">
            <div className="realism-header">
              <label className="check">
                <input type="checkbox" checked={realism} onChange={e => setRealism(e.target.checked)} />
                <b>Realism Mode</b> — natural, imperfect bodies
              </label>
              {realism && <span className="realism-active">CFG forced to 10</span>}
            </div>
            {realism && (
              <div className="feature-grid">
                {BODY_FEATURES.map(f => (
                  <label key={f.id} className={`feature-check ${features[f.id] ? 'active' : ''}`}>
                    <input type="checkbox" checked={!!features[f.id]} onChange={() => toggleFeature(f.id)} />
                    {f.label}
                  </label>
                ))}
              </div>
            )}
          </div>

          <button className="generate" onClick={generate} disabled={generating || !backendReady}>
            {generating ? status : '✨ Generate'}
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
              <button onClick={() => { setRefImage(''); setRefPreview(''); setResultUrl(''); setTask('refine'); }}>Refine</button>
              <button onClick={() => { const newSeed = Math.floor(Math.random() * 2**32); setSeed(newSeed); seedRef.current = newSeed; generate(); }}>Re-roll</button>
              <button onClick={() => { const a = document.createElement('a'); a.href = resultUrl; a.download = `studiopro_${Date.now()}.png`; a.click(); }}>Save</button>
            </div>
          )}
          {resultMeta && (
            <div className="meta">
              <div>Seed: {resultMeta.seed}</div>
              <div>Model: {resultMeta.model.replace('.safetensors', '')}</div>
              <div>Hi-Res: {resultMeta.upscale > 1 ? resultMeta.upscale + 'x' : 'Off'}</div>
              <div>CFG: {resultMeta.cfg}</div>
            </div>
          )}

          {history.length > 0 && (
            <div className="history">
              <h4>Recent</h4>
              <div className="history-grid">
                {history.map(h => (
                  <button key={h.id} className="history-thumb" onClick={() => {
                    setResultUrl(`${API}/api/history/${h.id}/image?date=${h.image.split('/')[0]}`);
                    setResultMeta(h);
                  }}>
                    <img src={`${API}/api/history/${h.id}/image?date=${h.image.split('/')[0]}`} alt="" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function DropZone({ label, onFile, name, preview }: { label: string, onFile: (f: File) => void, name: string, preview?: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <div className="dropzone" onClick={() => inputRef.current?.click()}>
      <input ref={inputRef} type="file" accept="image/*" hidden onChange={e => e.target.files?.[0] && onFile(e.target.files[0])} />
      {preview ? (
        <img src={preview} alt={label} className="dropzone-preview" />
      ) : !name ? (
        <><span>📷</span><div>{label}<small>Click or drop</small></div></>
      ) : (
        <span>{name}</span>
      )}
    </div>
  );
}
