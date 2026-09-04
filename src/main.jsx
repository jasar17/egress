import React, { useEffect, useState, useRef, useMemo } from 'react';
import { createRoot } from 'react-dom/client';
import {
  AlertTriangle,
  ArrowLeft,
  ChevronDown,
  Download,
  FileUp,
  LayoutDashboard,
  MapPin,
  MoreHorizontal,
  Search,
  ShieldCheck,
  Upload,
  X,
  CheckCircle2,
  Clock3,
  Building2,
  FileText,
  RefreshCw,
  Sliders,
  Check,
  FileCheck,
  Layers,
  Eye,
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Move,
  Grid
} from 'lucide-react';
import './styles.css';
import EgressHome from './EgressHome.jsx';

const DEMO_FLAGS = [
  { id: 'V-042', kind: 'Travel distance', clause: 'UAE FLSC 3.16-BUS-TD-S', title: 'Travel distance exceeds maximum', detail: 'Open office - North zone', measured: '51.8 m', limit: '45.0 m', severity: 'Critical', pos: ['30%', '26%'], status: 'open' },
  { id: 'V-043', kind: 'Travel distance', clause: 'UAE FLSC 3.16-BUS-TD-S', title: 'Travel distance exceeds maximum', detail: 'Meeting rooms 3-4', measured: '47.2 m', limit: '45.0 m', severity: 'High', pos: ['73%', '26%'], status: 'open' },
  { id: 'V-044', kind: 'Exit capacity', clause: 'UAE FLSC 3.14-LT500', title: 'Exit capacity is insufficient', detail: 'Floor level 06 - Exit west', measured: '1.50 m', limit: '1.80 m', severity: 'Critical', pos: ['79%', '74%'], status: 'open' },
  { id: 'V-045', kind: 'Travel distance', clause: 'UAE FLSC 3.16-BUS-TD-S', title: 'Travel distance exceeds maximum', detail: 'Open office - South zone', measured: '46.1 m', limit: '45.0 m', severity: 'High', pos: ['34%', '74%'], status: 'open' }
];

const API_URL = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://127.0.0.1:8000' : 'https://egressandco.onrender.com');
const DEMO_PROJECT_ID = 'project-al-noor';
const DEMO_DRAWING_ID = 'drawing-al-noor-l06';

const toUiFinding = (item) => {
  let pos = ['50%', '50%'];
  if (item.geometry?.coordinates && Array.isArray(item.geometry.coordinates)) {
    const coords = item.geometry.coordinates;
    if (coords.length >= 2) {
      const xPct = Math.max(3, Math.min(97, coords[0]));
      const yPct = Math.max(3, Math.min(97, coords[1]));
      pos = [`${xPct}%`, `${yPct}%`];
    }
  }

  // Extract clean room location name
  let roomName = item.location || '';
  if (!roomName && item.detail && item.detail.includes(' - ')) {
    roomName = item.detail.split(' - ')[0].trim();
  }
  if (!roomName && item.title && item.title.includes(' - ')) {
    roomName = item.title.split(' - ')[0].trim();
  }
  if (!roomName) {
    if ((item.type || '').includes('exit')) roomName = 'Overall Floor';
    else roomName = 'Floor Review';
  }

  // Clean concise title for cards
  let shortTitle = 'Travel Distance Exceeded';
  if ((item.type || '').includes('exit_count') || (item.type || '').includes('exit_capacity') || (item.type || '').includes('Number of floor exits')) {
    shortTitle = 'Insufficient Exit Count';
  } else if ((item.type || '').includes('width')) {
    shortTitle = 'Exit Width Undersized';
  } else if ((item.type || '').includes('dead_end')) {
    shortTitle = 'Dead-End Corridor Exceeded';
  } else if ((item.type || '').includes('area')) {
    shortTitle = 'Room Area Exceeds Limit';
  }

  return {
    id: item.id,
    kind: item.type,
    roomName,
    shortTitle,
    clause: item.clause_ref?.startsWith('UAE') ? item.clause_ref : `UAE FLSC ${item.clause_ref}`,
    title: item.title,
    detail: item.detail,
    measured: `${item.measured_value} ${item.measured_unit}`,
    limit: `${item.limit_value} ${item.limit_unit}`,
    severity: item.severity,
    status: item.status || 'open',
    pos
  };
};


