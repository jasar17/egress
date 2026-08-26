import React, { useState, useEffect } from 'react';
import {
  Phone,
  MapPin,
  ShoppingCart,
  ChevronDown,
  ChevronRight,
  Search,
  X,
  ExternalLink,
  ShieldCheck,
  Building2,
  Sparkles,
  Trophy,
  Lightbulb,
  Check,
  ArrowRight,
  Eye,
  Sliders,
  Send,
  Layers,
  FileCheck,
  Laptop
} from 'lucide-react';
import heroImg from './assets/hero_meeting.jpg';
import financeImg from './assets/finance_desk.jpg';
import abstractRedImg from './assets/abstract_red_bg.jpg';

// Exact SVG Squiggly Wave Accent (as shown in reference under headings)
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

// Chess Knight Icon (Front End Developemet)
const ChessKnightIcon = () => (
  <svg
    width="28"
    height="28"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M19 22H5v-2a3 3 0 0 1 3-3h8a3 3 0 0 1 3 3v2z" />
    <path d="M14 6.5C14 4.5 12 3 10 3c-1.5 0-3 1-3 2.5 0 .5.5 1.5.5 1.5L5 9c-.5.5-.5 1.5 0 2l1.5 1.5c.5.5 1.5.5 2 0l1-1c0 1.5.5 2.5 1.5 3.5l1 1h4v-3.5c0-1.5-.5-2.5-1.5-3.5L14 8.5V6.5z" />
    <circle cx="10" cy="6" r="0.75" fill="currentColor" />
  </svg>
);

// Creative Writing (Crossed Pen & Ruler / Quill)
const CreativeWritingIcon = () => (
  <svg
    width="28"
    height="28"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M18 3l3 3-10 10H8v-3L18 3z" />
    <path d="M3 21l3-3 5 5-3 3-5-5z" />
    <path d="M6 18l3-3" />
    <path d="M15 6l3 3" />
  </svg>
);

// Graphic Design (Paint Roller / Brush)
const GraphicDesignIcon = () => (
  <svg
    width="28"
    height="28"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="3" y="3" width="18" height="6" rx="1.5" />
    <path d="M12 9v4" />
    <path d="M12 13a3 3 0 0 1 3 3v5" />
    <path d="M9 19h6" />
  </svg>
);

// Responsive Web Design (Smartphone & Tablet Devices)
const ResponsiveWebIcon = () => (
  <svg
    width="28"
    height="28"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="2" y="3" width="14" height="18" rx="2" />
    <rect x="11" y="8" width="11" height="13" rx="2" />
    <circle cx="9" cy="18" r="0.8" />
    <circle cx="16.5" cy="18.5" r="0.8" />
  </svg>
);

