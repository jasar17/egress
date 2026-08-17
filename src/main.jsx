import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { AlertTriangle, ArrowLeft, ChevronDown, Download, FileUp, LayoutDashboard, MapPin, MoreHorizontal, Plus, Search, ShieldCheck, Upload, X, CheckCircle2, Clock3, Building2, FileText } from 'lucide-react';
import './styles.css';

const flags = [
  { id: 'V-042', kind: 'Travel distance', clause: 'UAE FLSC 4.2.8.3', title: 'Travel distance exceeds maximum', detail: 'Open office - North zone', measured: '51.8 m', limit: '45.0 m', severity: 'Critical', pos: ['34%', '31%'], status: 'open' },
  { id: 'V-043', kind: 'Travel distance', clause: 'UAE FLSC 4.2.8.3', title: 'Travel distance exceeds maximum', detail: 'Meeting rooms 3-4', measured: '47.2 m', limit: '45.0 m', severity: 'High', pos: ['56%', '55%'], status: 'open' },
  { id: 'V-044', kind: 'Exit capacity', clause: 'UAE FLSC 4.2.9.1', title: 'Exit capacity is insufficient', detail: 'Floor level 06', measured: '1.50 m', limit: '1.80 m', severity: 'Critical', pos: ['75%', '72%'], status: 'open' },
  { id: 'V-045', kind: 'Travel distance', clause: 'UAE FLSC 4.2.8.3', title: 'Travel distance exceeds maximum', detail: 'Open office - South zone', measured: '46.1 m', limit: '45.0 m', severity: 'High', pos: ['48%', '81%'], status: 'open' }
];

const API_URL = 'http://127.0.0.1:8000';
const DEMO_PROJECT_ID = 'project-al-noor';
const DEMO_DRAWING_ID = 'drawing-al-noor-l06';

const toUiFinding = (item) => ({
  id: item.id,
  kind: item.type,
  clause: `UAE FLSC ${item.clause_ref}`,
  title: item.title,
  detail: item.detail,
  measured: `${item.measured_value} ${item.measured_unit}`,
  limit: `${item.limit_value} ${item.limit_unit}`,
  severity: item.severity,
  status: item.status,
  pos: item.geometry?.coordinates?.map(value => `${value}%`) || ['50%', '50%']
});

