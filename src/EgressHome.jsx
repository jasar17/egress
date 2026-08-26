import React, { useState } from 'react';
import {
  ShieldCheck,
  Building2,
  FileUp,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Clock3,
  RefreshCw,
  Download,
  Search,
  ChevronDown,
  Layers,
  ArrowRight,
  Sparkles,
  MapPin,
  Phone,
  FileText,
  Check,
  X,
  ExternalLink,
  Eye,
  Maximize2
} from 'lucide-react';
import heroBrickImg from './assets/hero_brick_building.jpg';
import heroImg from './assets/hero_egress.jpg';
import financeImg from './assets/finance_desk.jpg';
import abstractDarkImg from './assets/abstract_dark_crimson.jpg';

// SVG Squiggly Wave Accent
export const SquigglyWave = ({ color = '#1a1a1a', width = 54, height = 10, className = '' }) => (
  <svg
    width={width}
    height={height}
    viewBox="0 0 54 10"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`squiggly-wave ${className}`}
  >
    <path
      d="M2 5C5.5 2 9.5 2 13 5C16.5 8 20.5 8 24 5C27.5 2 31.5 2 35 5C38.5 8 42.5 8 46 5C49.5 2 52.5 3 53 5"
      stroke={color}
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export default function EgressHome({
  items,
  selected,
  setSelected,
  drawingMeta,
  elements,
  multiFloorSummary,
  uploadState,
  uploadError,
  onFileUpload,
  onFallbackDemo,
  onFloorSwitch,
  onUpdateFindingStatus,
  onExportCsv,
  onNavigateToReview,
  toast,
  showToast
}) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [occupancyType, setOccupancyType] = useState('Business - Regular office areas');
  const [sprinklered, setSprinklered] = useState(true);
  const [selectedCapability, setSelectedCapability] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      onFileUpload(file, { occupancyType, sprinklered });
      onNavigateToReview();
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    if (file) {
      setSelectedFile(file);
      onFileUpload(file, { occupancyType, sprinklered });
      onNavigateToReview();
    }
  };

  const handleStartAnalysis = () => {
    if (selectedFile) {
      onFileUpload(selectedFile, { occupancyType, sprinklered });
      onNavigateToReview();
    } else {
      document.querySelector('#upload-section input[type=file]')?.click();
    }
  };

  const handleQuickDemoClick = () => {
    onFallbackDemo();
    onNavigateToReview();
    showToast('Loaded Al Noor Business Centre Level 06 into Audit Dashboard.');
  };

  const capabilitiesData = [
    {
      id: 'travel-distance',
      title: 'Travel Distance Verification',
      clause: 'UAE FLSC 3.16-BUS-TD-S',
      icon: <RouteIcon />,
      desc: 'Calculates true unobstructed travel distances from the most remote room points to the nearest fire exit enclosure, verifying compliance against the 45.0m non-sprinklered / 91.0m sprinklered thresholds.'
    },
    {
      id: 'exit-capacity',
      title: 'Exit Capacity & Width',
      clause: 'UAE FLSC 3.14-LT500',
      icon: <DoorIcon />,
      desc: 'Evaluates clear door widths and calculates total egress evacuation throughput capacity based on calculated peak room occupancy loads.'
    },
    {
      id: 'dead-end-corridors',
      title: 'Dead-End Corridors',
      clause: 'UAE FLSC 3.17-DEC-MAX',
      icon: <CornerIcon />,
      desc: 'Identifies hallway pockets exceeding the 6.0m maximum dead-end limit where occupants can be trapped in smoke before reaching an exit.'
    },
    {
      id: 'occupant-load',
      title: 'Occupant Density Matrix',
      clause: 'UAE FLSC Table 3.02',
      icon: <UsersIcon />,
      desc: 'Automates room-by-room occupant density calculations based on occupancy classifications (e.g. 9.3 m²/person for standard business offices).'
    },
    {
      id: 'multi-floor-audit',
      title: 'Multi-Floor Building Audit',
      clause: 'UAE FLSC Chapter 3 Overview',
      icon: <LayersIcon />,
      desc: 'Performs multi-page batch reviews across all building levels from Ground level to typical floors, providing storey-by-storey safety metrics.'
    },
    {
      id: 'clause-citation',
      title: 'Deterministic Code Citation',
      clause: 'Civil Defense Standard Sign-off',
      icon: <ShieldCheck size={26} strokeWidth={1.75} />,
      desc: 'Every flagged finding cites exact UAE Fire and Life Safety Code chapters and clauses with downloadable CSV/PDF audit summary reports.'
    }
  ];

  const isUploading = uploadState === 'uploading' || uploadState === 'processing';

  return (
    <div className="egress-app-wrapper">
      {/* 1. HERO SECTION CONTAINER (Framed with premium blurred dark crimson background) */}
      <div className="egress-hero-outer-wrapper">
        <div
          className="egress-hero-bg-blur"
          style={{ backgroundImage: `url(${abstractDarkImg})` }}
        />
        <div className="egress-hero-bg-overlay" />

        <div
          className="egress-hero-floating-card"
          style={{ backgroundImage: `url(${heroBrickImg})` }}
        >
          <div className="hero-card-dark-overlay"></div>

          {/* Top Nav inside Floating Card */}
          <div className="hero-card-nav">
            <div className="hero-brand-block" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
              <div className="hero-brand-shield">
                <ShieldCheck size={20} />
              </div>
              <span className="hero-brand-name">EGRESS</span>
            </div>

            <nav className="hero-nav-menu">
              <button className="hero-nav-item" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
                Home
              </button>
              <button className="hero-nav-item" onClick={() => document.getElementById('capabilities-section')?.scrollIntoView({ behavior: 'smooth' })}>
                Capabilities
              </button>
              <button className="hero-nav-item" onClick={() => document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' })}>
                Upload Floor Plan
              </button>
              <button className="hero-nav-item" onClick={() => document.getElementById('about-section')?.scrollIntoView({ behavior: 'smooth' })}>
                About EGRESS
              </button>
              <button className="hero-nav-item" onClick={() => document.getElementById('featured-audit')?.scrollIntoView({ behavior: 'smooth' })}>
                Case Audit
              </button>
            </nav>

            <div className="hero-nav-actions">
              <button className="btn-hero-nav-cta" onClick={handleQuickDemoClick}>
                Level 06 Demo
              </button>
            </div>
          </div>

          {/* Centered Hero Typography */}
          <div className="hero-card-center-body">
            <h1 className="hero-card-headline">
              Precision Egress to <span className="hero-headline-italic">Build Safer Spaces</span>
            </h1>
            <p className="hero-card-subtext">
              We deliver <span className="text-medium">deterministic AI compliance reviews</span> that analyze travel distances, exit capacities,
              and corridor safety. Ensure full <em>UAE Fire & Life Safety Code</em> conformity before civil defense submission.
            </p>

            <div className="hero-center-actions">
              <button className="btn-hero-tour" onClick={handleQuickDemoClick}>
                <Sparkles size={16} /> Take a Tour (Level 06 Demo)
              </button>
              <button
                className="btn-hero-tour"
                style={{ backgroundColor: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255,255,255,0.4)' }}
                onClick={() => document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' })}
              >
                <FileUp size={16} /> Upload Floor Plan ↓
              </button>
            </div>
          </div>

          {/* Bottom Docked 3-Column Glass Bar (Identical layout to reference) */}
          <div className="hero-card-bottom-bar">
            <div className="hero-bottom-col">
              <div className="hero-bottom-col-title">
                <ShieldCheck size={16} />
                <span>(*) Compliance Precision</span>
              </div>
              <p className="hero-bottom-col-desc">
                100% deterministic spatial checks against 168+ UAE Fire & Life Safety Code clauses.
              </p>
            </div>

            <div className="hero-bottom-col">
              <div className="hero-bottom-col-title">
                <UsersIcon />
                <span>👥 Architectural Safety</span>
              </div>
              <p className="hero-bottom-col-desc">
                Evaluates travel distances, exit unit widths, and dead-end corridor pockets in seconds.
              </p>
            </div>

            <div className="hero-bottom-col">
              <div className="hero-bottom-col-title">
                <CheckCircle2 size={16} />
                <span>📋 Civil Defense Sign-off</span>
              </div>
              <p className="hero-bottom-col-desc">
                Automated clause citations and traceable CSV audit reports ready for authority submission.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 2. COMPLIANCE CAPABILITIES (2x3 Grid like reference, purely safety focused) */}
      <section id="capabilities-section" className="egress-capabilities-section">
        <div className="egress-container capabilities-layout-grid">
          {/* Left Column: Heading + Intro + Squiggly Wave */}
          <div className="capabilities-left-col">
            <span className="about-eyebrow-chip">SAFETY MODULES</span>
            <h2 className="capabilities-title-dark">Egress <em>Capabilities</em></h2>
            <p className="capabilities-desc-muted">
              Deterministic architectural safety engine engineered to verify <em>every egress requirement</em> stipulated by the UAE Fire and Life Safety Code of Practice.
            </p>
            <SquigglyWave color="#991B1B" width={56} height={10} className="mt-wave" />
          </div>

          {/* Right Column: 2x3 Grid */}
          <div className="capabilities-right-grid">
            {capabilitiesData.map((cap) => (
              <div
                key={cap.id}
                className="capability-card-item"
                onClick={() => setSelectedCapability(cap)}
              >
                <div className="capability-icon-circle">
                  {cap.icon}
                </div>
                <h3 className="capability-title-text">{cap.title}</h3>
                <span className="capability-sub-clause">{cap.clause}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3. PROMO RIBBON WITH DOWNWARD NOTCH */}
      <section className="egress-promo-ribbon">
        <div className="egress-container promo-ribbon-inner">
          <div className="promo-left-block">
            <h2 className="promo-title-h2">EGRESS CODE AUDITING PLATFORM</h2>
            <p className="promo-desc-text">
              Upload multi-floor architectural packages in <em>DXF</em> or <em>PDF</em> format. Our geometric engine automatically classifies
              rooms, computes direct escape paths, and flags code violations before civil defense submission.
            </p>
          </div>
          <div className="promo-right-actions">
            <button className="btn-promo-solid-white" onClick={() => document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' })}>
              UPLOAD DRAWING
            </button>
            <button className="btn-promo-outline-white" onClick={handleQuickDemoClick}>
              OPEN DASHBOARD →
            </button>
          </div>
        </div>

        {/* Downward Caret Notch */}
        <div className="promo-down-notch" onClick={() => document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' })}>
          <div className="notch-triangle"></div>
          <ChevronDown size={14} className="notch-arrow" />
        </div>
      </section>

      {/* 4. IN-PAGE INITIAL UPLOAD & AUDIT SECTION */}
      <section id="upload-section" className="egress-upload-section">
        <div className="egress-container">
          <div className="upload-section-header">
            <h2 className="upload-section-title">Upload Floor Plan for <em>Instant Review</em></h2>
            <p className="upload-section-subtitle">
              Drop any architectural drawing file (<em>.dxf, .pdf</em>). Our engine extracts walls, rooms, and doors,
              and opens the full compliance review dashboard with live travel paths and exit capacity metrics.
            </p>
          </div>

          <div className="upload-workspace-card">
            {isUploading ? (
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <RefreshCw size={36} className="spin-fast" style={{ color: 'var(--egress-crimson)', margin: '0 auto 16px auto' }} />
                <h3 style={{ fontSize: '18px', fontWeight: 800, margin: '0 0 8px 0' }}>Analyzing Drawing Geometry...</h3>
                <p style={{ color: 'var(--egress-body-muted)', fontSize: '13px', margin: 0 }}>
                  Extracting room polygons, measuring travel distances, and verifying exit widths against UAE FLS code clauses.
                </p>
              </div>
            ) : (
              <>
                <label
                  className={`upload-dropzone-box ${dragOver ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                >
                  <div className="upload-icon-circle">
                    <FileUp size={28} />
                  </div>
                  <b className="dropzone-main-text">
                    {selectedFile ? `Selected: ${selectedFile.name}` : 'Drop DXF or PDF Floor Plan here, or click to browse'}
                  </b>
                  <span className="dropzone-sub-text">Supports AutoCAD .DXF vectors and multi-page architectural .PDF documents</span>
                  <input type="file" accept=".pdf,.dxf" onChange={handleFileChange} style={{ display: 'none' }} />
                </label>

                {uploadError && (
                  <div style={{ background: '#FEF2F2', border: '1px solid #F87171', borderRadius: '4px', padding: '12px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px', color: '#B91C1C', fontSize: '12.5px', fontWeight: 600 }}>
                    <AlertTriangle size={16} />
                    <span>{uploadError}</span>
                  </div>
                )}

                <div className="upload-config-grid">
                  <div className="config-field-group">
                    <label>OCCUPANCY CLASSIFICATION</label>
                    <select
                      className="config-select-input"
                      value={occupancyType}
                      onChange={(e) => setOccupancyType(e.target.value)}
                    >
                      <option value="Business - Regular office areas">Business - Regular office (9.3 m²/person)</option>
                      <option value="Business - Concentrated office areas (open-plan, workstation-dense)">Business - Concentrated (4.6 m²/person)</option>
                      <option value="Assembly - Unconcentrated">Assembly - Tables & Chairs (1.4 m²/person)</option>
                      <option value="Mercantile - Retail Floor">Mercantile - Retail sales (2.8 m²/person)</option>
                    </select>
                  </div>

                  <div className="config-field-group">
                    <label>FIRE SPRINKLER PROTECTION</label>
                    <select
                      className="config-select-input"
                      value={sprinklered ? 'yes' : 'no'}
                      onChange={(e) => setSprinklered(e.target.value === 'yes')}
                    >
                      <option value="yes">Sprinklered System (91m max travel distance)</option>
                      <option value="no">Non-Sprinklered System (61m max travel distance)</option>
                    </select>
                  </div>
                </div>

                <div className="upload-actions-bar">
                  <button className="btn-upload-submit" onClick={handleStartAnalysis}>
                    <FileUp size={16} />
                    <span>{selectedFile ? `Analyze "${selectedFile.name}" & Open Dashboard →` : 'Upload Floor Plan & Start Audit →'}</span>
                  </button>
                  <button className="btn-upload-demo-load" onClick={handleQuickDemoClick}>
                    <Sparkles size={15} style={{ color: '#D97706' }} />
                    <span>⚡ Load Sample Floor: Dubai Al Noor L06</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* 5. ABOUT EGRESS SECTION */}
      <section id="about-section" className="egress-about-section">
        <div className="egress-container about-layout-grid">
          <div className="about-left-col">
            <span className="about-eyebrow-chip">ABOUT EGRESS</span>
            <h2 className="about-heading-heavy">
              Automated civil defense compliance for <em>modern architectural engineering</em>
            </h2>
            <SquigglyWave color="#991B1B" width={56} height={10} className="mt-wave" />
          </div>
          <div className="about-right-col">
            <p className="about-body-paragraph">
              In modern building construction across the UAE and Gulf region, egress safety verification is one of the most critical stages in securing civil defense permitting. Traditionally, reviewing floor plans requires manual ruler measurements across dozens of architectural sheets to track travel paths and exit widths.
            </p>
            <p className="about-body-paragraph">
              <strong>EGRESS</strong> transforms this workflow into an instant, deterministic computational process. By extracting spatial geometry from DXF and PDF drawings, our platform calculates egress compliance against <em>168+ UAE code clauses</em> in seconds, preventing costly redesign delays before site execution.
            </p>
          </div>
        </div>
      </section>

      {/* 6. FEATURED AUDIT CASE STUDY (Dark Crimson 3D Abstract Background) */}
      <section
        id="featured-audit"
        className="egress-featured-audit-section"
        style={{ backgroundImage: `url(${abstractDarkImg})` }}
      >
        <div className="featured-dark-overlay"></div>
        <div className="egress-container featured-content-wrap">
          <div className="featured-head-center">
            <h2 className="featured-title-white">Featured Compliance Audit</h2>
            <p className="featured-sub-white">
              <em>Al Noor Business Centre</em> — Level 06 Commercial Office Floor Plan Compliance Analysis
            </p>
            <SquigglyWave color="#FFFFFF" width={56} height={10} className="mx-auto-wave" />
          </div>

          <div className="featured-case-card">
            <div className="case-card-image-half" style={{ backgroundImage: `url(${financeImg})` }}>
              <div className="case-image-badge">DUBAI COMMERCIAL AUDIT</div>
            </div>
            <div className="case-card-info-half">
              <h3 className="case-info-title">Corporate Building Review</h3>
              <p className="case-info-text">
                Complete architectural egress review flagged 4 critical findings: North & South zone travel distances
                exceeding 45.0m, and West exit door undersized for calculated occupant load.
              </p>
              <button
                className="btn-egress-primary"
                style={{ alignSelf: 'flex-start' }}
                onClick={handleQuickDemoClick}
              >
                INSPECT LEVEL 06 DRAWING →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 9. ASSURANCE & CONTACT BOTTOM BAR */}
      <div className="egress-bottom-assurance-bar">
        <div className="egress-container egress-bottom-assurance-inner">
          <div className="egress-bottom-contact">
            <a href="tel:+97143827000" className="bottom-contact-item">
              <Phone size={14} />
              <span>+971 4 382 7000</span>
            </a>
            <span className="bottom-contact-sep">•</span>
            <div className="bottom-contact-item">
              <MapPin size={14} />
              <span>Dubai Future District / Business Bay, UAE</span>
            </div>
          </div>

          <div className="egress-bottom-badges">
            <span className="bottom-compliance-badge">
              <ShieldCheck size={14} /> UAE Fire & Life Safety Code 2018 Edition
            </span>
            <span className="bottom-compliance-badge">
              ✓ 168 Deterministic Clauses
            </span>
          </div>
        </div>
      </div>

      {/* 10. FOOTER */}
      <footer className="egress-footer">
        <div className="egress-container egress-footer-inner">
          <div className="footer-brand-info">
            <b>EGRESS FLS Compliance Engine</b>
            <span>Deterministic Fire & Life Safety plan verification conforming to UAE Civil Defense regulations.</span>
          </div>
          <div className="footer-links-row">
            <a href="#code" onClick={(e) => { e.preventDefault(); showToast('UAE FLS Code 2018 Reference Library'); }}>Code Clauses</a>
            <a href="#dxf" onClick={(e) => { e.preventDefault(); showToast('DXF & PDF Specification'); }}>Drawing Specs</a>
            <a href="#privacy" onClick={(e) => { e.preventDefault(); showToast('Privacy Policy'); }}>Privacy</a>
            <a href="#terms" onClick={(e) => { e.preventDefault(); showToast('Terms of Service'); }}>Terms</a>
          </div>
        </div>
      </footer>

      {/* CAPABILITY DETAIL MODAL */}
      {selectedCapability && (
        <div className="payton-modal-backdrop" onClick={() => setSelectedCapability(null)}>
          <div className="payton-modal-box" onClick={(e) => e.stopPropagation()}>
            <button className="payton-modal-close" onClick={() => setSelectedCapability(null)}>
              <X size={18} />
            </button>
            <div className="modal-icon-badge" style={{ background: 'var(--egress-crimson-light)', color: 'var(--egress-crimson)' }}>
              {selectedCapability.icon}
            </div>
            <h3 className="modal-title-bold">{selectedCapability.title}</h3>
            <span style={{ display: 'inline-block', fontFamily: 'var(--egress-font-mono)', fontSize: '11px', fontWeight: 800, color: 'var(--egress-crimson)', marginBottom: '12px' }}>
              {selectedCapability.clause}
            </span>
            <p className="modal-desc-body">{selectedCapability.desc}</p>
            <div className="modal-feature-list">
              <div className="feature-check-item">
                <Check size={14} style={{ color: 'var(--egress-crimson)' }} />
                <span>Deterministic calculation verified against UAE Civil Defense standards</span>
              </div>
              <div className="feature-check-item">
                <Check size={14} style={{ color: 'var(--egress-crimson)' }} />
                <span>Supports both Sprinklered (91m) and Non-Sprinklered (61m) parameters</span>
              </div>
              <div className="feature-check-item">
                <Check size={14} style={{ color: 'var(--egress-crimson)' }} />
                <span>Exportable in compliant CSV sign-off summary</span>
              </div>
            </div>
            <button
              className="btn-egress-primary"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => {
                setSelectedCapability(null);
                handleQuickDemoClick();
              }}
            >
              TEST THIS MODULE ON DEMO FLOOR →
            </button>
          </div>
        </div>
      )}

      {/* TOAST BANNER */}
      {toast && (
        <div style={{ position: 'fixed', bottom: '24px', right: '24px', background: '#0F172A', color: '#FFFFFF', padding: '12px 20px', borderRadius: '6px', borderLeft: '4px solid var(--egress-crimson)', fontSize: '12.5px', fontWeight: 700, boxShadow: '0 10px 28px rgba(0,0,0,0.3)', zIndex: 999 }}>
          {toast}
        </div>
      )}
    </div>
  );
}

// Helper SVG Icons for Safety & Compliance modules
function RouteIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="19" r="3" />
      <path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15" />
      <circle cx="18" cy="5" r="3" />
    </svg>
  );
}

function DoorIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 20V6a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v14" />
      <path d="M2 20h20" />
      <path d="M14 12v.01" />
    </svg>
  );
}

function CornerIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}

function UsersIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function LayersIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z" />
      <path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65" />
      <path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65" />
    </svg>
  );
}