function App() {
  const [screen, setScreen] = useState('egress');
  const [selected, setSelected] = useState(null);
  const [items, setItems] = useState(DEMO_FLAGS);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadState, setUploadState] = useState('idle'); // 'idle' | 'uploading' | 'processing' | 'error'
  const [uploadError, setUploadError] = useState('');
  const [currentDrawingId, setCurrentDrawingId] = useState(DEMO_DRAWING_ID);
  const [projectDrawings, setProjectDrawings] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);
  const [hoveredDevice, setHoveredDevice] = useState(null);
  const [drawingMeta, setDrawingMeta] = useState({
    name: 'Al Noor Business Centre',
    floor: 'Level 06 - Architectural CAD Overview',
    documentType: 'architectural',
    occupancy: 'Business - Regular office areas',
    sprinklered: true,
    scale: '1:100',
    fileType: 'DXF',
    fileName: 'Dubai_Commercial_Floor_Level_02_Typical.dxf',
    hasImage: false,
    pageIndex: 0,
    pagesCount: 1,
    pages: [{ index: 0, title: 'Level 06 - Architectural CAD Overview' }],
    imageTimestamp: Date.now()
  });
  const [multiFloorSummary, setMultiFloorSummary] = useState(null);
  const [showMultiFloorOverview, setShowMultiFloorOverview] = useState(false);
  const [elements, setElements] = useState([]);
  const [toast, setToast] = useState('');
  const [violationsLoading, setViolationsLoading] = useState(false);
  const [violationsError, setViolationsError] = useState('');
  const [elementsLoading, setElementsLoading] = useState(false);
  const [floorSwitching, setFloorSwitching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileTab, setMobileTab] = useState('plan'); // 'plan' | 'findings'
  const [viewMode, setViewMode] = useState('hybrid'); // 'hybrid' | 'vector' | 'image'
  const [isFullScreen, setIsFullScreen] = useState(false);

  // Client-side in-memory floor cache: { [pageIndex]: { elements, items, floorTitle } }
  const floorCacheRef = useRef({});

  // Prevent browser window / tab zoom when scrolling over canvas
  useEffect(() => {
    const preventTabZoom = (e) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.target.closest('.plan') || e.target.closest('.fullscreen-plan-overlay') || e.target.closest('.plan-container') || e.target.closest('.review')) {
          e.preventDefault();
        }
      }
    };
    window.addEventListener('wheel', preventTabZoom, { passive: false });
    return () => window.removeEventListener('wheel', preventTabZoom);
  }, []);


  // Core loader for drawing data
  const loadDrawingData = async (drawingId, customMeta = null) => {
    setViolationsLoading(true);
    setViolationsError('');
    setElementsLoading(true);

    try {
      const vRes = await fetch(`${API_URL}/drawings/${drawingId}/violations`);
      if (vRes.ok) {
        const vData = await vRes.json();
        if (Array.isArray(vData)) {
          const findings = vData.map(toUiFinding);
          setItems(findings);
          setSelected(null);
        }
      } else {
        throw new Error('Violations API returned status ' + vRes.status);
      }
    } catch (err) {
      console.warn('Violations load error, falling back to local demo findings:', err);
      if (drawingId === DEMO_DRAWING_ID) {
        setItems(DEMO_FLAGS);
        setSelected(null);
      } else {
        setItems([]);
        setSelected(null);
      }
      setViolationsError('Server findings unavailable.');
    } finally {
      setViolationsLoading(false);
    }

    try {
      const eRes = await fetch(`${API_URL}/drawings/${drawingId}/elements`);
      if (eRes.ok) {
        const eData = await eRes.json();
        setElements(eData.features || []);
      }
    } catch (err) {
      console.warn('Elements load error:', err);
      setElements([]);
    } finally {
      setElementsLoading(false);
    }

    // Also fetch drawing info to get latest pages list, floor name, hasImage, and multi-floor summary
    try {
      const dRes = await fetch(`${API_URL}/drawings/${drawingId}`);
      if (dRes.ok) {
        const dData = await dRes.json();
        setDrawingMeta(prev => ({
          ...prev,
          name: dData.name ? dData.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' ') : prev.name,
          documentType: dData.document_type || prev.documentType || 'architectural',
          floor: dData.floor_name || prev.floor,
          fileType: (dData.file_type || '').toUpperCase(),
          hasImage: dData.has_image || false,
          pageIndex: dData.page_index !== undefined ? dData.page_index : prev.pageIndex,
          pagesCount: dData.pages_count || prev.pagesCount,
          pages: dData.pages || prev.pages,
          imageTimestamp: Date.now()
        }));
        if (dData.project_id) {
          fetchProjectDrawings(dData.project_id);
        }
        if (dData.multi_floor_summary) {
          setMultiFloorSummary(dData.multi_floor_summary);
          // Cache all floors
          if (Array.isArray(dData.multi_floor_summary.floors)) {
            dData.multi_floor_summary.floors.forEach(f => {
              floorCacheRef.current[f.index] = {
                elements: f.elements || [],
                items: Array.isArray(f.violations) ? f.violations.map(toUiFinding) : [],
                floorTitle: f.title
              };
            });
          }
        } else {
          fetch(`${API_URL}/drawings/${drawingId}/multi-floor-summary`)
            .then(res => res.ok ? res.json() : null)
            .then(summary => {
              if (summary) {
                setMultiFloorSummary(summary);
                if (Array.isArray(summary.floors)) {
                  summary.floors.forEach(f => {
                    floorCacheRef.current[f.index] = {
                      elements: f.elements || [],
                      items: Array.isArray(f.violations) ? f.violations.map(toUiFinding) : [],
                      floorTitle: f.title
                    };
                  });
                }
              }
            })
            .catch(() => {});
        }
      }
    } catch (dErr) {
      console.warn('Drawing meta fetch error:', dErr);
    }

    if (customMeta) {
      setDrawingMeta(prev => ({ ...prev, ...customMeta, imageTimestamp: Date.now() }));
    }
  };

  const fetchProjectDrawings = async (projId = DEMO_PROJECT_ID) => {
    if (!projId) return;
    try {
      const res = await fetch(`${API_URL}/projects/${projId}/drawings`);
      if (res.ok) {
        const data = await res.json();
        setProjectDrawings(Array.isArray(data) ? data : (data.drawings || []));
      }
    } catch (err) {
      console.warn('Project drawings fetch error:', err);
    }
  };

  const formatFloorTabTitle = (d) => {
    const isFa = d.document_type === 'fire_alarm';
    const raw = (d.floor_name || d.name || '').trim();
    
    if (isFa) {
      if (raw && !raw.toLowerCase().includes('architectural')) {
        const cleanRaw = raw
          .replace(/Dubai Commercial Floor\s*/i, '')
          .replace(/Dubai Level\s*/i, 'Level ')
          .replace(/Dubai\s*/i, '');
        return `🚨 ${cleanRaw}`;
      }
      return '🚨 Fire Alarm Plan';
    }

    if (!raw || raw === 'Architectural Floor Plan') {
      return `📐 Floor Plan (${d.file_type ? d.file_type.toUpperCase() : 'CAD'})`;
    }

    let clean = raw
      .replace(/^Dubai Commercial Floor\s*/i, '')
      .replace(/^Commercial Floor\s*/i, '')
      .replace(/^Dubai\s*/i, '')
      .replace(/^Level\s*0*/i, 'Level ');

    if (/Level\s*0*0\b|Ground/i.test(clean)) {
      return 'Level 00 (Ground)';
    }
    if (/Level\s*0*1\b/i.test(clean)) {
      if (/Typical/i.test(clean) || /Office/i.test(clean)) return 'Level 01 (Office)';
      if (/Arch/i.test(clean)) return 'Level 01 (Arch)';
      return 'Level 01';
    }
    if (/Level\s*0*2\b/i.test(clean)) {
      if (/Layout/i.test(clean)) return 'Level 02 (Layout)';
      return 'Level 02';
    }
    if (/Level\s*0*3\b/i.test(clean)) {
      return 'Level 03';
    }
    if (/Level\s*0*4\b/i.test(clean)) {
      if (/Executive/i.test(clean)) return 'Level 04 (Executive)';
      return 'Level 04';
    }
    if (/Level\s*0*5\b/i.test(clean)) {
      return 'Level 05 (Non-Compliant)';
    }
    if (/Level\s*0*6\b/i.test(clean)) {
      return 'Level 06 (Demo)';
    }
    return clean.length > 22 ? clean.substring(0, 20) + '…' : clean;
  };

  const validProjectDrawings = useMemo(() => {
    const list = (projectDrawings || []).filter(d => 
      d.status === 'ready' && 
      !((d.floor_name || d.name || '').toLowerCase().includes('corrupt'))
    );
    // Sort floors logically: Ground (00), 01, 02, 03, 04, 05, 06, then Fire Alarm
    const getFloorWeight = (d) => {
      if (d.document_type === 'fire_alarm') return 999;
      const str = (d.floor_name || d.name || '').toLowerCase();
      if (str.includes('ground') || str.includes('level 00')) return 0;
      const match = str.match(/level\s*0*(\d+)/i);
      if (match) return parseInt(match[1], 10);
      return 100;
    };
    list.sort((a, b) => getFloorWeight(a) - getFloorWeight(b));

    // Deduplicate by formatted floor title so identical runs don't show duplicates
    const deduped = [];
    const seen = new Set();
    for (const d of list) {
      const key = `${d.document_type}_${formatFloorTabTitle(d)}_${d.file_type || ''}`;
      if (!seen.has(key) || d.id === currentDrawingId) {
        seen.add(key);
        deduped.push(d);
      }
    }
    return deduped;
  }, [projectDrawings, currentDrawingId]);

  useEffect(() => {
    fetchProjectDrawings(DEMO_PROJECT_ID);
  }, []);

  useEffect(() => {
    loadDrawingData(currentDrawingId);
  }, [currentDrawingId]);

  const active = items.find(x => x.id === selected) || items[0] || null;

  const notify = (m) => {
    setToast(m);
    setTimeout(() => setToast(''), 3000);
  };

  const update = async (status) => {
    if (!selected) return;

    // Optimistic update
    setItems(prev => prev.map(x => x.id === selected ? { ...x, status } : x));
    notify(`Finding marked as ${status.replace('_', ' ')}.`);

    try {
      const res = await fetch(`${API_URL}/violations/${selected}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        const item = await res.json();
        setItems(v => v.map(x => x.id === selected ? toUiFinding(item) : x));
      }
    } catch (err) {
      console.warn('Backend patch failed, saved locally:', err);
    }
  };

  const exportCsv = async () => {
    try {
      const res = await fetch(`${API_URL}/drawings/${currentDrawingId}/export`);
      if (res.ok) {
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `FLS-Review-${currentDrawingId}.csv`;
        a.click();
        URL.revokeObjectURL(a.href);
        notify('CSV export downloaded from server.');
        return;
      }
    } catch (e) {
      console.warn('Backend export failed, generating client CSV:', e);
    }

    const headers = ['ID', 'Type', 'Location', 'Clause', 'Measured', 'Limit', 'Severity', 'Status'];
    const csvRows = [
      headers.join(','),
      ...items.map(f => [
        `"${f.id}"`,
        `"${f.kind}"`,
        `"${f.detail}"`,
        `"${f.clause}"`,
        `"${f.measured}"`,
        `"${f.limit}"`,
        `"${f.severity}"`,
        `"${f.status}"`
      ].join(','))
    ];
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `FLS-Review-${currentDrawingId}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
    notify('CSV review summary downloaded.');
  };

  const handleFileUpload = async (file, config = {}) => {
    if (!file) return;

    setUploadState('uploading');
    setUploadError('');

    const occType = config.occupancyType || 'Business - Regular office areas';
    const isSprinklered = config.sprinklered !== undefined ? config.sprinklered : true;
    const docType = config.documentType || 'architectural';

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', docType);
    formData.append('occupancy_type', occType);
    formData.append('sprinklered', isSprinklered ? 'true' : 'false');
    formData.append('scale', '100');

    try {
      const response = await fetch(`${API_URL}/projects/${DEMO_PROJECT_ID}/drawings`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Upload returned status ${response.status}`);
      }

      const data = await response.json();
      const newDrawingId = data.drawing_id;
      floorCacheRef.current = {};
      setCurrentDrawingId(newDrawingId);

      // Load new drawing data immediately
      if (data.multi_floor_summary) {
        setMultiFloorSummary(data.multi_floor_summary);
        if (Array.isArray(data.multi_floor_summary.floors)) {
          data.multi_floor_summary.floors.forEach(f => {
            floorCacheRef.current[f.index] = {
              elements: f.elements || [],
              items: Array.isArray(f.violations) ? f.violations.map(toUiFinding) : [],
              floorTitle: f.title
            };
          });
        }
      }
      await loadDrawingData(newDrawingId, {
        name: file.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' '),
        floor: data.floor_name || file.name.replace('.dxf', '').replace('.pdf', '').replace(/_/g, ' '),
        documentType: data.document_type || docType,
        occupancy: occType,
        sprinklered: isSprinklered,
        scale: '1:100',
        fileType: file.name.toLowerCase().endsWith('.dxf') ? 'DXF' : 'PDF',
        fileName: file.name,
        hasImage: data.has_image || file.name.toLowerCase().endsWith('.pdf'),
        pageIndex: data.page_index || 0,
        pagesCount: data.pages_count || 1,
        pages: data.pages || [{ index: 0, title: data.floor_name || (docType === 'fire_alarm' ? 'Fire Alarm Shop Drawing' : 'Architectural Floor Plan') }],
        imageTimestamp: Date.now()
      });

      fetchProjectDrawings(DEMO_PROJECT_ID);

      setUploadState('idle');
      setShowUploadModal(false);
      setScreen('review');
      notify(
        docType === 'fire_alarm'
          ? `Fire Alarm drawing "${file.name}" ingested: detected devices ready.`
          : `Drawing "${file.name}" analyzed (${isSprinklered ? 'Sprinklered' : 'Non-Sprinklered'}): floor overview ready.`
      );
    } catch (error) {
      console.error('File upload error:', error);
      setUploadState('error');
      setUploadError(error.message || `Could not connect to API server (${API_URL}).`);
    }
  };

  const handleFloorSwitch = async (pageIndex) => {
    if (pageIndex === drawingMeta.pageIndex) return;

    // 1. Instant optimistic local transition if cached
    const cached = floorCacheRef.current[pageIndex];
    const targetPage = drawingMeta.pages?.find(p => p.index === pageIndex);
    const floorTitle = cached?.floorTitle || targetPage?.title || `Floor Level 0${pageIndex}`;

    if (cached) {
      // Instant switch with zero lag and no loading overlay
      setElements(cached.elements || []);
      setItems(cached.items || []);
      setSelected(null);
      setDrawingMeta(prev => ({
        ...prev,
        floor: floorTitle,
        pageIndex: pageIndex,
        imageTimestamp: Date.now()
      }));
      notify(`Switched overview to ${floorTitle}`);
    } else {
      // If not yet cached, show lightweight floor indicator
      setFloorSwitching(true);
    }

    // 2. Asynchronously notify backend of active page and refresh
    try {
      const res = await fetch(`${API_URL}/drawings/${currentDrawingId}/page`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ page_index: pageIndex })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.multi_floor_summary) {
          setMultiFloorSummary(data.multi_floor_summary);
          if (Array.isArray(data.multi_floor_summary.floors)) {
            data.multi_floor_summary.floors.forEach(f => {
              floorCacheRef.current[f.index] = {
                elements: f.elements || [],
                items: Array.isArray(f.violations) ? f.violations.map(toUiFinding) : [],
                floorTitle: f.title
              };
            });
          }
        }
        // If it wasn't cached before, apply newly received elements and violations now
        if (!cached) {
          const freshTarget = floorCacheRef.current[pageIndex];
          if (freshTarget) {
            setElements(freshTarget.elements || []);
            setItems(freshTarget.items || []);
          }
          setDrawingMeta(prev => ({
            ...prev,
            floor: data.floor_name || floorTitle,
            pageIndex: pageIndex,
            imageTimestamp: Date.now()
          }));
          notify(`Switched overview to ${data.floor_name || floorTitle}`);
        }
      }
    } catch (err) {
      console.warn('Background floor switch notification:', err);
    } finally {
      setFloorSwitching(false);
    }
  };

  const handleDemoUploadFallback = () => {
    setCurrentDrawingId(DEMO_DRAWING_ID);
    setItems(DEMO_FLAGS);
    setSelected(DEMO_FLAGS[0]?.id || '');
    setDrawingMeta({
      name: 'Al Noor Business Centre',
      floor: 'Level 06 (Demo Plan)',
      occupancy: 'Business - Regular office areas',
      scale: '1:100',
      fileType: 'PDF',
      fileName: 'Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf',
      hasImage: false,
      pageIndex: 0,
      pagesCount: 1,
      pages: [{ index: 0, title: 'Level 06 (Demo Plan)' }],
      imageTimestamp: Date.now()
    });
    setUploadState('idle');
    setShowUploadModal(false);
    setScreen('review');
    notify('Demo drawing loaded with 4 egress compliance findings.');
  };

  const projectsList = [
    { id: 'al-noor', title: 'Al Noor Business Centre', client: 'Al Noor Properties', floors: '4 floors', flags: `${items.length} flags`, status: 'In review', done: false },
    { id: 'bay-square', title: 'Bay Square Offices', client: 'Dubai Properties', floors: '2 floors', flags: '5 flags', status: 'Ready for review', done: false },
    { id: 'emirates-tower', title: 'Emirates Tower Complex', client: 'Emirates Real Estate', floors: '6 floors', flags: '18 flags', status: 'In review', done: false }
  ].filter(p => p.title.toLowerCase().includes(searchQuery.toLowerCase()) || p.client.toLowerCase().includes(searchQuery.toLowerCase()));

  // Dynamic calculated floor metrics
  const totalFloorArea = Math.round(
    elements
      .filter(e => e.type === 'room' && !e.properties?.name?.toUpperCase().includes('STAIR'))
      .reduce((sum, e) => sum + (parseFloat(e.properties?.area_m2) || 0), 0)
  ) || (currentDrawingId === DEMO_DRAWING_ID ? 396 : 0);

  const totalFloorOccupants = elements
    .filter(e => e.type === 'room')
    .reduce((sum, e) => sum + (parseInt(e.properties?.occupant_load) || 0), 0) || (currentDrawingId === DEMO_DRAWING_ID ? 44 : 0);

  if (screen === 'egress') {
    return (
      <>
        <EgressHome
          items={items}
          selected={selected}
          setSelected={setSelected}
          drawingMeta={drawingMeta}
          elements={elements}
          multiFloorSummary={multiFloorSummary}
          uploadState={uploadState}
          uploadError={uploadError}
          onFileUpload={handleFileUpload}
          onFallbackDemo={handleDemoUploadFallback}
          onFloorSwitch={handleFloorSwitch}
          onUpdateFindingStatus={update}
          onExportCsv={exportCsv}
          onNavigateToReview={() => setScreen('review')}
          onOpenMultiFloorModal={() => setScreen('review')}
          toast={toast}
          showToast={notify}
        />
        {showUploadModal && (
          <UploadModal
            close={() => setShowUploadModal(false)}
            onFileSelected={handleFileUpload}
            uploadState={uploadState}
            error={uploadError}
            onFallbackDemo={handleDemoUploadFallback}
          />
        )}
      </>
    );
  }

  if (screen === 'dashboard') {
    return (
      <>
        <Header onSwitchToTheme={() => setScreen('payton')} onNew={() => { setUploadState('idle'); setUploadError(''); setShowUploadModal(true); }} />
        <main className="dashboard">
          <section className="hero">
            <div className="hero-copy">
              <span className="eyebrow">FIRE & LIFE SAFETY REVIEW</span>
              <h1>Clearer egress<br /><em>starts here.</em></h1>
              <p>Review commercial floor plans with confidence. Spot distance and exit-capacity risks before they become site issues.</p>
              <div className="hero-buttons">
                <button className="primary" onClick={() => { setUploadState('idle'); setUploadError(''); setShowUploadModal(true); }}>
                  <Upload size={16} /> Upload a drawing
                </button>
                <button className="text-button" onClick={() => setScreen('review')}>
                  Open latest review <span>↗</span>
                </button>
              </div>
              <div className="hero-points">
                <span><i /> UAE code clauses</span>
                <span><i /> Real floor plan rendering</span>
                <span><i /> Multi-floor review</span>
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
                <span>94% extraction accuracy</span>
              </div>
              <div className="hero-stat">
                <b>{items.filter(x => x.status === 'open').length}</b>
                <span>open findings<br />in current review</span>
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
                  <input
                    placeholder="Search projects"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </section>
              <div className="projects">
                {projectsList.map(p => (
                  <Project
                    key={p.id}
                    title={p.title}
                    client={p.client}
                    floors={p.floors}
                    flags={p.flags}
                    status={p.status}
                    done={p.done}
                    action={() => {
                      setCurrentDrawingId(DEMO_DRAWING_ID);
                      setScreen('review');
                    }}
                  />
                ))}
              </div>
            </div>
            <section>
              <Metric icon={<AlertTriangle size={20} />} label="Critical findings" value={items.filter(x => x.severity === 'Critical' && x.status === 'open').length.toString()} sub="Require immediate review" danger={true} />
              <Metric icon={<Clock3 size={20} />} label="Pending reviews" value={items.filter(x => x.status === 'open').length.toString()} sub="Findings waiting sign-off" />
              <Metric icon={<CheckCircle2 size={20} />} label="Resolved / Reviewed" value={items.filter(x => x.status !== 'open').length.toString()} sub="Reviewed findings" />
            </section>
          </section>
        </main>
        {showUploadModal && (
          <UploadModal
            close={() => setShowUploadModal(false)}
            onFileSelected={handleFileUpload}
            uploadState={uploadState}
            error={uploadError}
            onFallbackDemo={handleDemoUploadFallback}
          />
        )}
        {toast && <div className="toast">{toast}</div>}
      </>
    );
  }

  const reviewedCount = items.filter(x => x.status !== 'open').length;
  const progressPercent = items.length > 0 ? Math.round((reviewedCount / items.length) * 100) : 0;

  return (
    <>
      <Header compact onSwitchToHome={() => setScreen('egress')} onNew={() => { setUploadState('idle'); setUploadError(''); setShowUploadModal(true); }} />
      <div className={`review mobile-tab-${mobileTab}`}>
        {/* Clean, Focused Left Sidebar */}
        <aside className={`sidebar ${mobileTab === 'info' ? 'mobile-active' : ''}`}>
          <button className="back" onClick={() => setScreen('egress')}>
            <ArrowLeft size={16} /> ← Back to EgressCo Home
          </button>

          <div className="project-mini">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span className="eyebrow" style={{ margin: 0 }}>ACTIVE DRAWING</span>
              <span style={{
                fontSize: '9.5px',
                fontWeight: 700,
                textTransform: 'uppercase',
                padding: '2px 8px',
                borderRadius: '4px',
                letterSpacing: '0.04em',
                background: drawingMeta.documentType === 'fire_alarm' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                color: drawingMeta.documentType === 'fire_alarm' ? '#ef4444' : '#3b82f6',
                border: drawingMeta.documentType === 'fire_alarm' ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(59, 130, 246, 0.3)'
              }}>
                {drawingMeta.documentType === 'fire_alarm' ? '🚨 Fire Alarm Shop Drawing' : '📐 Architectural Floor Plan'}
              </span>
            </div>
            <h2>{drawingMeta.floor || drawingMeta.name}</h2>
            <p className="sub-loc">Dubai, UAE • {drawingMeta.scale}</p>
          </div>

          <div className="sidebar-stats-grid">
            {drawingMeta.documentType === 'fire_alarm' ? (
              <>
                <div className="sb-stat-card">
                  <span className="sb-lbl">DEVICES</span>
                  <b>{elements.filter(e => e.type === 'fire_alarm_device' || ['smoke_detector', 'heat_detector', 'manual_call_point', 'sounder', 'fire_alarm_panel'].includes(e.type)).length} units</b>
                </div>
                <div className="sb-stat-card">
                  <span className="sb-lbl">DETECTORS</span>
                  <b>{elements.filter(e => e.type === 'smoke_detector' || e.type === 'heat_detector' || e.properties?.device_type === 'smoke_detector' || e.properties?.device_type === 'heat_detector').length} units</b>
                </div>
                <div className="sb-stat-card">
                  <span className="sb-lbl">MANUAL CALL</span>
                  <b>{elements.filter(e => e.type === 'manual_call_point' || e.properties?.device_type === 'manual_call_point').length} MCPs</b>
                </div>
                <div className="sb-stat-card">
                  <span className="sb-lbl">INGESTION</span>
                  <b className="text-green">✓ Extracted</b>
                </div>
              </>
            ) : (
              <>
                <div className="sb-stat-card">
                  <span className="sb-lbl">FLOOR AREA</span>
                  <b>{totalFloorArea > 0 ? `${totalFloorArea} m²` : '427 m²'}</b>
                </div>
                <div className="sb-stat-card">
                  <span className="sb-lbl">OCCUPANTS</span>
                  <b>{totalFloorOccupants > 0 ? `${totalFloorOccupants} p` : '227 p'}</b>
                </div>
                <div className="sb-stat-card">
                  <span className="sb-lbl">EXITS FOUND</span>
                  <b>{elements.filter(e => e.properties?.kind === 'exit' || e.properties?.kind === 'door').length || 2} doors</b>
                </div>
                <div className="sb-stat-card">
                  <span className="sb-lbl">STATUS</span>
                  <b className={items.length > 0 ? 'text-red' : 'text-green'}>
                    {items.length > 0 ? `${items.filter(x => x.status === 'open').length} Violations` : '✓ 100% Passed'}
                  </b>
                </div>
              </>
            )}
          </div>

          <div className="side-block">
            <span>OCCUPANCY & SAFETY SETUP</span>
            <div className="setup-pill">
              <small>CLASSIFICATION</small>
              <b>{drawingMeta.occupancy || 'Business - Regular office (9.3 m²/p)'}</b>
            </div>
          </div>

          <div className="side-block">
            <span>REVIEW PROGRESS</span>
            <div className="progress-row">
              <b>{reviewedCount} of {items.length} reviewed</b>
              <b>{progressPercent}%</b>
            </div>
            <div className="progress">
              <i style={{ width: `${progressPercent}%` }} />
            </div>
          </div>

          <div className="side-footer">
            <ShieldCheck size={16} /> UAE FLS Code of Practice (168 Clauses)
          </div>
        </aside>

        {/* Center Viewer */}
        <main className={`viewer ${mobileTab === 'plan' ? 'mobile-active' : ''}`}>
          {/* SINGLE UNIFIED TOP CONTROL BAR */}
          <div className="unified-top-bar">
            {/* Project Floor & Drawing Tabs */}
            {validProjectDrawings && validProjectDrawings.length > 1 ? (
              <div
                className="floor-tabs-unified"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  overflowX: 'auto',
                  flex: 1,
                  minWidth: 0,
                  paddingRight: '10px',
                  scrollbarWidth: 'none'
                }}
              >
                <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 800, whiteSpace: 'nowrap', marginRight: '4px' }}>
                  Floors:
                </span>
                {validProjectDrawings.map((d) => {
                  const isCur = d.id === currentDrawingId;
                  const isFa = d.document_type === 'fire_alarm';
                  const title = formatFloorTabTitle(d);
                  const errCount = d.violations_count !== undefined ? d.violations_count : 0;
                  return (
                    <button
                      key={`proj-drw-${d.id}`}
                      className={`floor-btn ${isCur ? 'active' : ''}`}
                      onClick={() => {
                        if (!isCur) {
                          setCurrentDrawingId(d.id);
                          notify(`Switched to ${title}`);
                        }
                      }}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '5px 12px',
                        borderRadius: '20px',
                        fontSize: '11px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                        transition: 'all 0.15s ease',
                        border: isCur
                          ? (isFa ? '1px solid #ef4444' : '1px solid #dc2626')
                          : '1px solid rgba(0,0,0,0.1)',
                        background: isCur
                          ? (isFa ? '#ef4444' : '#dc2626')
                          : 'var(--bg-muted, #f1f5f9)',
                        color: isCur ? '#ffffff' : 'var(--ink-secondary, #475569)'
                      }}
                      title={`${d.floor_name || d.name || title} (${d.elements_count || 0} elements)`}
                    >
                      <span>{title}</span>
                      {isFa ? (
                        <span style={{
                          fontSize: '9px',
                          fontWeight: 800,
                          padding: '1px 5px',
                          borderRadius: '8px',
                          background: isCur ? 'rgba(0,0,0,0.25)' : 'rgba(239, 68, 68, 0.15)',
                          color: isCur ? '#ffffff' : '#ef4444'
                        }}>
                          {d.elements_count || 0} dev
                        </span>
                      ) : (
                        <span
                          className={`err-pill ${errCount > 0 ? 'err' : 'ok'}`}
                          style={isCur ? { background: 'rgba(0,0,0,0.25)', color: '#ffffff' } : {}}
                        >
                          {errCount > 0 ? `${errCount} ⚠️` : '✓'}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            ) : (
              /* Fallback for single drawing with multi-page PDF floors */
              multiFloorSummary?.floors && multiFloorSummary.floors.length > 1 ? (
                <div className="floor-tabs-unified" style={{ display: 'flex', alignItems: 'center', gap: '6px', overflowX: 'auto', flex: 1, minWidth: 0, paddingRight: '10px' }}>
                  <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 800, whiteSpace: 'nowrap', marginRight: '4px' }}>
                    Floors:
                  </span>
                  {multiFloorSummary.floors.map((p) => {
                    const isActive = p.index === drawingMeta.pageIndex;
                    let cleanTitle = p.title || `Level 0${p.index}`;
                    if (cleanTitle.toLowerCase().includes('ground') || p.index === 0) {
                      cleanTitle = 'Level 00 (Ground)';
                    } else if (!cleanTitle.toLowerCase().includes('level')) {
                      cleanTitle = `Level 0${p.index}`;
                    }
                    const errCount = p.violations_count !== undefined ? p.violations_count : (p.violations ? p.violations.length : 0);
                    return (
                      <button
                        key={`floor-tab-${p.index}`}
                        className={`floor-btn ${isActive ? 'active' : ''}`}
                        onClick={() => handleFloorSwitch(p.index)}
                      >
                        <span>{cleanTitle}</span>
                        <span className={`err-pill ${errCount > 0 ? 'err' : 'ok'}`}>
                          {errCount > 0 ? `${errCount} ⚠️` : '✓'}
                        </span>
                      </button>
                    );
                  })}
                </div>
              ) : null
            )}

            {/* View mode & actions */}
            <div className="top-actions">
              <div className="view-mode-group">
                <button
                  className={`view-mode-btn ${viewMode === 'hybrid' ? 'active' : ''}`}
                  onClick={() => setViewMode('hybrid')}
                  title="PDF Drawing with compliance overlays"
                >
                  ✨ Hybrid
                </button>
                <button
                  className={`view-mode-btn ${viewMode === 'vector' ? 'active' : ''}`}
                  onClick={() => setViewMode('vector')}
                  title="CAD Vector blueprint mode"
                >
                  📐 Vector CAD
                </button>
                {drawingMeta.hasImage && (
                  <button
                    className={`view-mode-btn ${viewMode === 'image' ? 'active' : ''}`}
                    onClick={() => setViewMode('image')}
                    title="Original PDF image"
                  >
                    📄 Original PDF
                  </button>
                )}
              </div>

              <button
                className={`secondary fullscreen-btn-top ${isFullScreen ? 'active' : ''}`}
                onClick={() => setIsFullScreen(prev => !prev)}
                title={isFullScreen ? "Exit Fullscreen (Esc)" : "Full Screen View (F)"}
              >
                {isFullScreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                <span>{isFullScreen ? "Exit" : "Full Screen"}</span>
              </button>

              <button
                className="secondary all-floors-btn"
                onClick={() => setShowMultiFloorOverview(true)}
                title="View All Building Floors and Error Breakdown"
              >
                <Grid size={14} /> All Floors ({multiFloorSummary?.total_pages || 5})
              </button>

              <button className="primary export-btn" onClick={exportCsv}>
                <Download size={14} /> Export Report
              </button>
            </div>
          </div>

          <div className="content">
            {/* Floor Plan Viewport */}
            <section className="plan-wrap">
              <FloorPlan
                activeId={active?.id || selected}
                select={setSelected}
                elements={elements}
                findings={items}
                loading={elementsLoading}
                currentDrawingId={currentDrawingId}
                drawingMeta={drawingMeta}
                viewMode={viewMode}
                setViewMode={setViewMode}
                isFullScreen={isFullScreen}
                setIsFullScreen={setIsFullScreen}
                handleFloorSwitch={handleFloorSwitch}
                selectedDeviceId={selectedDeviceId}
                setSelectedDeviceId={setSelectedDeviceId}
                hoveredDevice={hoveredDevice}
                setHoveredDevice={setHoveredDevice}
              />
            </section>

            <aside className={`findings ${mobileTab === 'findings' ? 'mobile-active' : ''}`}>
              {drawingMeta.documentType === 'fire_alarm' ? (
                <div className="fire-alarm-sidebar-wrap" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <div className="find-head">
                    <div>
                      <h2>Fire Alarm Devices <span className="count-badge" style={{ background: '#ef4444' }}>{elements.filter(e => e.type === 'fire_alarm_device' || ['smoke_detector', 'heat_detector', 'manual_call_point', 'sounder', 'fire_alarm_panel'].includes(e.type)).length} detected</span></h2>
                      <p>DXF point symbol extraction & coordinates</p>
                    </div>
                  </div>

                  {/* Scope Boundary Notice */}
                  <div style={{ margin: '10px 14px', padding: '10px 12px', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.25)', borderRadius: '6px', fontSize: '11px', color: '#93c5fd' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, marginBottom: '3px' }}>
                      <CheckCircle2 size={13} style={{ color: '#60a5fa' }} />
                      <span>Phase 1 Ingestion: Symbol Extraction Only</span>
                    </div>
                    <span style={{ opacity: 0.88, lineHeight: 1.4, display: 'block' }}>
                      Coordinates and tags extracted from CAD layers. Rule evaluation and cross-document linking will be performed in subsequent phase.
                    </span>
                  </div>

                  {/* Device Type Summary Pills */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px', padding: '0 14px 10px 14px' }}>
                    <div style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '6px', padding: '7px 9px' }}>
                      <span style={{ fontSize: '9.5px', color: '#fca5a5', textTransform: 'uppercase', fontWeight: 700 }}>Smoke Detectors</span>
                      <div style={{ fontSize: '16px', fontWeight: 800, color: '#ef4444', marginTop: '2px' }}>
                        {elements.filter(e => e.type === 'smoke_detector' || e.properties?.device_type === 'smoke_detector').length} units
                      </div>
                    </div>
                    <div style={{ background: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.25)', borderRadius: '6px', padding: '7px 9px' }}>
                      <span style={{ fontSize: '9.5px', color: '#fde68a', textTransform: 'uppercase', fontWeight: 700 }}>Heat Detectors</span>
                      <div style={{ fontSize: '16px', fontWeight: 800, color: '#f59e0b', marginTop: '2px' }}>
                        {elements.filter(e => e.type === 'heat_detector' || e.properties?.device_type === 'heat_detector').length} units
                      </div>
                    </div>
                    <div style={{ background: 'rgba(220, 38, 38, 0.12)', border: '1px solid rgba(220, 38, 38, 0.25)', borderRadius: '6px', padding: '7px 9px' }}>
                      <span style={{ fontSize: '9.5px', color: '#fca5a5', textTransform: 'uppercase', fontWeight: 700 }}>Manual Call Points</span>
                      <div style={{ fontSize: '16px', fontWeight: 800, color: '#dc2626', marginTop: '2px' }}>
                        {elements.filter(e => e.type === 'manual_call_point' || e.properties?.device_type === 'manual_call_point').length} MCPs
                      </div>
                    </div>
                    <div style={{ background: 'rgba(139, 92, 246, 0.12)', border: '1px solid rgba(139, 92, 246, 0.25)', borderRadius: '6px', padding: '7px 9px' }}>
                      <span style={{ fontSize: '9.5px', color: '#c4b5fd', textTransform: 'uppercase', fontWeight: 700 }}>Sounders & Panel</span>
                      <div style={{ fontSize: '16px', fontWeight: 800, color: '#a78bfa', marginTop: '2px' }}>
                        {elements.filter(e => ['sounder', 'fire_alarm_panel'].includes(e.type) || ['sounder_beacon', 'fire_alarm_control_panel'].includes(e.properties?.device_type)).length} units
                      </div>
                    </div>
                  </div>

                  {/* Device List */}
                  <div className="finding-list" style={{ flex: 1, overflowY: 'auto' }}>
                    {elementsLoading && (
                      <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Extracting point symbols...</p>
                      </div>
                    )}
                    {!elementsLoading && elements.filter(e => e.type === 'fire_alarm_device' || ['smoke_detector', 'heat_detector', 'manual_call_point', 'sounder', 'fire_alarm_panel'].includes(e.type)).map((dev, idx) => {
                      const p = dev.properties || {};
                      const isChosen = selectedDeviceId === dev.id;
                      const devType = p.device_type || dev.type;
                      return (
                        <div
                          key={dev.id || idx}
                          onClick={() => setSelectedDeviceId(isChosen ? null : dev.id)}
                          className={`finding-card ${isChosen ? 'selected' : ''}`}
                          style={{ cursor: 'pointer', borderLeft: isChosen ? '3px solid #ef4444' : '3px solid transparent' }}
                        >
                          <div className="fc-top-row">
                            <div className="fc-pin-num" style={{ background: devType.includes('smoke') ? '#ef4444' : devType.includes('heat') ? '#f59e0b' : devType.includes('mcp') || devType.includes('manual') ? '#dc2626' : '#8b5cf6' }}>
                              {idx + 1}
                            </div>
                            <div className="fc-room-title">
                              <b>{p.tag || `${devType.replace(/_/g, ' ')} #${idx + 1}`}</b>
                              <span className="fc-kind" style={{ textTransform: 'capitalize' }}>{devType.replace(/_/g, ' ')}</span>
                            </div>
                            <span className="fc-sev-tag" style={{ background: 'rgba(255,255,255,0.08)', color: '#94a3b8' }}>{p.layer || 'FA-LAYER'}</span>
                          </div>

                          <div className="fc-compare-box" style={{ marginTop: '8px' }}>
                            <div className="fc-c-item">
                              <small>PHYSICAL COORD (X, Y)</small>
                              <b style={{ fontFamily: 'monospace', color: '#38bdf8' }}>
                                {p.x_m !== undefined ? `${p.x_m}m, ${p.y_m}m` : (p.pos_m ? `${p.pos_m[0]}m, ${p.pos_m[1]}m` : 'N/A')}
                              </b>
                            </div>
                            <div className="fc-c-item">
                              <small>SVG NORM (X%, Y%)</small>
                              <b style={{ fontFamily: 'monospace', color: '#a3e635' }}>
                                {dev.geometry?.coordinates ? `${dev.geometry.coordinates[0]}%, ${dev.geometry.coordinates[1]}%` : 'N/A'}
                              </b>
                            </div>
                          </div>

                          {/* Phase 2b: Cross-Document Linked Room Tag */}
                          <div style={{ marginTop: '8px', padding: '5px 8px', borderRadius: '4px', background: p.linked_room_name && !p.linked_room_name.includes('corridor') ? 'rgba(34, 197, 94, 0.12)' : 'rgba(148, 163, 184, 0.12)', border: p.linked_room_name && !p.linked_room_name.includes('corridor') ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(148, 163, 184, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
                            <span style={{ color: p.linked_room_name && !p.linked_room_name.includes('corridor') ? '#86efac' : '#cbd5e1', fontWeight: 700 }}>
                              {p.linked_room_name ? (p.linked_room_name.includes('corridor') ? '🚪 unassigned - corridor' : '📍 ' + p.linked_room_name) : '⏳ Linking...'}
                            </span>
                            <span style={{ fontSize: '10px', textTransform: 'uppercase', opacity: 0.85, color: p.linked_room_name && !p.linked_room_name.includes('corridor') ? '#22c55e' : '#94a3b8' }}>
                              {p.linking_status === 'assigned_room' ? 'Room Linked' : 'Circulation'}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <>
                  <div className="find-head">
                    <div>
                      <h2>Safety Findings <span className="count-badge">{items.filter(x => x.status === 'open').length} open</span></h2>
                      <p>Click any card or floor pin to inspect.</p>
                    </div>
                  </div>

                  <div className="finding-list">
                    {violationsLoading && (
                      <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Analyzing floor plan...</p>
                      </div>
                    )}
                    {violationsError && !violationsLoading && (
                      <div className="error-state">
                        <AlertTriangle size={20} />
                        <p><strong>Notice</strong>: {violationsError}</p>
                      </div>
                    )}
                    {!violationsLoading && items.length === 0 && (
                      <div className="empty-state">
                        <CheckCircle2 size={28} />
                        <p>100% Compliant</p>
                        <small>All travel distances & exit capacities on this floor satisfy UAE Fire & Life Safety Code requirements.</small>
                      </div>
                    )}
                    {!violationsLoading && items.map((f, idx) => {
                      const isSelected = f.id === selected;
                      const isDone = f.status !== 'open';
                      return (
                        <div
                          key={f.id}
                          onClick={() => setSelected(isSelected ? null : f.id)}
                          className={`finding-card ${isSelected ? 'selected' : ''} ${isDone ? 'done' : ''}`}
                        >
                          <div className="fc-top-row">
                            <div className="fc-pin-num">{idx + 1}</div>
                            <div className="fc-room-title">
                              <b>{f.roomName}</b>
                              <span className="fc-kind">{f.kind || 'Travel Distance'}</span>
                            </div>
                            <span className={`fc-sev-tag ${f.severity?.toLowerCase()}`}>{f.severity}</span>
                          </div>

                          <p className="fc-desc">{f.shortTitle || f.title}</p>

                          <div className="fc-compare-box">
                            <div className="fc-c-item">
                              <small>MEASURED</small>
                              <b className="val-danger">{f.measured}</b>
                            </div>
                            <div className="fc-c-item">
                              <small>UAE CODE LIMIT</small>
                              <b className="val-safe">{f.limit}</b>
                            </div>
                          </div>

                          <div className="fc-bottom-row">
                            <span className="fc-clause-chip">{f.clause}</span>
                            <span className="fc-inspect-link">Inspect Clause ↗</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
            </aside>
          </div>
        </main>
      </div>

      {/* Mobile Bottom Navigation Dock */}
      <div className="mobile-review-nav">
        <button
          className={`mob-nav-item ${mobileTab === 'plan' ? 'active' : ''}`}
          onClick={() => setMobileTab('plan')}
        >
          <Layers size={17} />
          <span>Floor Plan</span>
        </button>
        <button
          className={`mob-nav-item ${mobileTab === 'findings' ? 'active' : ''}`}
          onClick={() => setMobileTab('findings')}
        >
          <AlertTriangle size={17} />
          <span>Findings</span>
          {items.filter(x => x.status === 'open').length > 0 && (
            <span className="mob-badge">{items.filter(x => x.status === 'open').length}</span>
          )}
        </button>
        <button
          className={`mob-nav-item ${mobileTab === 'info' ? 'active' : ''}`}
          onClick={() => setMobileTab('info')}
        >
          <Building2 size={17} />
          <span>Overview</span>
        </button>
      </div>

      {/* Slide-over finding inspection drawer */}
      {selected && active && (
        <>
          <div className="detail-backdrop" onClick={() => setSelected(null)} />
          <div className="detail-panel">

          <div className="detail-head">
            <div className="detail-title-group">
              <span className={`severity ${active.severity?.toLowerCase()}`}>{active.severity}</span>
              <span className="flag-kind">{active.kind}</span>
            </div>
            <button className="detail-close" onClick={() => setSelected(null)} aria-label="Close detail panel">
              <X size={18} />
            </button>
          </div>
          <div className="detail-body">
            <div className="detail-header-row">
              <span className="flag-id-large">{active.id}</span>
              <h2>{active.title}</h2>
            </div>
            <div className="detail-grid">
              <div className="detail-card">
                <small>CODE CLAUSE</small>
                <code>{active.clause}</code>
              </div>
              <div className="detail-card">
                <small>LOCATION</small>
                <p>{active.detail}</p>
              </div>
              <div className="detail-card">
                <small>MEASURED VALUE</small>
                <p className="val danger">{active.measured}</p>
              </div>
              <div className="detail-card">
                <small>CODE LIMIT</small>
                <p className="val safe">{active.limit}</p>
              </div>
            </div>

            <div className="detail-status-banner">
              <span>CURRENT STATUS: <b>{active.status.toUpperCase().replace('_', ' ')}</b></span>
            </div>

            <div className="detail-actions">
              {active.status === 'open' && (
                <>
                  <button className="secondary" onClick={() => update('false_positive')}>
                    Mark False Positive
                  </button>
                  <button className="primary" onClick={() => update('confirmed')}>
                    <Check size={15} /> Confirm Finding
                  </button>
                </>
              )}
              {active.status === 'confirmed' && (
                <>
                  <button className="secondary" onClick={() => update('open')}>
                    <RefreshCw size={14} /> Reopen
                  </button>
                  <button className="primary" onClick={() => update('resolved')}>
                    <CheckCircle2 size={15} /> Mark Resolved
                  </button>
                </>
              )}
              {active.status === 'resolved' && (
                <button className="secondary full-w" onClick={() => update('open')}>
                  <RefreshCw size={14} /> Reopen Finding
                </button>
              )}
              {active.status === 'false_positive' && (
                <button className="secondary full-w" onClick={() => update('open')}>
                  <RefreshCw size={14} /> Reopen Finding
                </button>
              )}
            </div>
          </div>
        </div>
      </>
    )}


      {showUploadModal && (
        <UploadModal
          close={() => setShowUploadModal(false)}
          onFileSelected={handleFileUpload}
          uploadState={uploadState}
          error={uploadError}
          onFallbackDemo={handleDemoUploadFallback}
        />
      )}
      {showMultiFloorOverview && (
        <MultiFloorOverviewModal
          isOpen={showMultiFloorOverview}
          onClose={() => setShowMultiFloorOverview(false)}
          summary={multiFloorSummary}
          currentDrawingId={currentDrawingId}
          activePageIndex={drawingMeta.pageIndex}
          onSelectFloor={handleFloorSwitch}
        />
      )}
      {toast && <div className="toast">{toast}</div>}
    </>
  );
}

const Header = ({ onNew, compact, onSwitchToHome }) => (
  <header className="egress-review-header">
    <div className="brand" onClick={onSwitchToHome} style={{ cursor: 'pointer' }} title="Return to EgressCo Home">
      <div className="brand-lockup-inline">
        <span className="brand-bold">EGRESS</span>
        <span className="brand-light">CO</span>
        <span className="brand-sq"></span>
      </div>
      <small style={{ background: '#FEF2F2', color: '#DC2626', border: '1px solid #FECACA', marginLeft: '8px' }}>UAE FLSC 2018</small>
    </div>
    {compact ? (
      <div className="user">
        {onSwitchToHome && (
          <button className="secondary small" onClick={onSwitchToHome} style={{ marginRight: '8px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <ArrowLeft size={13} /> Home Page
          </button>
        )}
        <button className="primary small header-upload-btn" onClick={onNew} style={{ background: 'var(--egress-crimson)' }}>
          <Upload size={14} /> Upload Plan
        </button>
        <span className="avatar" style={{ background: '#1E293B', color: '#FFFFFF' }}>EA</span> Eng. Ahmed <ChevronDown size={15} />
      </div>
    ) : (
      <nav>
        {onSwitchToHome && (
          <button className="secondary small" onClick={onSwitchToHome}>
            <ArrowLeft size={13} /> Home
          </button>
        )}
        <a className="active"><LayoutDashboard size={16} /> Audit Workspace</a>
        <a>UAE Code Library (168 Clauses)</a>
        <button className="primary small" onClick={onNew} style={{ background: 'var(--egress-crimson)' }}>
          <Upload size={16} /> Upload Plan
        </button>
        <span className="avatar" style={{ background: '#1E293B', color: '#FFFFFF' }}>EA</span>
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
    <div className="project-floors-col"><small>FLOORS</small><b>{floors}</b></div>
    <div className="project-flags-col"><small>FINDINGS</small><b className={done ? 'success' : ''}>{flags}</b></div>
    <div className="project-status-col">
      <span className={'status ' + (done ? 'complete' : '')}>
        {done ? <CheckCircle2 size={14} /> : <Clock3 size={14} />} {status}
      </span>
    </div>
    <ChevronDown className="chev" size={18} />
  </button>
);


function FloorPlan({
  activeId,
  select,
  elements,
  findings,
  loading,
  currentDrawingId,
  drawingMeta,
  viewMode,
  setViewMode,
  isFullScreen,
  setIsFullScreen,
  handleFloorSwitch,
  selectedDeviceId,
  setSelectedDeviceId,
  hoveredDevice,
  setHoveredDevice
}) {
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showPills, setShowPills] = useState(true);
  const [showPins, setShowPins] = useState(true);
  const [showExits, setShowExits] = useState(true);
  const [showCadWalls, setShowCadWalls] = useState(false);
  const [overlayOpacity, setOverlayOpacity] = useState(0.72);
  const [hoveredRoom, setHoveredRoom] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  // Zoom & Pan interactive state
  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [showFindingsInFullscreen, setShowFindingsInFullscreen] = useState(true);

  const isRealDrawing = elements && elements.length > 0;

  const roomElements = isRealDrawing ? elements.filter(e => e.type === 'room') : [];
  const wallElements = isRealDrawing ? elements.filter(e => e.type === 'wall') : [];
  const doorElements = isRealDrawing ? elements.filter(e => e.type === 'door' && !e.properties?.is_exit) : [];
  const exitElements = isRealDrawing ? elements.filter(e => e.type === 'exit' || e.properties?.is_exit === true) : [];
  const fireAlarmElements = isRealDrawing ? elements.filter(e => 
    e.type === 'fire_alarm_device' || 
    ['smoke_detector', 'heat_detector', 'manual_call_point', 'sounder', 'fire_alarm_panel'].includes(e.type)
  ) : [];

  // Generate image source URL with active page and cache-busting timestamp
  const imageSrc = drawingMeta.hasImage
    ? `${API_URL}/drawings/${currentDrawingId}/image?page=${drawingMeta.pageIndex || 0}&t=${drawingMeta.imageTimestamp || ''}`
    : null;

  const selectedFinding = findings?.find(f => f.id === activeId);
  const activeRoom = roomElements.find(el => {
    const name = el.properties?.name || '';
    return (selectedFinding && (selectedFinding.title?.includes(name) || selectedFinding.detail?.includes(name)))
      || (hoveredRoom && hoveredRoom.name === name);
  });

  const planRef = useRef(null);

  // Zoom & Pan Handlers
  const handleZoomIn = () => setZoom(prev => Math.min(4.0, Math.round((prev + 0.25) * 100) / 100));
  const handleZoomOut = () => setZoom(prev => Math.max(0.5, Math.round((prev - 0.25) * 100) / 100));
  const handleResetZoom = () => {
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
  };

  // Active non-passive mouse wheel listener to strictly prevent browser tab zoom
  useEffect(() => {
    const el = planRef.current;
    if (!el) return;

    const handleWheelEvent = (e) => {
      e.preventDefault();
      e.stopPropagation();

      const isPinch = e.ctrlKey || e.metaKey;
      const step = isPinch ? 0.04 : 0.12;
      const delta = e.deltaY < 0 ? step : -step;

      setZoom(prev => Math.min(4.0, Math.max(0.5, Math.round((prev + delta) * 100) / 100)));
    };

    el.addEventListener('wheel', handleWheelEvent, { passive: false });
    return () => el.removeEventListener('wheel', handleWheelEvent);
  }, [isFullScreen]);

  // CAD Navigation: Spacebar and Middle-click drag listeners
  const handleMouseDown = (e) => {
    if (e.button === 0 || e.button === 1 || isSpacePressed) {
      if (e.button === 1) e.preventDefault();
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Mobile Touch Gestures: Single finger drag pan & Two-finger pinch zoom
  const touchRef = useRef({ mode: 'none', startPan: { x: 0, y: 0 }, startTouch: { x: 0, y: 0 }, startDist: 0, startZoom: 1.0 });

  const handleTouchStart = (e) => {
    if (e.touches.length === 1) {
      const t = e.touches[0];
      touchRef.current = {
        mode: 'pan',
        startPan: { ...pan },
        startTouch: { x: t.clientX, y: t.clientY },
        startDist: 0,
        startZoom: zoom
      };
      setIsDragging(true);
    } else if (e.touches.length === 2) {
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
      touchRef.current = {
        mode: 'pinch',
        startPan: { ...pan },
        startTouch: { x: (t1.clientX + t2.clientX) / 2, y: (t1.clientY + t2.clientY) / 2 },
        startDist: dist,
        startZoom: zoom
      };
      setIsDragging(true);
    }
  };

  const handleTouchMove = (e) => {
    if (touchRef.current.mode === 'pan' && e.touches.length === 1) {
      const t = e.touches[0];
      const dx = t.clientX - touchRef.current.startTouch.x;
      const dy = t.clientY - touchRef.current.startTouch.y;
      setPan({
        x: touchRef.current.startPan.x + dx,
        y: touchRef.current.startPan.y + dy
      });
    } else if (touchRef.current.mode === 'pinch' && e.touches.length === 2) {
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
      if (touchRef.current.startDist > 0) {
        const factor = dist / touchRef.current.startDist;
        const newZoom = Math.min(4.0, Math.max(0.5, Math.round(touchRef.current.startZoom * factor * 100) / 100));
        setZoom(newZoom);
      }
    }
  };

  const handleTouchEnd = (e) => {
    if (e.touches.length === 0) {
      touchRef.current = { mode: 'none', startPan: { x: 0, y: 0 }, startTouch: { x: 0, y: 0 }, startDist: 0, startZoom: 1.0 };
      setIsDragging(false);
    } else if (e.touches.length === 1) {
      const t = e.touches[0];
      touchRef.current = {
        mode: 'pan',
        startPan: { ...pan },
        startTouch: { x: t.clientX, y: t.clientY },
        startDist: 0,
        startZoom: zoom
      };
    }
  };

  // Keyboard navigation & CAD shortcuts (Spacebar pan, Z to fit, 0, +, -)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) return;
      if (e.code === 'Space' && !e.repeat) {
        setIsSpacePressed(true);
      } else if (e.key === 'Escape' && isFullScreen) {
        setIsFullScreen(false);
      } else if (e.key === 'f' || e.key === 'F') {
        setIsFullScreen(prev => !prev);
      } else if (e.key === '+' || e.key === '=') {
        handleZoomIn();
      } else if (e.key === '-' || e.key === '_') {
        handleZoomOut();
      } else if (e.key === '0' || e.key === 'z' || e.key === 'Z' || (e.shiftKey && e.key === '!')) {
        handleResetZoom();
      }
    };

    const handleKeyUp = (e) => {
      if (e.code === 'Space') {
        setIsSpacePressed(false);
        setIsDragging(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isFullScreen]);

  // Reset pan when floor changes
  useEffect(() => {
    setPan({ x: 0, y: 0 });
  }, [currentDrawingId, drawingMeta.pageIndex]);

  // Layer Controls Bar JSX
  const renderLayerControls = (isFs = false) => (
    <div className={`layer-controls-bar ${isFs ? 'fullscreen-controls-bar' : ''}`}>
      <div className="layer-toggles">
        <span className="layer-label"><Sliders size={12} /> LAYERS:</span>
        <button
          className={`layer-chip ${showHeatmap ? 'active' : ''}`}
          onClick={() => setShowHeatmap(!showHeatmap)}
          title="Toggle compliance zone heatmaps on rooms"
        >
          🌡️ Heatmap
        </button>
        <button
          className={`layer-chip ${showPills ? 'active' : ''}`}
          onClick={() => setShowPills(!showPills)}
          title="Toggle room compliance info badges"
        >
          🏷️ Badges
        </button>
        <button
          className={`layer-chip ${showPins ? 'active' : ''}`}
          onClick={() => setShowPins(!showPins)}
          title="Toggle finding hazard markers"
        >
          ⚠️ Safety Pins
        </button>
        <button
          className={`layer-chip ${showExits ? 'active' : ''}`}
          onClick={() => setShowExits(!showExits)}
          title="Toggle emergency exits & escape paths"
        >
          🚪 Exits & Routes
        </button>
        {(viewMode === 'hybrid' || isFs) && (
          <button
            className={`layer-chip ${showCadWalls ? 'active' : ''}`}
            onClick={() => setShowCadWalls(!showCadWalls)}
            title="Toggle vector CAD wall lines overlay"
          >
            📐 CAD Lines
          </button>
        )}
      </div>

      <div className="layer-right-controls">
        <div className="layer-slider-group">
          <span className="slider-lbl">Opacity:</span>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={overlayOpacity}
            onChange={(e) => setOverlayOpacity(parseFloat(e.target.value))}
            className="opacity-slider"
            title={`Overlay Opacity: ${Math.round(overlayOpacity * 100)}%`}
          />
          <span className="opacity-val">{Math.round(overlayOpacity * 100)}%</span>
        </div>

        {/* Zoom & Pan Toolbar */}
        <div className="canvas-zoom-toolbar">
          <button
            className="zoom-btn"
            onClick={handleZoomOut}
            title="Zoom Out (-)"
          >
            <ZoomOut size={13} />
          </button>
          <span className="zoom-indicator" title="Click to reset zoom (0)" onClick={handleResetZoom}>
            {Math.round(zoom * 100)}%
          </span>
          <button
            className="zoom-btn"
            onClick={handleZoomIn}
            title="Zoom In (+)"
          >
            <ZoomIn size={13} />
          </button>
          <button
            className="zoom-btn reset-btn"
            onClick={handleResetZoom}
            title="Fit to Screen / Reset (0)"
          >
            <RotateCcw size={12} />
          </button>
          <div className="zoom-divider" />
          <button
            className={`fullscreen-btn ${isFullScreen ? 'active' : ''}`}
            onClick={() => setIsFullScreen(!isFullScreen)}
            title={isFullScreen ? "Exit Fullscreen (Esc)" : "Full Screen View (F)"}
          >
            {isFullScreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
            <span>{isFullScreen ? "Exit" : "Full Screen"}</span>
          </button>
        </div>
      </div>
    </div>
  );

  // Plan Canvas Stage JSX
  const renderPlanCanvas = (isFs = false) => (
    <div
      ref={planRef}
      className={`plan ${viewMode === 'vector' ? 'blueprint-mode' : ''} ${isFs ? 'fullscreen-stage' : ''}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => {
        setIsDragging(false);
        setHoveredRoom(null);
      }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onTouchCancel={handleTouchEnd}
      style={{
        cursor: isDragging ? 'grabbing' : isSpacePressed ? 'grab' : zoom > 1.05 ? 'grab' : 'default',
        touchAction: 'none'
      }}
    >
      {loading && (
        <div className="canvas-loading-overlay">
          <div className="spinner"></div>
          <span>Analyzing drawing geometry...</span>
        </div>
      )}

      {/* Pannable & Zoomable Stage */}
      <div
        className="plan-canvas-stage"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: 'center center',
          transition: isDragging ? 'none' : 'transform 0.12s ease-out'
        }}
      >
        <svg viewBox="0 0 100 100" className="plan-svg" preserveAspectRatio="none">
          <defs>
            <pattern id="arch-grid" width="5" height="5" patternUnits="userSpaceOnUse">
              <path d="M 5 0 L 0 0 0 5" fill="none" stroke={viewMode === 'vector' ? '#253549' : '#f0ebe4'} strokeWidth="0.25" />
            </pattern>
            <filter id="glow-danger" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="0.8" floodColor="#ef4444" floodOpacity="0.6" />
            </filter>
            <filter id="glow-safe" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="0.6" floodColor="#22c55e" floodOpacity="0.5" />
            </filter>
          </defs>

          {/* 1. Background Grid Pattern */}
          <rect width="100" height="100" fill={viewMode === 'vector' ? '#0f172a' : '#fffdf9'} />
          {viewMode !== 'image' && <rect width="100" height="100" fill="url(#arch-grid)" />}

          {/* 2. Real Rendered Architectural PDF Image Backdrop */}
          {imageSrc && viewMode !== 'vector' && (
            <image
              href={imageSrc}
              x="0"
              y="0"
              width="100"
              height="100"
              preserveAspectRatio="none"
              opacity={viewMode === 'image' ? 1.0 : 0.94}
            />
          )}

          {/* 3. Dynamic Vector CAD Compliance Layer with adjustable opacity */}
          {isRealDrawing && (
            <g className="cad-dynamic-layer" opacity={viewMode === 'image' ? 0.0 : overlayOpacity}>
              {/* Dynamic Room Polygons & Compliance Heatmaps */}
              {showHeatmap && roomElements.map((el, idx) => {
                const geom = el.geometry;
                const props = el.properties || {};
                if (!geom || geom.type !== 'Polygon') return null;
                const coords = geom.coordinates[0];
                const points = coords.map(c => `${c[0]},${c[1]}`).join(' ');
                const nameUpper = (props.name || '').toUpperCase();
                const isStair = nameUpper.includes('STAIR');
                const isLift = nameUpper.includes('LIFT');
                
                const relatedFinding = findings?.find(f => f.title?.includes(props.name) || f.detail?.includes(props.name));
                const isSelected = activeId && (activeId === relatedFinding?.id || (selectedFinding && (selectedFinding.title?.includes(props.name) || selectedFinding.detail?.includes(props.name))));
                const hasViolation = Boolean(relatedFinding);
                const isHovered = hoveredRoom?.name === props.name;

                let fillColor = 'rgba(255, 255, 255, 0.05)';
                let strokeColor = 'rgba(140, 130, 118, 0.4)';
                let strokeWidth = '0.35';

                if (viewMode === 'vector' || !imageSrc) {
                  fillColor = isSelected ? 'rgba(239, 68, 68, 0.35)' : hasViolation ? 'rgba(249, 115, 22, 0.25)' : isStair ? 'rgba(34, 197, 94, 0.25)' : isLift ? 'rgba(234, 179, 8, 0.20)' : 'rgba(30, 41, 59, 0.6)';
                  strokeColor = isSelected ? '#ef4444' : hasViolation ? '#f97316' : isStair ? '#22c55e' : '#475569';
                  strokeWidth = isSelected ? '0.7' : '0.4';
                } else {
                  if (isSelected) {
                    fillColor = 'rgba(239, 68, 68, 0.26)';
                    strokeColor = '#ef4444';
                    strokeWidth = '0.75';
                  } else if (isHovered) {
                    fillColor = hasViolation ? 'rgba(239, 68, 68, 0.22)' : 'rgba(34, 197, 94, 0.18)';
                    strokeColor = hasViolation ? '#ef4444' : '#16a34a';
                    strokeWidth = '0.6';
                  } else if (hasViolation) {
                    fillColor = 'rgba(249, 115, 22, 0.18)';
                    strokeColor = '#ea580c';
                    strokeWidth = '0.55';
                  } else if (isStair) {
                    fillColor = 'rgba(34, 197, 94, 0.16)';
                    strokeColor = '#16a34a';
                    strokeWidth = '0.4';
                  } else if (isLift) {
                    fillColor = 'rgba(234, 179, 8, 0.14)';
                    strokeColor = '#ca8a04';
                    strokeWidth = '0.4';
                  } else {
                    fillColor = 'rgba(241, 245, 249, 0.08)';
                    strokeColor = 'rgba(100, 116, 139, 0.45)';
                  }
                }

                return (
                  <polygon
                    key={`room-poly-${idx}`}
                    points={points}
                    fill={fillColor}
                    stroke={strokeColor}
                    strokeWidth={strokeWidth}
                    strokeDasharray={hasViolation ? '1.2, 0.8' : 'none'}
                    className={`room-poly ${isSelected ? 'selected' : ''} ${hasViolation ? 'violation' : ''}`}
                    onMouseEnter={() => setHoveredRoom({ ...props, hasViolation, relatedFinding })}
                    onMouseLeave={() => setHoveredRoom(null)}
                    onClick={() => {
                      if (relatedFinding) {
                        select(isSelected ? null : relatedFinding.id);
                      }
                    }}
                  />
                );
              })}

              {/* Active Egress Escape Route Path */}
              {showExits && activeRoom && activeRoom.properties?.connection_path && (
                <g className="active-escape-route-group">
                  <polyline
                    points={activeRoom.properties.connection_path.map(c => `${c[0]},${c[1]}`).join(' ')}
                    fill="none"
                    stroke="#ef4444"
                    strokeWidth="0.65"
                    strokeDasharray="1.5, 1.0"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="escape-path-line"
                  />
                  {activeRoom.properties.centroid && (
                    <circle
                      cx={activeRoom.properties.centroid[0]}
                      cy={activeRoom.properties.centroid[1]}
                      r="1.0"
                      fill="#ef4444"
                      className="pulse-start"
                    />
                  )}
                </g>
              )}

              {/* Dynamic Wall LineStrings */}
              {(viewMode === 'vector' || showCadWalls || !imageSrc) && wallElements.map((el, idx) => {
                const geom = el.geometry;
                if (!geom) return null;
                const strokeColor = viewMode === 'vector' || !imageSrc ? '#94a3b8' : '#475569';
                const strokeW = viewMode === 'vector' || !imageSrc ? '0.7' : '0.45';

                if (geom.type === 'LineString' && Array.isArray(geom.coordinates)) {
                  const pts = geom.coordinates;
                  if (pts.length === 2) {
                    return (
                      <line
                        key={`wall-${idx}`}
                        x1={pts[0][0]}
                        y1={pts[0][1]}
                        x2={pts[1][0]}
                        y2={pts[1][1]}
                        stroke={strokeColor}
                        strokeWidth={strokeW}
                        strokeLinecap="round"
                      />
                    );
                  } else if (pts.length > 2) {
                    return (
                      <polyline
                        key={`wall-poly-${idx}`}
                        points={pts.map(c => `${c[0]},${c[1]}`).join(' ')}
                        fill="none"
                        stroke={strokeColor}
                        strokeWidth={strokeW}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    );
                  }
                }
                return null;
              })}

              {/* Dynamic Door Openings */}
              {showExits && doorElements.map((el, idx) => {
                const geom = el.geometry;
                if (!geom || geom.type !== 'Point' || !Array.isArray(geom.coordinates)) return null;
                const [dx, dy] = geom.coordinates;
                return (
                  <g key={`door-${idx}`} className="cad-door-marker">
                    <circle cx={dx} dy={dy} r="0.7" fill="#65a30d" />
                    <circle cx={dx} dy={dy} r="1.6" fill="none" stroke="#65a30d" strokeWidth="0.25" strokeDasharray="0.5,0.5" />
                  </g>
                );
              })}

              {/* Dynamic Emergency Exit Badges */}
              {showExits && exitElements.map((el, idx) => {
                const geom = el.geometry;
                if (!geom || geom.type !== 'Point' || !Array.isArray(geom.coordinates)) return null;
                const [ex, ey] = geom.coordinates;
                return (
                  <g key={`exit-${idx}`} transform={`translate(${ex}, ${ey})`} className="cad-exit-group">
                    <rect
                      x="-3.6"
                      y="-1.5"
                      width="7.2"
                      height="3.0"
                      rx="0.8"
                      fill="#16a34a"
                      stroke="#ffffff"
                      strokeWidth="0.3"
                    />
                    <text
                      x="0"
                      y="0.1"
                      textAnchor="middle"
                      dominantBaseline="central"
                      fill="#ffffff"
                      fontSize="0.95"
                      fontWeight="800"
                      fontFamily="'DM Mono', monospace"
                    >
                      EXIT
                    </text>
                  </g>
                );
              })}

              {/* Floating Room Compliance Badges */}
              {showPills && roomElements.map((el, idx) => {
                const props = el.properties || {};
                const geom = el.geometry;
                if (!geom) return null;
                const coords = geom.coordinates[0];
                if (!coords || coords.length === 0) return null;

                let cx = 50;
                let cy = 50;
                if (props.centroid && Array.isArray(props.centroid)) {
                  cx = props.centroid[0];
                  cy = props.centroid[1];
                } else if (props.svg_centroid && Array.isArray(props.svg_centroid)) {
                  cx = props.svg_centroid[0];
                  cy = props.svg_centroid[1];
                } else {
                  cx = coords.reduce((s, pt) => s + pt[0], 0) / coords.length;
                  cy = coords.reduce((s, pt) => s + pt[1], 0) / coords.length;
                }

                const relatedFinding = findings?.find(f => f.title?.includes(props.name) || f.detail?.includes(props.name));
                const hasViolation = Boolean(relatedFinding);
                const isSelected = activeId && activeId === relatedFinding?.id;
                const isHovered = hoveredRoom && hoveredRoom.name === props.name;

                // Level-of-Detail (LOD): hide non-critical badges when zoomed out below 80%
                const isLODVisible = zoom >= 0.80 || hasViolation || isSelected || isHovered;
                if (!isLODVisible) return null;

                if (viewMode === 'hybrid') {
                  const badgeText = hasViolation
                    ? `⚠️ ${relatedFinding?.severity || 'Violation'} • ${props.occupant_load || 0} occ`
                    : `${props.occupant_load !== undefined ? `${props.occupant_load} occ` : ''}${props.area_m2 ? ` • ${props.area_m2}m²` : ''} ✓`;
                  const textLen = badgeText.length;
                  const badgeW = Math.min(14.0, Math.max(7.5, textLen * 0.46 + 1.8));
                  const badgeH = 2.3;
                  const badgeY = hasViolation && showPins ? cy - 3.2 : cy + 2.0;

                  return (
                    <g
                      key={`room-pill-${idx}`}
                      transform={`translate(${cx}, ${badgeY})`}
                      className="room-pill-badge"
                      style={{ cursor: 'pointer' }}
                      onClick={() => {
                        if (relatedFinding) select(isSelected ? null : relatedFinding.id);
                      }}
                    >
                      <rect
                        x={-badgeW / 2}
                        y={-badgeH / 2}
                        width={badgeW}
                        height={badgeH}
                        rx="0.5"
                        fill={isSelected ? 'rgba(220, 38, 38, 0.95)' : hasViolation ? 'rgba(185, 28, 28, 0.92)' : 'rgba(15, 23, 42, 0.88)'}
                        stroke={isSelected ? '#ffffff' : hasViolation ? '#fca5a5' : 'rgba(255, 255, 255, 0.25)'}
                        strokeWidth="0.22"
                        filter="drop-shadow(0 1px 2px rgba(0,0,0,0.3))"
                      />
                      <text
                        x="0"
                        y="0.1"
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill={isSelected ? '#ffffff' : hasViolation ? '#fee2e2' : '#38bdf8'}
                        fontSize="0.75"
                        fontWeight="800"
                        fontFamily="'JetBrains Mono', monospace"
                      >
                        {badgeText}
                      </text>
                    </g>
                  );
                }

                return (
                  <g key={`room-label-vector-${idx}`} className="room-label-vector">
                    <text
                      x={cx}
                      y={cy - 1.0}
                      textAnchor="middle"
                      dominantBaseline="central"
                      fill={hasViolation ? '#f87171' : '#f8fafc'}
                      fontSize="1.15"
                      fontWeight="800"
                      fontFamily="'DM Mono', monospace"
                    >
                      {props.name}
                    </text>
                    {props.area_m2 && (
                      <text
                        x={cx}
                        y={cy + 1.4}
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill={hasViolation ? '#fca5a5' : '#94a3b8'}
                        fontSize="0.85"
                        fontWeight="600"
                        fontFamily="'DM Mono', monospace"
                      >
                        {props.area_m2} m² {props.occupant_load !== undefined ? `• ${props.occupant_load} occ` : ''}
                      </text>
                    )}
                  </g>
                );
              })}

              {/* Fire Alarm CAD Point Symbols (Phase 1 Ingestion) */}
              {fireAlarmElements.map((el, idx) => {
                const geom = el.geometry;
                const props = el.properties || {};
                if (!geom || geom.type !== 'Point' || !Array.isArray(geom.coordinates)) return null;
                const [fx, fy] = geom.coordinates;
                const devType = props.device_type || el.type;
                const tag = props.tag || '';
                const isHovered = hoveredDevice && hoveredDevice.id === el.id;
                const isSelected = selectedDeviceId === el.id;

                if (devType === 'smoke_detector' || devType.includes('smoke')) {
                  return (
                    <g
                      key={`fa-smoke-${el.id || idx}`}
                      transform={`translate(${fx}, ${fy})`}
                      className={`fa-device-symbol fa-smoke ${isSelected ? 'selected' : ''}`}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredDevice(el)}
                      onMouseLeave={() => setHoveredDevice(null)}
                      onClick={() => setSelectedDeviceId(isSelected ? null : el.id)}
                    >
                      {(isHovered || isSelected) && (
                        <circle cx="0" cy="0" r="4.2" fill="rgba(239, 68, 68, 0.16)" stroke="#ef4444" strokeWidth="0.25" strokeDasharray="0.6, 0.6" />
                      )}
                      <circle cx="0" cy="0" r="1.3" fill="#fee2e2" stroke={isSelected ? '#ffffff' : '#ef4444'} strokeWidth={isSelected ? '0.45' : '0.3'} />
                      <circle cx="0" cy="0" r="0.45" fill="#dc2626" />
                      <text
                        x="0"
                        y="2.3"
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill={isSelected ? '#ffffff' : '#fca5a5'}
                        fontSize="0.75"
                        fontWeight="800"
                        fontFamily="'JetBrains Mono', monospace"
                      >
                        {tag || 'SD'}
                      </text>
                    </g>
                  );
                } else if (devType === 'heat_detector' || devType.includes('heat')) {
                  return (
                    <g
                      key={`fa-heat-${el.id || idx}`}
                      transform={`translate(${fx}, ${fy})`}
                      className={`fa-device-symbol fa-heat ${isSelected ? 'selected' : ''}`}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredDevice(el)}
                      onMouseLeave={() => setHoveredDevice(null)}
                      onClick={() => setSelectedDeviceId(isSelected ? null : el.id)}
                    >
                      {(isHovered || isSelected) && (
                        <circle cx="0" cy="0" r="3.8" fill="rgba(245, 158, 11, 0.16)" stroke="#f59e0b" strokeWidth="0.25" strokeDasharray="0.6, 0.6" />
                      )}
                      <circle cx="0" cy="0" r="1.3" fill="#fef3c7" stroke={isSelected ? '#ffffff' : '#f59e0b'} strokeWidth={isSelected ? '0.45' : '0.3'} />
                      <polygon points="0,-0.6 0.6,0.4 -0.6,0.4" fill="#d97706" />
                      <text
                        x="0"
                        y="2.3"
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill={isSelected ? '#ffffff' : '#fde68a'}
                        fontSize="0.75"
                        fontWeight="800"
                        fontFamily="'JetBrains Mono', monospace"
                      >
                        {tag || 'HD'}
                      </text>
                    </g>
                  );
                } else if (devType === 'manual_call_point' || devType.includes('mcp') || devType.includes('manual')) {
                  return (
                    <g
                      key={`fa-mcp-${el.id || idx}`}
                      transform={`translate(${fx}, ${fy})`}
                      className={`fa-device-symbol fa-mcp ${isSelected ? 'selected' : ''}`}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredDevice(el)}
                      onMouseLeave={() => setHoveredDevice(null)}
                      onClick={() => setSelectedDeviceId(isSelected ? null : el.id)}
                    >
                      {(isHovered || isSelected) && (
                        <rect x="-2.2" y="-2.2" width="4.4" height="4.4" rx="0.5" fill="rgba(220, 38, 38, 0.18)" stroke="#ef4444" strokeWidth="0.25" strokeDasharray="0.6, 0.6" />
                      )}
                      <rect x="-1.2" y="-1.2" width="2.4" height="2.4" rx="0.3" fill="#b91c1c" stroke={isSelected ? '#ffffff' : '#fca5a5'} strokeWidth={isSelected ? '0.45' : '0.3'} />
                      <circle cx="0" cy="0" r="0.45" fill="#ffffff" />
                      <text
                        x="0"
                        y="2.3"
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill={isSelected ? '#ffffff' : '#f87171'}
                        fontSize="0.75"
                        fontWeight="800"
                        fontFamily="'JetBrains Mono', monospace"
                      >
                        {tag || 'MCP'}
                      </text>
                    </g>
                  );
                } else if (devType === 'sounder' || devType === 'sounder_beacon' || devType.includes('sounder')) {
                  return (
                    <g
                      key={`fa-sounder-${el.id || idx}`}
                      transform={`translate(${fx}, ${fy})`}
                      className={`fa-device-symbol fa-sounder ${isSelected ? 'selected' : ''}`}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredDevice(el)}
                      onMouseLeave={() => setHoveredDevice(null)}
                      onClick={() => setSelectedDeviceId(isSelected ? null : el.id)}
                    >
                      {(isHovered || isSelected) && (
                        <circle cx="0" cy="0" r="3.5" fill="rgba(139, 92, 246, 0.16)" stroke="#8b5cf6" strokeWidth="0.25" strokeDasharray="0.6, 0.6" />
                      )}
                      <polygon points="0,-1.3 1.3,0 0,1.3 -1.3,0" fill="#7c3aed" stroke={isSelected ? '#ffffff' : '#c4b5fd'} strokeWidth={isSelected ? '0.45' : '0.3'} />
                      <text
                        x="0"
                        y="2.3"
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill={isSelected ? '#ffffff' : '#c4b5fd'}
                        fontSize="0.75"
                        fontWeight="800"
                        fontFamily="'JetBrains Mono', monospace"
                      >
                        {tag || 'SB'}
                      </text>
                    </g>
                  );
                } else if (devType === 'fire_alarm_panel' || devType === 'fire_alarm_control_panel' || devType.includes('facp') || devType.includes('panel')) {
                  return (
                    <g
                      key={`fa-panel-${el.id || idx}`}
                      transform={`translate(${fx}, ${fy})`}
                      className={`fa-device-symbol fa-facp ${isSelected ? 'selected' : ''}`}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredDevice(el)}
                      onMouseLeave={() => setHoveredDevice(null)}
                      onClick={() => setSelectedDeviceId(isSelected ? null : el.id)}
                    >
                      <rect x="-3.0" y="-1.5" width="6.0" height="3.0" rx="0.5" fill="#991b1b" stroke={isSelected ? '#ffffff' : '#fecaca'} strokeWidth={isSelected ? '0.5' : '0.35'} />
                      <text
                        x="0"
                        y="0.1"
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill="#ffffff"
                        fontSize="0.9"
                        fontWeight="800"
                        fontFamily="'DM Mono', monospace"
                      >
                        FACP
                      </text>
                    </g>
                  );
                }
                return null;
              })}
            </g>
          )}

          {!isRealDrawing && !imageSrc && (
            <g className="default-plan-lines">
              <rect x="5" y="5" width="90" height="90" fill="none" stroke="#756d63" strokeWidth="1.2" rx="1" />
              <rect x="10" y="10" width="40" height="32" fill="#eae6d3" fillOpacity="0.3" stroke="#989878" strokeWidth="0.8" />
              <rect x="58" y="10" width="30" height="32" fill="#eae6d3" fillOpacity="0.3" stroke="#989878" strokeWidth="0.8" />
              <rect x="10" y="58" width="48" height="32" fill="#eae6d3" fillOpacity="0.3" stroke="#989878" strokeWidth="0.8" />
              <rect x="67" y="58" width="24" height="32" fill="#eae6d3" fillOpacity="0.3" stroke="#989878" strokeWidth="0.8" />
            </g>
          )}
        </svg>

        {/* Dynamic Hazard Pins */}
        {showPins && (findings || []).map((f, idx) => {
          const isChosen = f.id === activeId;
          const isResolved = f.status === 'resolved';
          const isFalsePositive = f.status === 'false_positive';
          const markerClass = `pin-marker ${isChosen ? 'chosen' : ''} ${isResolved ? 'resolved' : ''} ${isFalsePositive ? 'false-pos' : ''}`;
          const markerLeft = f.pos?.[0] || '50%';
          const markerTop = f.pos?.[1] || '50%';

          return (
            <button
              onClick={() => select(isChosen ? null : f.id)}
              key={f.id}
              aria-label={`Finding ${idx + 1}`}
              className={markerClass}
              style={{ left: markerLeft, top: markerTop }}
              title={`Finding ${idx + 1}: ${f.title} (${f.clause})`}
            >
              <span className="pin-num">{idx + 1}</span>
            </button>
          );
        })}
      </div>

      {/* Floating Canvas Zoom & View Control Badge */}
      <div className="floating-canvas-controls">
        <button
          className="float-tool-btn"
          onClick={handleZoomOut}
          title="Zoom Out (-)"
        >
          <ZoomOut size={13} />
        </button>
        <button
          className="float-tool-btn zoom-text-btn"
          onClick={handleResetZoom}
          title="Click to reset zoom (0)"
        >
          {Math.round(zoom * 100)}%
        </button>
        <button
          className="float-tool-btn"
          onClick={handleZoomIn}
          title="Zoom In (+)"
        >
          <ZoomIn size={13} />
        </button>
        <button
          className="float-tool-btn"
          onClick={handleResetZoom}
          title="Reset View / Fit (0)"
        >
          <RotateCcw size={12} />
        </button>
        <button
          className={`float-tool-btn fs-trigger-btn ${isFullScreen ? 'active' : ''}`}
          onClick={() => setIsFullScreen(!isFullScreen)}
          title={isFullScreen ? "Exit Fullscreen (Esc)" : "Full Screen View (F)"}
        >
          {isFullScreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
        </button>
      </div>

      {/* Hover Tooltip Card */}
      {hoveredRoom && (
        <div
          className="room-hover-tooltip"
          style={{
            left: Math.min(Math.max(10, mousePos.x + 15), 480),
            top: Math.min(Math.max(10, mousePos.y - 45), 440)
          }}
        >
          <div className="rht-head">
            <b>{hoveredRoom.name}</b>
            <span className={`rht-badge ${hoveredRoom.hasViolation ? 'danger' : 'safe'}`}>
              {hoveredRoom.hasViolation ? '⚠️ Non-Compliant' : '✓ Compliant'}
            </span>
          </div>
          <div className="rht-body">
            <span>Area: <b>{hoveredRoom.area_m2} m²</b></span>
            <span>Occupants: <b>{hoveredRoom.occupant_load || hoveredRoom.occupant_load_explicit || 'N/A'}</b></span>
            {hoveredRoom.travel_distance_m && (
              <span>Travel: <b>{hoveredRoom.travel_distance_m} m</b></span>
            )}
          </div>
          {hoveredRoom.relatedFinding && (
            <div className="rht-finding">
              <AlertTriangle size={12} />
              <span>{hoveredRoom.relatedFinding.shortTitle || hoveredRoom.relatedFinding.title}</span>
            </div>
          )}
        </div>
      )}

      {/* Fire Alarm Device Hover Tooltip */}
      {hoveredDevice && (
        <div
          className="room-hover-tooltip"
          style={{
            left: Math.min(Math.max(10, mousePos.x + 15), 480),
            top: Math.min(Math.max(10, mousePos.y - 45), 440),
            borderColor: 'rgba(239, 68, 68, 0.4)'
          }}
        >
          <div className="rht-head">
            <b>{hoveredDevice.properties?.tag || hoveredDevice.type}</b>
            <span className="rht-badge safe" style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' }}>
              {hoveredDevice.properties?.device_type?.replace(/_/g, ' ') || hoveredDevice.type}
            </span>
          </div>
          <div className="rht-body">
            <span>Layer: <b>{hoveredDevice.properties?.layer || 'N/A'}</b></span>
            <span>Physical: <b>{hoveredDevice.properties?.x_m !== undefined ? `${hoveredDevice.properties.x_m}m, ${hoveredDevice.properties.y_m}m` : (hoveredDevice.properties?.pos_m ? `${hoveredDevice.properties.pos_m[0]}m, ${hoveredDevice.properties.pos_m[1]}m` : 'N/A')}</b></span>
            {hoveredDevice.geometry?.coordinates && (
              <span>SVG Norm: <b>{hoveredDevice.geometry.coordinates[0]}%, {hoveredDevice.geometry.coordinates[1]}%</b></span>
            )}
          </div>
        </div>
      )}
    </div>
  );

  // Full Screen Modal Viewport
  if (isFullScreen) {
    return (
      <div className="fullscreen-plan-overlay">
        {/* Fullscreen Header Bar */}
        <header className="fullscreen-header">
          <div className="fs-header-left">
            <div className="fs-badge">
              <Building2 size={16} />
              <span>EGRESS AUDIT VIEWER</span>
            </div>
            <h2 className="fs-floor-title">{drawingMeta.floor}</h2>
            {drawingMeta.pagesCount > 1 && (
              <span className="fs-page-tag">Sheet {drawingMeta.pageIndex + 1} of {drawingMeta.pagesCount}</span>
            )}
          </div>

          <div className="fs-header-center">
            {/* View Mode Switchers in Fullscreen */}
            <div className="view-mode-group">
              <button
                className={`view-mode-btn ${viewMode === 'hybrid' ? 'active' : ''}`}
                onClick={() => setViewMode && setViewMode('hybrid')}
                title="PDF Drawing with compliance overlays"
              >
                ✨ Hybrid
              </button>
              <button
                className={`view-mode-btn ${viewMode === 'vector' ? 'active' : ''}`}
                onClick={() => setViewMode && setViewMode('vector')}
                title="CAD Vector blueprint mode"
              >
                📐 Vector CAD
              </button>
              {drawingMeta.hasImage && (
                <button
                  className={`view-mode-btn ${viewMode === 'image' ? 'active' : ''}`}
                  onClick={() => setViewMode && setViewMode('image')}
                  title="Original PDF image"
                >
                  📄 Original PDF
                </button>
              )}
            </div>

            {/* Quick Floor Switching Tabs in Fullscreen */}
            {drawingMeta.pages && drawingMeta.pages.length > 1 && (
              <div className="fs-floor-tabs">
                {drawingMeta.pages.map((p, pIdx) => (
                  <button
                    key={`fs-page-${pIdx}`}
                    className={`fs-floor-tab ${pIdx === drawingMeta.pageIndex ? 'active' : ''}`}
                    onClick={() => handleFloorSwitch && handleFloorSwitch(pIdx)}
                  >
                    Level 0{pIdx}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="fs-header-right">
            {/* Toggle Findings Sidebar Button */}
            <button
              className={`fs-tool-btn ${showFindingsInFullscreen ? 'active' : ''}`}
              onClick={() => setShowFindingsInFullscreen(!showFindingsInFullscreen)}
              title="Toggle Findings Drawer"
            >
              <FileCheck size={14} />
              <span>Findings ({findings?.length || 0})</span>
            </button>

            {/* Exit Fullscreen Button */}
            <button
              className="fs-exit-btn"
              onClick={() => setIsFullScreen(false)}
              title="Exit Full Screen (Esc)"
            >
              <X size={16} />
              <span>Exit Fullscreen</span>
            </button>
          </div>
        </header>

        {/* Fullscreen Sub-header Layer Bar */}
        {renderLayerControls(true)}

        {/* Fullscreen Main Content Split */}
        <div className="fullscreen-body">
          <div className="fullscreen-canvas-wrap">
            {renderPlanCanvas(true)}
          </div>

          {/* Docked Findings Sidebar in Fullscreen */}
          {showFindingsInFullscreen && (
            <aside className="fullscreen-findings-drawer">
              <div className="fs-findings-head">
                <div>
                  <h3>Safety Findings</h3>
                  <p>{findings?.filter(x => x.status === 'open').length || 0} open finding(s)</p>
                </div>
                <button
                  className="fs-close-drawer-btn"
                  onClick={() => setShowFindingsInFullscreen(false)}
                  title="Close Findings Sidebar"
                >
                  <X size={14} />
                </button>
              </div>

              <div className="fs-finding-cards-list">
                {findings && findings.length > 0 ? (
                  findings.map((f, idx) => {
                    const isSelected = f.id === activeId;
                    return (
                      <div
                        key={`fs-f-${f.id}`}
                        className={`fs-finding-card ${isSelected ? 'selected' : ''} ${f.status}`}
                        onClick={() => select(isSelected ? null : f.id)}
                      >
                        <div className="fs-fc-top">
                          <span className="fs-pin-chip">{idx + 1}</span>
                          <span className="fs-fc-title">{f.roomName || f.title}</span>
                          <span className={`fs-fc-sev ${f.severity?.toLowerCase()}`}>{f.severity}</span>
                        </div>
                        <div className="fs-fc-body">
                          <span className="fs-fc-type">{f.shortTitle || f.kind}</span>
                          <div className="fs-fc-metric">
                            <span>Measured: <b>{f.measured}</b></span>
                            <span>Limit: <b>{f.limit}</b></span>
                          </div>
                          <span className="fs-fc-clause">{f.clause}</span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="fs-no-findings">
                    <CheckCircle2 size={24} color="#10B981" />
                    <h4>100% Compliant</h4>
                    <p>No safety or travel distance violations found on this floor level.</p>
                  </div>
                )}
              </div>
            </aside>
          )}
        </div>
      </div>
    );
  }

  // Standard inline plan container
  return (
    <div className="plan-container">
      {renderLayerControls(false)}
      {renderPlanCanvas(false)}
    </div>
  );
}


function UploadModal({ close, onFileSelected, uploadState, error, onFallbackDemo }) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [occupancyType, setOccupancyType] = useState('Business - Regular office areas');
  const [sprinklered, setSprinklered] = useState(true);
  const [documentType, setDocumentType] = useState('architectural');

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleSubmit = () => {
    if (selectedFile) {
      onFileSelected(selectedFile, { occupancyType, sprinklered, documentType });
    } else {
      document.querySelector('.drop input')?.click();
    }
  };

  const isUploading = uploadState === 'uploading' || uploadState === 'processing';

  return (
    <div className="modal-bg" onClick={(e) => { if (e.target === e.currentTarget && !isUploading) close(); }}>
      <div className="modal">
        <button className="close" onClick={close} disabled={isUploading} aria-label="Close modal">
          <X size={18} />
        </button>
        <h2>Upload CAD / PDF Drawing</h2>
        <p>Upload DXF architectural floor plans or fire alarm shop drawings to parse vector geometry and extracted point symbols.</p>

        {isUploading && (
          <div className="upload-status">
            <div className="spinner"></div>
            <h3>Analyzing drawing...</h3>
            <p>Extracting geometric elements, calculating travel distances, and verifying exit capacities.</p>
            <div className="upload-steps">
              <span className="step done"><CheckCircle2 size={13} /> File received</span>
              <span className="step active"><RefreshCw size={13} className="spin-fast" /> Rendering overview image & vector rooms</span>
              <span className="step"><Clock3 size={13} /> Checking UAE FLS code clauses</span>
            </div>
          </div>
        )}

        {error && (
          <div className="upload-error" style={{ background: 'var(--brand-red-light)', border: '1px solid rgba(211, 47, 47, 0.3)', borderRadius: 'var(--radius-sm)', padding: '14px', margin: '14px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--brand-red)', fontWeight: 700, fontSize: '13px', marginBottom: '4px' }}>
              <AlertTriangle size={16} />
              <span>Upload Notice</span>
            </div>
            <p style={{ margin: '0 0 10px', fontSize: '12px', color: 'var(--ink-primary)' }}>{error}</p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="primary" style={{ padding: '6px 12px', fontSize: '11px' }} onClick={onFallbackDemo}>
                Load Demo Findings
              </button>
              <button className="secondary" style={{ padding: '6px 12px', fontSize: '11px' }} onClick={() => document.querySelector('.drop input')?.click()}>
                Select Another File
              </button>
            </div>
          </div>
        )}

        {!isUploading && !error && (
          <>
            <label
              className={`drop ${dragOver ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
            >
              <FileUp size={28} />
              <b>{selectedFile ? `Selected: ${selectedFile.name}` : 'Choose drawing file or drag & drop'}</b>
              <span>Auto-detects CAD rooms, dimensions, and exits (.dxf, .pdf)</span>
              <input type="file" accept=".pdf,.dxf" onChange={handleFileChange} />
            </label>

            <div className="modal-fields">
              <div className="modal-field" style={{ gridColumn: '1 / -1' }}>
                <label>DRAWING DISCIPLINE / TYPE</label>
                <select
                  className="modal-select"
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                >
                  <option value="architectural">📐 Architectural Floor Plan (Means of Egress)</option>
                  <option value="fire_alarm">🚨 Fire Alarm Shop Drawing (Detection & MCP)</option>
                </select>
              </div>

              <div className="modal-field">
                <label>OCCUPANCY CLASSIFICATION</label>
                <select
                  className="modal-select"
                  value={occupancyType}
                  onChange={(e) => setOccupancyType(e.target.value)}
                >
                  <option value="Business - Regular office areas">Business - Regular office (9.3 m²/person)</option>
                  <option value="Business - Concentrated office areas (open-plan, workstation-dense)">Business - Concentrated (4.6 m²/person)</option>
                </select>
              </div>

              <div className="modal-field">
                <label>FIRE SPRINKLER SYSTEM</label>
                <select
                  className="modal-select"
                  value={sprinklered ? 'yes' : 'no'}
                  onChange={(e) => setSprinklered(e.target.value === 'yes')}
                >
                  <option value="yes">Sprinklered (91m max travel)</option>
                  <option value="no">Non-Sprinklered (61m max travel)</option>
                </select>
              </div>
            </div>

            <button className="primary full" onClick={handleSubmit}>
              {selectedFile ? `Analyze "${selectedFile.name}" →` : 'Select File & Start Review →'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}


function MultiFloorOverviewModal({ isOpen, onClose, summary, currentDrawingId, activePageIndex, onSelectFloor }) {
  if (!isOpen || !summary) return null;

  const totalFloors = summary.total_pages || (summary.floors ? summary.floors.length : 1);
  const totalErrors = summary.total_violations_count !== undefined ? summary.total_violations_count : 0;
  const floors = summary.floors || [];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel multi-floor-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="mf-header-titles">
            <div className="mf-title-row">
              <Building2 size={22} className="text-teal" />
              <h3>All Floor Plans & Error Analysis</h3>
            </div>
            <p className="mf-subtitle">
              Comprehensive FLS egress compliance audit across all {totalFloors} decoded building levels.
            </p>
          </div>
          <div className="mf-header-badges">
            <span className="mf-badge floors-count">
              <Layers size={13} /> {totalFloors} Floors Analyzed
            </span>
            <span className={`mf-badge errors-count ${totalErrors > 0 ? 'has-errors' : 'clean'}`}>
              <AlertTriangle size={13} /> {totalErrors} Total Findings
            </span>
            <button className="modal-close" onClick={onClose}>
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="mf-modal-body">
          <div className="mf-floors-grid">
            {floors.map((fl) => {
              const isActive = fl.index === activePageIndex;
              const hasErrors = (fl.violations_count || 0) > 0;
              const cleanTitle = (fl.title || `Floor Level 0${fl.index}`)
                .replace(' - TYPICAL OFFICE FLOOR PLAN', '')
                .replace(' FLOOR PLAN', '')
                .replace('ARCHITECTURAL FLOOR PLAN - ', '');

              return (
                <div key={`mf-card-${fl.index}`} className={`mf-floor-card ${isActive ? 'active-floor' : ''} ${hasErrors ? 'non-compliant' : 'compliant'}`}>
                  <div className="mf-card-top">
                    <div className="mf-card-title-group">
                      <span className="mf-floor-index-badge">Level 0{fl.index}</span>
                      <h4 className="mf-card-title">{cleanTitle}</h4>
                    </div>
                    <span className={`mf-status-chip ${hasErrors ? 'status-danger' : 'status-safe'}`}>
                      {hasErrors ? `⚠️ ${fl.violations_count} VIOLATIONS` : '✓ 100% COMPLIANT'}
                    </span>
                  </div>

                  {/* Metrics bar */}
                  <div className="mf-metrics-row">
                    <div className="mf-metric-item">
                      <span className="lbl">OCCUPANTS</span>
                      <b>{fl.total_occupant_load} p</b>
                    </div>
                    <div className="mf-metric-item">
                      <span className="lbl">FLOOR AREA</span>
                      <b>{fl.total_floor_area_m2} m²</b>
                    </div>
                    <div className="mf-metric-item">
                      <span className="lbl">ROOMS / EXITS</span>
                      <b>{fl.rooms_count} / {fl.exits_count}</b>
                    </div>
                    <div className="mf-metric-item">
                      <span className="lbl">MAX TRAVEL</span>
                      <b className={fl.max_travel_distance_m > 91.0 ? 'text-red' : 'text-green'}>
                        {fl.max_travel_distance_m} m
                      </b>
                    </div>
                  </div>

                  {/* Violations / Errors Breakdown for this floor */}
                  <div className="mf-errors-section">
                    <span className="mf-errors-heading">
                      {hasErrors ? `FLS CODE FINDINGS (${fl.violations.length})` : 'COMPLIANCE AUDIT'}
                    </span>
                    {hasErrors ? (
                      <div className="mf-violations-list">
                        {fl.violations.map((v, vIdx) => (
                          <div key={`mf-v-${fl.index}-${vIdx}`} className="mf-violation-item">
                            <div className="mf-v-top">
                              <span className={`mf-v-sev ${v.severity?.toLowerCase()}`}>{v.severity}</span>
                              <span className="mf-v-clause">{v.clause_ref}</span>
                            </div>
                            <p className="mf-v-title">{v.title}</p>
                            <div className="mf-v-meas">
                              <span>Measured: <b>{v.measured_value} {v.measured_unit}</b></span>
                              <span>Limit: <b>{v.limit_value} {v.limit_unit}</b></span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="mf-safe-notice">
                        <CheckCircle2 size={16} />
                        <span>All travel distances & exit capacities on this floor satisfy UAE Fire & Life Safety Code requirements.</span>
                      </div>
                    )}
                  </div>

                  {/* Action */}
                  <div className="mf-card-footer">
                    <button
                      className={`mf-inspect-btn ${isActive ? 'current' : ''}`}
                      onClick={() => {
                        onSelectFloor(fl.index);
                        onClose();
                      }}
                    >
                      {isActive ? '✓ Currently Viewing Floor' : 'Inspect Floor Plan & Findings ↗'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}


class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('FLS Checker Runtime Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', fontFamily: 'sans-serif', textAlign: 'center', background: '#F8F9FA', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#FFFFFF', padding: '32px', borderRadius: '12px', border: '1px solid #E5E7EB', maxWidth: '500px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
            <h2 style={{ color: '#D32F2F', margin: '0 0 10px' }}>Something went wrong</h2>
            <p style={{ color: '#4B5563', fontSize: '13px', margin: '0 0 20px' }}>{this.state.error?.message || 'An unexpected rendering error occurred.'}</p>
            <button
              onClick={() => window.location.reload()}
              style={{ background: '#D32F2F', color: '#FFFFFF', border: 'none', padding: '10px 20px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);