function App() {
  const [screen, setScreen] = useState('dashboard');
  const [selected, setSelected] = useState('V-042');
  const [items, setItems] = useState(flags);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadState, setUploadState] = useState('idle');
  const [uploadError, setUploadError] = useState('');
  const [currentDrawingId, setCurrentDrawingId] = useState(DEMO_DRAWING_ID);
  const [elements, setElements] = useState([]);
  const [toast, setToast] = useState('');
  const [violationsLoading, setViolationsLoading] = useState(false);
  const [violationsError, setViolationsError] = useState('');
  const [elementsLoading, setElementsLoading] = useState(false);

  useEffect(() => {
    setViolationsLoading(true);
    setViolationsError('');
    fetch(`${API_URL}/drawings/${currentDrawingId}/violations`)
      .then(res => res.ok ? res.json() : Promise.reject('API error'))
      .then(data => {
        const findings = data.map(toUiFinding);
        setItems(findings);
        setSelected(findings[0]?.id || '');
        setViolationsLoading(false);
      })
      .catch((err) => {
        setItems(flags);
        setViolationsError('Unable to load findings from server. Using demo data.');
        setViolationsLoading(false);
      });
  }, [currentDrawingId]);

  useEffect(() => {
    setElementsLoading(true);
    fetch(`${API_URL}/drawings/${currentDrawingId}/elements`)
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(data => {
        setElements(data.features || []);
        setElementsLoading(false);
      })
      .catch(() => {
        setElements([]);
        setElementsLoading(false);
      });
  }, [currentDrawingId]);

  const active = items.find(x => x.id === selected) || items[0];

  const notify = (m) => {
    setToast(m);
    setTimeout(() => setToast(''), 2200);
  };

  const update = (status) => {
    fetch(`${API_URL}/violations/${selected}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    })
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(item => {
        setItems(v => v.map(x => x.id === selected ? toUiFinding(item) : x));
        notify(`Flag ${status.replace('_', ' ')}.`);
      })
      .catch(() => {
        setItems(v => v.map(x => x.id === selected ? { ...x, status } : x));
        notify('Saved locally - API is unavailable.');
      });
  };

  const exportCsv = () => {
    fetch(`${API_URL}/drawings/${currentDrawingId}/export`)
      .then(res => res.ok ? res.blob() : Promise.reject())
      .then(blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `FLS-Review-Summary-${currentDrawingId}.csv`;
        a.click();
        URL.revokeObjectURL(a.href);
        notify('CSV export downloaded.');
      })
      .catch(() => notify('Export requires the backend to be running.'));
  };

  const pollDrawingStatus = (drawingId) => {
    let attempts = 0;
    const maxAttempts = 30;

    const checkStatus = () => {
      fetch(`${API_URL}/drawings/${drawingId}/status`)
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(data => {
          if (data.status === 'ready') {
            setUploadState('idle');
            setShowUploadModal(false);
            notify('Drawing ready. Loading findings...');
          } else if (data.status === 'failed') {
            setUploadState('error');
            setUploadError('Drawing processing failed.');
            notify('Processing failed.');
          } else {
            attempts++;
            if (attempts < maxAttempts) {
              setTimeout(checkStatus, 1000);
            } else {
              setUploadState('error');
              setUploadError('Processing timeout.');
            }
          }
        })
        .catch(() => {
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(checkStatus, 1000);
          }
        });
    };

    checkStatus();
  };

  const handleFileUpload = async (file) => {
    if (!file) return;

    setUploadState('uploading');
    setUploadError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('occupancy_type', 'commercial_office');
    formData.append('scale', '100');

    try {
      const response = await fetch(`${API_URL}/projects/${DEMO_PROJECT_ID}/drawings`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      setCurrentDrawingId(data.drawing_id);
      setUploadState('processing');
      notify('File uploaded. Processing...');
      setScreen('review');
      pollDrawingStatus(data.drawing_id);
    } catch (error) {
      setUploadState('error');
      setUploadError('Upload failed.');
      notify('Upload failed.');
    }
  };

  if (screen === 'dashboard') {
    return (
      <>
        <Header onNew={() => setShowUploadModal(true)} />
        <main className="dashboard">
          <section className="hero">
            <div className="hero-copy">
              <span className="eyebrow">FIRE & LIFE SAFETY REVIEW</span>
              <h1>Clearer egress<br /><em>starts here.</em></h1>
              <p>Review commercial floor plans with confidence. Spot distance and exit-capacity risks before they become site issues.</p>
              <div className="hero-buttons">
                <button className="primary" onClick={() => setShowUploadModal(true)}>
                  <Upload size={16} /> Upload a drawing
                </button>
                <button className="text-button" onClick={() => setScreen('review')}>
                  Open latest review <span>↗</span>
                </button>
              </div>
              <div className="hero-points">
                <span><i /> UAE code clauses</span>
                <span><i /> Reviewer sign-off</span>
              </div>
            </div>
            <div className="hero-visual">
              <div className="drawing-art">
                <div className="art-title">LEVEL 06 <small>COMMERCIAL OFFICE</small></div>
                <div className="art-room a"></div>
                <div className="art-room b"></div>
                <div className="art-room c"></div>
                <div className="art-path"></div>
                <div className="art-exit one">EXIT</div>
                <div className="art-exit two">EXIT</div>
                <div className="art-flag"><AlertTriangle size={16} /><span>51.8m</span></div>
              </div>
              <div className="review-note">
                <div className="faces"><i>MA</i><i>SK</i><i>AR</i></div>
                <b>Review confidence</b>
                <span>87% extraction accuracy</span>
              </div>
              <div className="hero-stat">
                <b>28</b>
                <span>open findings<br />across projects</span>
              </div>
            </div>
          </section>
          <section className="dashboard-lower">
            <div>
              <section className="section-head">
                <div>
                  <span className="eyebrow">YOUR WORKSPACE</span>
                  <h2>Active <em>projects</em></h2>
                </div>
                <div className="search">
                  <Search size={17} />
                  <input placeholder="Search projects" />
                </div>
              </section>
              <div className="projects">
                <Project title="Al Noor Business Centre" client="Al Noor Properties" floors="4 floors" flags="12 flags" status="In review" action={() => { setCurrentDrawingId(DEMO_DRAWING_ID); setScreen('review'); }} />
                <Project title="Bay Square Offices" client="Dubai Properties" floors="2 floors" flags="5 flags" status="Ready for review" action={() => setScreen('review')} />
                <Project title="Emirates Tower Complex" client="Emirates Real Estate" floors="6 floors" flags="18 flags" status="In review" action={() => setScreen('review')} />
              </div>
            </div>
            <section>
              <Metric icon={<AlertTriangle size={20} />} label="Critical findings" value="5" sub="Require immediate review" danger={true} />
              <Metric icon={<Clock3 size={20} />} label="Pending reviews" value="3" sub="Projects waiting" />
              <Metric icon={<CheckCircle2 size={20} />} label="Resolved" value="23" sub="This quarter" />
            </section>
          </section>
        </main>
        {showUploadModal && <UploadModal close={() => setShowUploadModal(false)} onFileSelected={handleFileUpload} isUploading={uploadState === 'uploading'} error={uploadError} />}
        {toast && <div className="toast">{toast}</div>}
      </>
    );
  }

  return (
    <>
      <Header compact onNew={() => setShowUploadModal(true)} />
      <div className="review">
        <aside className="sidebar">
          <button className="back" onClick={() => setScreen('dashboard')}>
            <ArrowLeft size={17} /> Projects
          </button>
          <div className="project-mini">
            <span className="eyebrow">PROJECT</span>
            <h2>Al Noor Business Centre</h2>
            <p>Dubai, UAE</p>
          </div>
          <div className="floor-active">
            <FileText size={18} />
            <div>
              <b>Level 06</b>
              <small>Commercial Office</small>
            </div>
            <ChevronDown size={16} />
          </div>
          <div className="side-block">
            <span>REVIEW PROGRESS</span>
            <div className="progress-row">
              <b>{items.filter(x => x.status !== 'open').length} of {items.length} reviewed</b>
              <b>{items.length > 0 ? Math.round((items.filter(x => x.status !== 'open').length / items.length) * 100) : 0}%</b>
            </div>
            <div className="progress">
              <i style={{ width: `${items.length > 0 ? (items.filter(x => x.status !== 'open').length / items.length) * 100 : 0}%` }} />
            </div>
          </div>
          <div className="side-block">
            <span>DRAWING DETAILS</span>
            <p>Scale <b>1:100</b></p>
            <p>Source <b>PDF</b></p>
            <p>Confidence <b className="amber">87%</b></p>
          </div>
          <div className="side-footer">
            <ShieldCheck size={17} /> Review required before export
          </div>
        </aside>
        <main className="viewer">
          <div className="toolbar">
            <div>
              <span className="breadcrumb">Al Noor Business Centre / Level 06</span>
              <h1>Compliance review</h1>
            </div>
            <div className="actions">
              <button className="secondary" onClick={() => notify('Drawing scale confirmed at 1:100.')}>
                <CheckCircle2 size={16} /> Scale 1:100
              </button>
              <button className="primary" onClick={exportCsv}>
                <Download size={16} /> Export
              </button>
            </div>
          </div>
          <div className="content">
            <section className="plan-wrap">
              <div className="plan-top">
                <span><MapPin size={15} /> Floor plan overlay</span>
                <span className="legend"><i className="red" /> Critical <i className="orange" /> High <i className="green" /> Exit</span>
              </div>
              <FloorPlan active={active.id} select={setSelected} elements={elements} findings={items} />
            </section>
            <aside className="findings">
              <div className="find-head">
                <div>
                  <h2>Findings <em>{items.filter(x => x.status === 'open').length}</em></h2>
                  <p>Click a finding to inspect it.</p>
                </div>
                <MoreHorizontal size={20} />
              </div>
              <div className="finding-list">
                {violationsLoading && (
                  <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading findings...</p>
                  </div>
                )}
                {violationsError && !violationsLoading && (
                  <div className="error-state">
                    <AlertTriangle size={24} />
                    <p><strong>Unable to load findings</strong></p>
                    <small>{violationsError}</small>
                  </div>
                )}
                {!violationsLoading && !violationsError && items.length === 0 && (
                  <div className="empty-state">
                    <CheckCircle2 size={24} />
                    <p>No findings</p>
                    <small>This drawing meets all egress requirements.</small>
                  </div>
                )}
                {!violationsLoading && items.map(f => (
                  <button key={f.id} onClick={() => setSelected(f.id)} className={'finding ' + (f.id === selected ? 'selected' : '') + (f.status !== 'open' ? ' done' : '')}>
                    <div className="find-row">
                      <div><span className="flag-id">{f.id}</span><b>{f.title}</b><span className="location">{f.detail}</span></div>
                      <span className={'severity ' + f.severity.toLowerCase()}>{f.severity}</span>
                    </div>
                  </button>
                ))}
              </div>
            </aside>
          </div>
        </main>
      </div>
      {selected && active && (
        <div className="detail-panel">
          <div className="detail-head">
            <span className="flag-kind">{active.kind}</span>
            <button onClick={() => setSelected(null)}><X size={20} /></button>
          </div>
          <div className="detail-body">
            <h2>{active.title}</h2>
            <div className="detail-grid">
              <div><small>CLAUSE</small><code>{active.clause}</code></div>
              <div><small>LOCATION</small><p>{active.detail}</p></div>
              <div><small>MEASURED</small><p>{active.measured}</p></div>
              <div><small>LIMIT</small><p>{active.limit}</p></div>
            </div>
            <div className="detail-actions">
              {active.status === 'open' && (
                <>
                  <button className="secondary" onClick={() => update('false_positive')}>Mark false positive</button>
                  <button className="primary" onClick={() => update('confirmed')}>Confirm finding</button>
                </>
              )}
              {active.status === 'confirmed' && (
                <>
                  <button className="secondary" onClick={() => update('open')}>Reopen</button>
                  <button className="primary" onClick={() => update('resolved')}>Mark resolved</button>
                </>
              )}
              {active.status === 'resolved' && (
                <button className="secondary" onClick={() => update('open')}>Reopen</button>
              )}
              {active.status === 'false_positive' && (
                <button className="secondary" onClick={() => update('open')}>Reopen</button>
              )}
            </div>
          </div>
        </div>
      )}
      {showUploadModal && <UploadModal close={() => setShowUploadModal(false)} onFileSelected={handleFileUpload} isUploading={uploadState === 'uploading'} error={uploadError} />}
      {toast && <div className="toast">{toast}</div>}
    </>
  );
}

const Header = ({ onNew, compact }) => (
  <header>
    <div className="brand">
      <div className="brand-mark">F</div>
      <span>FLS <b>CHECKER</b></span>
      <small>MVP</small>
    </div>
    {compact ? (
      <div className="user">
        <span className="avatar">SA</span> Samir Ahmed <ChevronDown size={15} />
      </div>
    ) : (
      <nav>
        <a className="active"><LayoutDashboard size={16} /> Projects</a>
        <a>Code library</a>
        <a>Team</a>
        <button className="primary small" onClick={onNew}>
          <Upload size={16} /> Upload drawing
        </button>
        <span className="avatar">SA</span>
      </nav>
    )}
  </header>
);

const Metric = ({ icon, label, value, sub, danger }) => (
  <div className="metric">
    <div className={danger ? 'metric-icon danger' : 'metric-icon'}>{icon}</div>
    <div>
      <span>{label}</span>
      <b>{value}</b>
      <small className={danger ? 'critical-text' : ''}>{sub}</small>
    </div>
  </div>
);

const Project = ({ title, client, floors, flags, status, done, action }) => (
  <button className="project" onClick={action}>
    <div className="project-icon"><Building2 size={21} /></div>
    <div className="project-name">
      <b>{title}</b>
      <span>{client}</span>
    </div>
    <div><small>FLOORS</small><b>{floors}</b></div>
    <div><small>FINDINGS</small><b className={done ? 'success' : ''}>{flags}</b></div>
    <div>
      <span className={'status ' + (done ? 'complete' : '')}>
        {done ? <CheckCircle2 size={14} /> : <Clock3 size={14} />} {status}
      </span>
    </div>
    <ChevronDown className="chev" size={18} />
  </button>
);

function FloorPlan({ active, select, elements, findings }) {
  const renderElements = () => {
    if (!elements || elements.length === 0) return null;
    return elements.map((el, i) => {
      const geom = el.geometry;
      if (!geom) return null;
      if (geom.type === 'Polygon') {
        const coords = geom.coordinates[0];
        const points = coords.map(c => `${c[0]},${c[1]}`).join(' ');
        return <polygon key={i} points={points} fill="#ecf0f1" fillOpacity="0.3" stroke="#95a5a6" strokeWidth="1" />;
      }
      return null;
    });
  };

  return (
    <div className="plan">
      <svg viewBox="0 0 100 70" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
        {renderElements()}
      </svg>
      <div className="room r1">OPEN OFFICE<br /><small>NORTH</small></div>
      <div className="room r2">MEETING<br />ROOMS</div>
      <div className="room r3">OPEN OFFICE<br /><small>SOUTH</small></div>
      <div className="room r4">RECEPTION</div>
      <div className="corridor">CORRIDOR</div>
      <div className="exit e1">EXIT</div>
      <div className="exit e2">EXIT</div>
      {findings.map(f => (
        <button
          onClick={() => select(f.id)}
          key={f.id}
          aria-label={f.id}
          className={'marker ' + (f.id === active ? 'chosen' : '')}
          style={{ left: f.pos[0], top: f.pos[1] }}
        >
          <AlertTriangle size={18} />
          <span>{f.id}</span>
        </button>
      ))}
    </div>
  );
}

function UploadModal({ close, onFileSelected, isUploading, error }) {
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelected(file);
    }
  };

  const showForm = !isUploading && !error;

  return (
    <div className="modal-bg">
      <div className="modal">
        <button className="close" onClick={close} disabled={isUploading}>
          <X />
        </button>
        <span className="eyebrow">NEW FLOOR REVIEW</span>
        <h2>Upload a floor drawing</h2>
        <p>PDF and DXF files are supported. We'll detect scale and egress elements before your review.</p>

        {isUploading && (
          <div className="upload-status">
            <div className="spinner"></div>
            <p>Uploading and processing...</p>
          </div>
        )}

        {error && (
          <div className="upload-error">
            <AlertTriangle size={18} />
            <p>{error}</p>
          </div>
        )}

        {showForm && (
          <>
            <label className="drop">
              <FileUp size={30} />
              <b>Drop drawing here or browse</b>
              <span>PDF or DXF · Maximum 100 MB</span>
              <input type="file" accept=".pdf,.dxf" onChange={handleFileChange} />
            </label>
            <div className="field">
              <label>Occupancy type</label>
              <div>Commercial Office <ChevronDown size={16} /></div>
            </div>
            <button className="primary full" onClick={() => document.querySelector('.drop input').click()}>
              Start review <span>→</span>
            </button>
          </>
        )}
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