export default function PaytonLanding({ onSwitchToApp, onOpenUpload }) {
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [cartCount, setCartCount] = useState(0);
  const [showCartModal, setShowCartModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [emailInput, setEmailInput] = useState('');
  const [toastMessage, setToastMessage] = useState('');

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3200);
  };

  const servicesData = [
    {
      id: 'creative-writing',
      title: 'Creative Writing',
      icon: <CreativeWritingIcon />,
      desc: 'Compelling brand storytelling, conversion copywriting, and creative narratives designed to engage target audiences.'
    },
    {
      id: 'print-design',
      title: 'Print Design',
      icon: <Lightbulb size={28} strokeWidth={1.75} />,
      desc: 'High-end editorial layouts, brochures, marketing collateral, packaging, and tactile print brand collateral.'
    },
    {
      id: 'social-media',
      title: 'Social Media',
      icon: <Trophy size={28} strokeWidth={1.75} />,
      desc: 'Data-driven social campaigns, influencer partnerships, content calendars, and growth strategies across global channels.'
    },
    {
      id: 'front-end-dev',
      title: 'Front End Developemet',
      icon: <ChessKnightIcon />,
      desc: 'Pixel-perfect, high-performance responsive web interfaces built with modern React, Vite, and clean modular CSS.'
    },
    {
      id: 'graphic-design',
      title: 'Graphic Design',
      icon: <GraphicDesignIcon />,
      desc: 'Unique visual identities, brand typography systems, vector illustrations, and digital graphic assets.'
    },
    {
      id: 'responsive-design',
      title: 'Responsive Web Design',
      icon: <ResponsiveWebIcon />,
      desc: 'Adaptive user experiences engineered to look flawless across all screen sizes, from mobile phones to ultra-wide displays.'
    }
  ];

  return (
    <div className="payton-page-wrapper">
      {/* 1. TOP UTILITY BAR (Red Bar) */}
      <div className="payton-top-bar">
        <div className="payton-container payton-top-bar-inner">
          <div className="payton-top-contact">
            <a href="tel:+1234567890" className="top-item">
              <Phone size={13} className="top-icon" />
              <span>+1 (234) 567-890</span>
            </a>
            <span className="top-sep">•</span>
            <div className="top-item">
              <MapPin size={13} className="top-icon" />
              <span>228 Park Ave S, New York, NY 10003</span>
            </div>
          </div>

          <div className="payton-top-socials">
            <a href="#facebook" onClick={(e) => { e.preventDefault(); showToast('Connecting to Facebook...'); }} title="Facebook" aria-label="Facebook">f</a>
            <a href="#twitter" onClick={(e) => { e.preventDefault(); showToast('Connecting to Twitter...'); }} title="Twitter" aria-label="Twitter">🐦</a>
            <a href="#google" onClick={(e) => { e.preventDefault(); showToast('Connecting to Google+...'); }} title="Google+" aria-label="Google+">G+</a>
            <a href="#pinterest" onClick={(e) => { e.preventDefault(); showToast('Connecting to Pinterest...'); }} title="Pinterest" aria-label="Pinterest">P</a>
            <a href="#linkedin" onClick={(e) => { e.preventDefault(); showToast('Connecting to LinkedIn...'); }} title="LinkedIn" aria-label="LinkedIn">in</a>
            <a href="#instagram" onClick={(e) => { e.preventDefault(); showToast('Connecting to Instagram...'); }} title="Instagram" aria-label="Instagram">📷</a>
          </div>
        </div>
      </div>

      {/* 2. HERO AREA WITH OVERLAY HEADER */}
      <section className="payton-hero-section" style={{ backgroundImage: `url(${heroImg})` }}>
        <div className="payton-hero-overlay"></div>

        {/* NAVIGATION HEADER (Overlay on top of Hero) */}
        <header className="payton-header">
          <div className="payton-container payton-header-inner">
            <div className="payton-logo" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
              <span>PAYTON</span>
            </div>

            <nav className="payton-nav">
              <div
                className="nav-item has-dropdown"
                onMouseEnter={() => setActiveDropdown('homepages')}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <button className="nav-link">
                  HOMEPAGES <ChevronDown size={13} className="dropdown-arrow" />
                </button>
                {activeDropdown === 'homepages' && (
                  <div className="dropdown-menu">
                    <a href="#creative" onClick={(e) => { e.preventDefault(); showToast('Homepage: Creative Agency'); }}>Creative Agency</a>
                    <a href="#studio" onClick={(e) => { e.preventDefault(); showToast('Homepage: Modern Studio'); }}>Modern Studio</a>
                    <a href="#fls" onClick={(e) => { e.preventDefault(); onSwitchToApp?.(); }}>Fire & Safety Compliance MVP</a>
                    <a href="#corporate" onClick={(e) => { e.preventDefault(); showToast('Homepage: Corporate Branding'); }}>Corporate Branding</a>
                  </div>
                )}
              </div>

              <div
                className="nav-item has-dropdown"
                onMouseEnter={() => setActiveDropdown('sliders')}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <button className="nav-link">
                  SLIDERS <ChevronDown size={13} className="dropdown-arrow" />
                </button>
                {activeDropdown === 'sliders' && (
                  <div className="dropdown-menu">
                    <a href="#revolution" onClick={(e) => { e.preventDefault(); showToast('Revolution Fullscreen Slider'); }}>Revolution Slider</a>
                    <a href="#parallax" onClick={(e) => { e.preventDefault(); showToast('3D Parallax Motion'); }}>3D Parallax Motion</a>
                    <a href="#cad-preview" onClick={(e) => { e.preventDefault(); onSwitchToApp?.(); }}>CAD Interactive Viewer</a>
                  </div>
                )}
              </div>

              <div
                className="nav-item has-dropdown"
                onMouseEnter={() => setActiveDropdown('hero')}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <button className="nav-link">
                  HERO SCENES <ChevronDown size={13} className="dropdown-arrow" />
                </button>
                {activeDropdown === 'hero' && (
                  <div className="dropdown-menu">
                    <a href="#design-exp" onClick={(e) => { e.preventDefault(); showToast('Selected: Better Design Experiences'); }}>Design Experiences</a>
                    <a href="#abstract" onClick={(e) => { e.preventDefault(); showToast('Selected: Abstract 3D Red Geometry'); }}>Abstract 3D Geometric</a>
                  </div>
                )}
              </div>

              <a href="#blog" className="nav-link single" onClick={(e) => { e.preventDefault(); showToast('Opening Payton Blog...'); }}>
                BLOG
              </a>

              <div
                className="nav-item has-dropdown"
                onMouseEnter={() => setActiveDropdown('shop')}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <button className="nav-link">
                  SHOP <ChevronDown size={13} className="dropdown-arrow" />
                </button>
                {activeDropdown === 'shop' && (
                  <div className="dropdown-menu">
                    <a href="#shop-grid" onClick={(e) => { e.preventDefault(); setShowCartModal(true); }}>Theme Catalog ($49)</a>
                    <a href="#addons" onClick={(e) => { e.preventDefault(); setShowCartModal(true); }}>FLS CAD Add-ons</a>
                  </div>
                )}
              </div>

              <div
                className="nav-item has-dropdown"
                onMouseEnter={() => setActiveDropdown('pages')}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <button className="nav-link">
                  PAGES <ChevronDown size={13} className="dropdown-arrow" />
                </button>
                {activeDropdown === 'pages' && (
                  <div className="dropdown-menu">
                    <a href="#about" onClick={() => document.getElementById('about-section')?.scrollIntoView({ behavior: 'smooth' })}>About Payton</a>
                    <a href="#services" onClick={() => document.getElementById('services-section')?.scrollIntoView({ behavior: 'smooth' })}>Our Services</a>
                    <a href="#project" onClick={() => document.getElementById('featured-section')?.scrollIntoView({ behavior: 'smooth' })}>Featured Project</a>
                  </div>
                )}
              </div>

              <div
                className="nav-item has-dropdown"
                onMouseEnter={() => setActiveDropdown('elements')}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <button className="nav-link">
                  ELEMENTS <ChevronDown size={13} className="dropdown-arrow" />
                </button>
                {activeDropdown === 'elements' && (
                  <div className="dropdown-menu">
                    <a href="#buttons" onClick={(e) => { e.preventDefault(); showToast('Modern UI Buttons & Cards'); }}>Typography & Buttons</a>
                    <a href="#abstract-shapes" onClick={(e) => { e.preventDefault(); showToast('3D Abstract Ruby Backgrounds'); }}>Abstract 3D Shapes</a>
                  </div>
                )}
              </div>

              <a href="#contact" className="nav-link single" onClick={(e) => { e.preventDefault(); setShowContactModal(true); }}>
                CONTACT
              </a>

              <button className="nav-cart-btn" onClick={() => setShowCartModal(true)}>
                <ShoppingCart size={14} />
                <span>{cartCount} ITEMS</span>
              </button>

              {/* Seamless switch button to FLS Review App */}
              <button className="nav-app-switch-btn" onClick={onSwitchToApp} title="Switch to FLS Compliance Review Workspace">
                <ShieldCheck size={14} />
                <span>LAUNCH FLS APP</span>
              </button>
            </nav>
          </div>
        </header>

        {/* HERO COPY & CALL TO ACTION */}
        <div className="payton-container payton-hero-content">
          <div className="hero-text-block">
            <h1 className="hero-main-title">
              Better <span className="text-red-highlight">Design</span> Experiences
            </h1>
            <p className="hero-subtext">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer adipiscing
              erat eget risus sollicitudin pellentesque et.
            </p>
            <div className="hero-actions-row">
              <button className="btn-payton-solid-red" onClick={() => setShowBuyModal(true)}>
                BUY NOW
              </button>
              <button
                className="btn-payton-outline-white"
                onClick={() => document.getElementById('services-section')?.scrollIntoView({ behavior: 'smooth' })}
              >
                LEARN MORE
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 3. PROMO RIBBON / BANNER WITH POINTER TAB */}
      <section className="payton-promo-ribbon">
        <div className="payton-container promo-ribbon-inner">
          <div className="promo-left">
            <h2 className="promo-title">PAYTON WORDPRESS THEME</h2>
            <p className="promo-desc">
              Est eu quem suscipit, quaeque ponderum pertinacia qui id, ex inani eripuit legimus pro. Ut nobis
              senserit his. Aim vide senserit id, appareat similique qui.
            </p>
          </div>
          <div className="promo-right">
            <button className="btn-payton-solid-white" onClick={() => setShowBuyModal(true)}>
              BUY NOW
            </button>
            <button
              className="btn-payton-outline-white-border"
              onClick={() => document.getElementById('about-section')?.scrollIntoView({ behavior: 'smooth' })}
            >
              LEARN MORE
            </button>
          </div>
        </div>

        {/* Pointer notch (triangle tab pointing down to Our Services) */}
        <div className="promo-down-notch" onClick={() => document.getElementById('services-section')?.scrollIntoView({ behavior: 'smooth' })}>
          <div className="notch-triangle"></div>
          <ChevronDown size={14} className="notch-arrow" />
        </div>
      </section>

      {/* 4. OUR SERVICES SECTION */}
      <section id="services-section" className="payton-services-section">
        <div className="payton-container services-layout-grid">
          {/* Left Column: Heading + Intro + Squiggly Wave */}
          <div className="services-left-col">
            <h2 className="section-title-dark">Our Services</h2>
            <p className="section-paragraph-muted">
              Etiam non erat mi. Etiam congue et augue sed tempus. Aenean sed
              ipsum luctus, scelerisque ipsum nec, iaculis justo. Sed at vestibulum.
            </p>
            <SquigglyWave color="#333333" width={56} height={10} className="mt-wave" />
          </div>

          {/* Right Column: 2x3 Grid of Services */}
          <div className="services-right-grid">
            {servicesData.map((svc) => (
              <div
                key={svc.id}
                className="service-card-item"
                onClick={() => setSelectedService(svc)}
              >
                <div className="service-icon-wrap">
                  {svc.icon}
                </div>
                <h3 className="service-title-text">{svc.title}</h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 5. ABOUT PAYTON SECTION */}
      <section id="about-section" className="payton-about-section">
        <div className="payton-container about-layout-grid">
          <div className="about-left-col">
            <span className="eyebrow-label">ABOUT PAYTON</span>
            <h2 className="about-heading-heavy">
              Creative startups make classic businesses effective and profitable
            </h2>
          </div>
          <div className="about-right-col">
            <p className="about-body-p">
              Digital marketing's development since the 1990s and 2000s has changed the way brands and businesses use technology for marketing. Digital platforms are increasingly incorporated into marketing plans and everyday life as people switch to digital devices en masse.
            </p>
            <p className="about-body-p">
              Chief among the new methods are search engine optimization (SEO), search engine marketing (SEM), content marketing, influencer marketing and content automation.
            </p>
          </div>
        </div>
      </section>

      {/* 6. FEATURED PROJECT SECTION WITH 3D ABSTRACT RED GEOMETRIC BACKGROUND */}
      <section
        id="featured-section"
        className="payton-featured-section"
        style={{ backgroundImage: `url(${abstractRedImg})` }}
      >
        <div className="featured-abstract-overlay"></div>
        <div className="payton-container featured-content-inner">
          {/* Centered Header */}
          <div className="featured-head-center">
            <h2 className="featured-title-white">Featured Project</h2>
            <p className="featured-sub-white">
              Donec quam felis, ultricies nec, esque eu, pretium quis, sem. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu.
            </p>
            <SquigglyWave color="#ffffff" width={56} height={10} className="mx-auto-wave" />
          </div>

          {/* Overlapping Project Showcase Card */}
          <div className="featured-project-card">
            <div className="project-card-image-half" style={{ backgroundImage: `url(${financeImg})` }}>
              <div className="project-image-badge">FINANCE CASE STUDY</div>
            </div>
            <div className="project-card-info-half">
              <h3 className="project-info-title">Corporate Branding</h3>
              <p className="project-info-text">
                Donec quam felis, ultricies nec, esque eu, pretium quis, sem. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu.
              </p>
              <button className="btn-payton-solid-red" onClick={() => { showToast('Project details loaded!'); onSwitchToApp?.(); }}>
                GET STARTED
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 7. QUICK ACTION FOOTER BAR */}
      <footer className="payton-footer-bottom">
        <div className="payton-container footer-bottom-inner">
          <div className="footer-copyright">
            © 2026 PAYTON WordPress Theme. All Rights Reserved. Built with precision and aesthetic excellence.
          </div>
          <div className="footer-links">
            <a href="#privacy" onClick={(e) => { e.preventDefault(); showToast('Privacy Policy'); }}>Privacy</a>
            <a href="#terms" onClick={(e) => { e.preventDefault(); showToast('Terms of Service'); }}>Terms</a>
            <button className="footer-switch-btn" onClick={onSwitchToApp}>
              <ShieldCheck size={14} /> Open FLS Egress Checker
            </button>
          </div>
        </div>
      </footer>

      {/* FLOATING APP SWITCHER DOCK (Bottom Right) */}
      <div className="payton-floating-dock">
        <button
          className="floating-switch-main-btn"
          onClick={onSwitchToApp}
          title="Switch to FLS Fire & Life Safety Compliance Suite"
        >
          <div className="dock-icon-pulse">
            <ShieldCheck size={18} />
          </div>
          <div className="dock-label-group">
            <span className="dock-title">FLS Safety Suite</span>
            <span className="dock-subtitle">Inspect Drawings & UAE Code ↗</span>
          </div>
        </button>
      </div>

      {/* SERVICE DETAILS MODAL */}
      {selectedService && (
        <div className="payton-modal-backdrop" onClick={() => setSelectedService(null)}>
          <div className="payton-modal-box" onClick={(e) => e.stopPropagation()}>
            <button className="payton-modal-close" onClick={() => setSelectedService(null)}>
              <X size={18} />
            </button>
            <div className="modal-icon-badge">
              {selectedService.icon}
            </div>
            <h3 className="modal-title-bold">{selectedService.title}</h3>
            <p className="modal-desc-body">{selectedService.desc}</p>
            <div className="modal-feature-list">
              <div className="feature-check-item">
                <Check size={14} className="text-red" />
                <span>Custom design system & typography tokens</span>
              </div>
              <div className="feature-check-item">
                <Check size={14} className="text-red" />
                <span>Cross-platform responsiveness & high performance</span>
              </div>
              <div className="feature-check-item">
                <Check size={14} className="text-red" />
                <span>Production-ready source code and vector assets</span>
              </div>
            </div>
            <div className="modal-actions-row">
              <button
                className="btn-payton-solid-red full-w"
                onClick={() => {
                  setCartCount(prev => prev + 1);
                  setSelectedService(null);
                  showToast(`Added "${selectedService.title}" to cart!`);
                }}
              >
                ORDER SERVICE ($299)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SHOP / CART MODAL */}
      {showCartModal && (
        <div className="payton-modal-backdrop" onClick={() => setShowCartModal(false)}>
          <div className="payton-modal-box" onClick={(e) => e.stopPropagation()}>
            <button className="payton-modal-close" onClick={() => setShowCartModal(false)}>
              <X size={18} />
            </button>
            <div className="modal-icon-badge">
              <ShoppingCart size={26} />
            </div>
            <h3 className="modal-title-bold">Payton Theme & Suite Cart</h3>
            <p className="modal-desc-body">
              {cartCount === 0 ? 'Your cart is currently empty. Add the Payton Theme package to start building.' : `You have ${cartCount} items in your active cart.`}
            </p>
            <div className="cart-item-preview">
              <div className="ci-left">
                <b>PAYTON WordPress Theme License</b>
                <span>Includes 12 Demos, 60+ Elements, Free Updates</span>
              </div>
              <div className="ci-price">$49.00</div>
            </div>
            <div className="modal-actions-row">
              <button
                className="btn-payton-solid-red full-w"
                onClick={() => {
                  setShowCartModal(false);
                  showToast('Checkout completed successfully! Thank you.');
                  setCartCount(0);
                }}
              >
                PROCEED TO CHECKOUT ($49)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BUY NOW MODAL */}
      {showBuyModal && (
        <div className="payton-modal-backdrop" onClick={() => setShowBuyModal(false)}>
          <div className="payton-modal-box" onClick={(e) => e.stopPropagation()}>
            <button className="payton-modal-close" onClick={() => setShowBuyModal(false)}>
              <X size={18} />
            </button>
            <div className="modal-icon-badge">
              <Sparkles size={26} />
            </div>
            <h3 className="modal-title-bold">Get Payton WordPress Theme</h3>
            <p className="modal-desc-body">
              Unlock the complete Payton Theme with all 814k+ downloadable assets, full responsive layouts, and FLS architectural compliance tools.
            </p>
            <div className="pricing-box-pill">
              <span className="price-big">$49</span>
              <span className="price-sub">One-time payment • Lifetime updates</span>
            </div>
            <div className="modal-actions-row">
              <button
                className="btn-payton-solid-red full-w"
                onClick={() => {
                  setShowBuyModal(false);
                  showToast('License key sent to your email!');
                }}
              >
                PURCHASE REGULAR LICENSE
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONTACT MODAL */}
      {showContactModal && (
        <div className="payton-modal-backdrop" onClick={() => setShowContactModal(false)}>
          <div className="payton-modal-box" onClick={(e) => e.stopPropagation()}>
            <button className="payton-modal-close" onClick={() => setShowContactModal(false)}>
              <X size={18} />
            </button>
            <div className="modal-icon-badge">
              <Send size={26} />
            </div>
            <h3 className="modal-title-bold">Contact Payton Studio</h3>
            <p className="modal-desc-body">
              Leave your message or inquiry and our design & compliance engineering team will respond within 24 hours.
            </p>
            <div className="contact-form-fields">
              <input type="text" placeholder="Your Name" className="contact-input" defaultValue="Sarah Miller" />
              <input type="email" placeholder="Your Email Address" className="contact-input" defaultValue="sarah@example.com" />
              <textarea placeholder="How can we help your business?" className="contact-textarea" rows="3" defaultValue="Hi, I'm interested in deploying Payton for our new architectural agency website."></textarea>
            </div>
            <button
              className="btn-payton-solid-red full-w"
              onClick={() => {
                setShowContactModal(false);
                showToast('Message sent! We will get back to you shortly.');
              }}
            >
              SEND MESSAGE
            </button>
          </div>
        </div>
      )}

      {/* TOAST NOTIFICATION */}
      {toastMessage && (
        <div className="payton-toast-banner">
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}
