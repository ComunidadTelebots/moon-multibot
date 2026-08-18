const STYLE_ID = "moon-canva-transport-theme";

export function applyCanvaTransportTheme() {
  if (document.getElementById(STYLE_ID)) return { dispose() {} };
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    :root{
      --moon-ink:#050b12;--moon-surface:#091621;--moon-card:#10232f;
      --moon-card-strong:#142d39;--moon-line:#294654;--moon-muted:#8fa8b2;
      --moon-text:#f0fafb;--moon-teal:#55e6d0;--moon-teal-dark:#123b38;
      --moon-orange:#f49a32;--moon-orange-deep:#bf4933;--moon-warning:#ffd166;
      --moon-danger:#ff7065;--moon-radius:16px;--moon-shadow:0 18px 48px #0009;
    }
    body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--moon-text)}
    button,select,input{font:inherit}button{font-weight:700;letter-spacing:.005em}
    .hud{border-color:#ffffff18!important;background:linear-gradient(125deg,#07121df2,#102b36e8)!important;box-shadow:var(--moon-shadow)!important}
    .pill{border:1px solid #ffffff14!important;border-radius:12px!important;background:linear-gradient(145deg,#142936d9,#0b1923d9)!important;color:var(--moon-muted)!important}
    .pill b{color:var(--moon-text)!important}.pill b:first-letter{color:var(--moon-teal)}
    .controls:not(.drive),.controls.drive{border-color:#ffffff1c!important;background:linear-gradient(180deg,#102733ee,#07121cf2)!important;box-shadow:var(--moon-shadow)!important}
    .controls button,.fleet-select,.map-tools button,.cargo-actions button{border:1px solid #ffffff1a!important;border-radius:12px!important;background:linear-gradient(145deg,#162d3a,#0c1c27)!important;color:#e9f5f6!important}
    .controls button:hover,.map-tools button:hover,.cargo-actions button:hover{border-color:#55e6d099!important;transform:translateY(-1px)}
    .controls button.on,.cargo-actions button.on,.map-tools button.on{border-color:var(--moon-teal)!important;background:linear-gradient(145deg,#174940,#10312f)!important;color:#71f4df!important;box-shadow:inset 0 0 20px #55e6d018,0 0 0 1px #55e6d018!important}
    .controls.drive button[data-key="w"],#worldPlanButton,#aviationFlightMode{border-color:#ffb055!important;background:linear-gradient(135deg,var(--moon-orange),var(--moon-orange-deep))!important;color:white!important;box-shadow:0 8px 24px #d75a3145!important}
    button:disabled{opacity:.42!important;filter:saturate(.45);transform:none!important}
    .map-panel,.aviation-deck,.region-ops,.cargo-monitor{border:1px solid #47707b!important;border-radius:20px!important;background:linear-gradient(145deg,#081722f5,#102a35f0)!important;box-shadow:0 28px 80px #000c!important;backdrop-filter:blur(22px)!important}
    .map-panel>header,.aviation-head,.region-ops__hero{margin:-12px -12px 12px!important;padding:14px 16px!important;border-bottom:1px solid #ffffff16!important;background:linear-gradient(105deg,#153742,#0a1924)!important}
    .map-panel h3,.aviation-head h3,.region-ops h2{letter-spacing:-.02em;color:var(--moon-text)!important}
    .world-plan,.route-output,.aviation-route,.region-ops__route{border:1px solid #315966!important;background:#081a24!important;color:#b8d2d7!important}
    .world-plan b,.route-output,.aviation-airport span,.region-ops__access{color:var(--moon-teal)!important}
    .cockpit-panel{border-color:#52636d!important;background:linear-gradient(180deg,#273138f5,#090d11f7)!important;box-shadow:0 -20px 70px #000d,inset 0 1px #ffffff22!important}
    .dash-screen{border-color:#426b72!important;background:radial-gradient(circle at 50% 0,#11343b,#041016 72%)!important;box-shadow:inset 0 0 34px #34cdb01d!important}
    .dash-speed,.dash-navigation b,.dash-status b{color:#efffff!important}.dash-row,.dash-navigation small,.dash-alert{color:var(--moon-teal)!important}
    .dash-buttons button{border:1px solid #344851!important;border-radius:10px!important;background:linear-gradient(145deg,#172229,#0d1418)!important;color:#d8e6e8!important}
    .dash-buttons button.on{border-color:var(--moon-teal)!important;background:var(--moon-teal-dark)!important;color:#75f5e2!important}
    .event-kpi,.cargo-meter,.cargo-card,.moon-action{border-color:#ffffff16!important;background:linear-gradient(145deg,#122833,#0a1923)!important}
    .cargo-selector{display:grid;gap:5px;margin:0 0 10px;color:var(--moon-muted);font-size:10px;text-transform:uppercase;letter-spacing:.08em}.cargo-selector select{padding:10px;border:1px solid var(--moon-line);border-radius:11px;background:#091a24;color:var(--moon-text)}
    .event-kpi b,.cargo-meter b{color:var(--moon-teal)!important}
    .moon-shell{background:radial-gradient(circle at 85% 0,#173a42aa,transparent 38%),linear-gradient(115deg,#050d15fa,#0b1b26f4)!important}
    .moon-shell-nav{background:#06111bed!important}.moon-action i{background:#143b38!important;color:var(--moon-teal)!important}
    .moon-action:hover{border-color:#55e6d080!important;background:linear-gradient(145deg,#17323c,#0c202a)!important}
    .warning,[data-level="warning"]{color:var(--moon-warning)!important}[data-level="critical"]{color:var(--moon-danger)!important}
    @media(max-width:700px){
      .hud{border-radius:14px!important}.map-panel,.aviation-deck,.region-ops{border-radius:17px!important}
      .controls:not(.drive),.controls.drive{border-radius:15px!important}.controls button,.fleet-select{min-height:44px!important}
      .moon-action-grid{grid-template-columns:1fr!important}.moon-action{min-height:92px!important}
    }
    @media(prefers-reduced-motion:reduce){*,*:before,*:after{scroll-behavior:auto!important;animation-duration:.01ms!important;transition-duration:.01ms!important}}
  `;
  document.head.append(style);
  document.documentElement.dataset.moonTheme = "canva";
  return { dispose() { style.remove(); delete document.documentElement.dataset.moonTheme; } };
}

export default applyCanvaTransportTheme;
