import streamlit as st


def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0,0&display=block');
    :root {
        --ww-blue: #168fe5;
        --ww-blue-dark: #0a66c2;
        --ww-ink: #17192f;
        --ww-muted: #667085;
        --ww-panel: #f3f7fb;
        --ww-border: #dde7f1;
    }
    html, body, button, input, textarea, select {
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"],
    [data-testid="stMetric"],
    [data-testid="stSelectbox"],
    [data-testid="stTabs"],
    [data-testid="stCaptionContainer"] {
        font-family: 'Inter', sans-serif !important;
    }
    .material-icons,
    .material-icons-round,
    .material-icons-outlined,
    .material-symbols-rounded,
    .material-symbols-outlined,
    [class*="material-symbols"],
    [data-testid="stIconMaterial"],
    span[data-testid="stIconMaterial"],
    i[data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded' !important;
        font-weight: normal !important;
        font-style: normal !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' !important;
        font-feature-settings: 'liga' !important;
        -webkit-font-smoothing: antialiased !important;
    }
    h1, h2, h3 {
        color: var(--ww-ink);
        letter-spacing: -0.01em;
        font-weight: 700;
    }
    h1 {
        font-size: 3.1rem !important;
        line-height: 1.05 !important;
    }
    h2, h3 {
        font-weight: 650;
    }
    .stMetric label { font-size: 0.85rem; color: #555; }

    section[data-testid="stSidebar"] {
        width: 460px !important;
        min-width: 460px !important;
        background:
            radial-gradient(circle at 18% 8%, rgba(68, 199, 244, 0.18), transparent 30%),
            linear-gradient(180deg, #f8fbff 0%, #eef5fb 56%, #e9f1f8 100%);
        border-right: 1px solid var(--ww-border);
        box-shadow: 12px 0 38px rgba(15, 53, 92, 0.08);
        overflow-x: hidden !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 460px !important;
        min-width: 460px !important;
        max-width: 460px !important;
        box-sizing: border-box !important;
        padding: 1.35rem 1.45rem 2.2rem;
        overflow-x: hidden !important;
    }
    section[data-testid="stSidebar"] * {
        box-sizing: border-box;
    }
    section[data-testid="stSidebar"] [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        padding: 0.4rem 0 1.55rem;
    }
    section[data-testid="stSidebar"] [data-testid="stImage"] img {
        width: 100%;
        max-width: 400px;
        border-radius: 22px;
        border: 1px solid rgba(221, 231, 241, 0.9);
        box-shadow:
            0 22px 55px rgba(15, 80, 140, 0.14),
            inset 0 1px 0 rgba(255, 255, 255, 0.9);
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: var(--ww-ink);
        font-size: 1.45rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.65rem;
    }
    section[data-testid="stSidebar"] label {
        color: var(--ww-ink) !important;
        font-size: 0.98rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
        margin-bottom: 0.44rem !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] {
        margin-bottom: 1.15rem;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        min-height: 58px;
        background: #ffffff;
        border: 1px solid rgba(221, 231, 241, 0.85);
        border-radius: 15px;
        box-shadow: 0 12px 28px rgba(15, 53, 92, 0.07);
        transition: border-color 150ms ease, box-shadow 150ms ease;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div:hover,
    section[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within {
        border-color: rgba(22, 143, 229, 0.5);
        box-shadow: 0 10px 26px rgba(22, 143, 229, 0.12);
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] span,
    section[data-testid="stSidebar"] [data-baseweb="select"] div {
        font-size: 1.02rem;
        color: var(--ww-ink);
    }
    div[data-testid="stSidebarCollapsedControl"] button,
    button[data-testid="baseButton-headerNoPadding"],
    [data-testid="stSidebarNav"] button {
        border-radius: 999px !important;
        border: 1px solid var(--ww-border) !important;
        background: rgba(255, 255, 255, 0.92) !important;
        box-shadow: 0 8px 24px rgba(15, 53, 92, 0.12) !important;
        color: var(--ww-blue-dark) !important;
    }
    div[data-testid="stSidebarCollapsedControl"] button:hover,
    button[data-testid="baseButton-headerNoPadding"]:hover,
    [data-testid="stSidebarNav"] button:hover {
        border-color: rgba(22, 143, 229, 0.55) !important;
        box-shadow: 0 10px 28px rgba(22, 143, 229, 0.18) !important;
    }
    button[data-testid="baseButton-headerNoPadding"] {
        width: 42px !important;
        height: 42px !important;
        font-size: 0 !important;
        position: relative !important;
        overflow: hidden !important;
    }
    button[data-testid="baseButton-headerNoPadding"] * {
        display: none !important;
    }
    button[data-testid="baseButton-headerNoPadding"]::after {
        content: "‹‹";
        font-family: 'Inter', sans-serif !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        color: var(--ww-blue-dark);
    }
    div[data-testid="stSidebarCollapsedControl"] button {
        width: 42px !important;
        height: 42px !important;
        font-size: 0 !important;
        position: relative !important;
        overflow: hidden !important;
    }
    div[data-testid="stSidebarCollapsedControl"] button * {
        display: none !important;
    }
    div[data-testid="stSidebarCollapsedControl"] button::after {
        content: "››";
        font-family: 'Inter', sans-serif !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        color: var(--ww-blue-dark);
    }
    [data-testid="stHeader"] [data-testid="stIconMaterial"],
    [data-testid="stHeader"] [class*="material-symbols"],
    section[data-testid="stSidebar"] [data-testid="stIconMaterial"],
    section[data-testid="stSidebar"] [class*="material-symbols"] {
        font-size: 0 !important;
        max-width: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
    }
    .ww-filter-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        color: var(--ww-blue-dark);
        background: rgba(22, 143, 229, 0.09);
        border: 1px solid rgba(22, 143, 229, 0.16);
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.38rem 0.65rem;
        margin: 0.15rem 0 0.6rem;
    }
    .ww-metric-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid rgba(221, 231, 241, 0.95);
        border-radius: 18px;
        padding: 1.05rem 1.15rem;
        box-shadow: 0 14px 34px rgba(15, 53, 92, 0.07);
        min-height: 116px;
    }
    .ww-metric-label {
        color: #667085;
        font-size: 0.88rem;
        font-weight: 700;
        letter-spacing: 0.01em;
        margin-bottom: 0.35rem;
    }
    .ww-metric-value {
        color: var(--ww-ink);
        font-size: 2.35rem;
        line-height: 1;
        font-weight: 750;
        letter-spacing: -0.04em;
    }
    .ww-metric-sub {
        color: #7b8496;
        font-size: 0.82rem;
        margin-top: 0.4rem;
    }
    .ww-section-caption {
        color: #667085;
        font-size: 0.95rem;
        line-height: 1.5;
        margin: -0.25rem 0 1.15rem;
    }
    .ww-loader-overlay {
        position: fixed;
        inset: 0;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        background:
            radial-gradient(circle at 50% 42%, rgba(22, 143, 229, 0.16), transparent 22%),
            rgba(7, 12, 18, 0.92);
        backdrop-filter: blur(4px);
    }
    .ww-loader-panel {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1.3rem;
        min-width: 260px;
        padding: 2.1rem 2.3rem;
        border-radius: 24px;
        background: rgba(13, 24, 36, 0.64);
        border: 1px solid rgba(106, 213, 255, 0.18);
        box-shadow: 0 28px 80px rgba(0, 0, 0, 0.35);
    }
    .ww-loader-dots {
        position: relative;
        width: 92px;
        height: 92px;
        animation: ww-loader-spin 1.2s linear infinite;
    }
    .ww-loader-dots span {
        position: absolute;
        top: 38px;
        left: 38px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: #23c7f4;
        box-shadow: 0 0 18px rgba(35, 199, 244, 0.55);
        transform-origin: 8px 8px;
    }
    .ww-loader-dots span:nth-child(1) { transform: rotate(0deg) translate(0, -34px); opacity: 1; }
    .ww-loader-dots span:nth-child(2) { transform: rotate(36deg) translate(0, -34px); opacity: .92; }
    .ww-loader-dots span:nth-child(3) { transform: rotate(72deg) translate(0, -34px); opacity: .84; }
    .ww-loader-dots span:nth-child(4) { transform: rotate(108deg) translate(0, -34px); opacity: .76; }
    .ww-loader-dots span:nth-child(5) { transform: rotate(144deg) translate(0, -34px); opacity: .68; }
    .ww-loader-dots span:nth-child(6) { transform: rotate(180deg) translate(0, -34px); opacity: .60; }
    .ww-loader-dots span:nth-child(7) { transform: rotate(216deg) translate(0, -34px); opacity: .52; }
    .ww-loader-dots span:nth-child(8) { transform: rotate(252deg) translate(0, -34px); opacity: .44; }
    .ww-loader-dots span:nth-child(9) { transform: rotate(288deg) translate(0, -34px); opacity: .36; }
    .ww-loader-dots span:nth-child(10) { transform: rotate(324deg) translate(0, -34px); opacity: .28; }
    .ww-loader-text {
        color: #dcebf7;
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        text-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }
    .ww-loader-subtext {
        color: rgba(220, 235, 247, 0.72);
        font-size: 0.9rem;
        margin-top: -0.9rem;
    }
    @keyframes ww-loader-spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    div[data-testid="stSpinner"] {
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        left: 460px !important;
        z-index: 999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 100vh !important;
        padding: 1.5rem !important;
        background:
            radial-gradient(circle at 50% 42%, rgba(35, 199, 244, 0.14), transparent 28%),
            rgba(13, 19, 28, 0.92) !important;
        backdrop-filter: blur(2px);
    }
    div[data-testid="stSpinner"] > div {
        position: relative !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 1rem !important;
        width: min(380px, calc(100vw - 3rem)) !important;
        min-width: 0 !important;
        padding: 2rem 2.1rem !important;
        border-radius: 24px !important;
        background: rgba(13, 24, 36, 0.7) !important;
        border: 1px solid rgba(106, 213, 255, 0.22) !important;
        box-shadow: 0 28px 80px rgba(0, 0, 0, 0.35) !important;
    }
    div[data-testid="stSpinner"] svg,
    div[data-testid="stSpinner"] [role="progressbar"] {
        display: none !important;
    }
    div[data-testid="stSpinner"] > div::before {
        content: "";
        width: 82px;
        height: 82px;
        border-radius: 50%;
        background:
            radial-gradient(circle at 50% 5%, #23c7f4 0 8px, transparent 9px),
            radial-gradient(circle at 79% 17%, rgba(35, 199, 244, .92) 0 8px, transparent 9px),
            radial-gradient(circle at 95% 50%, rgba(35, 199, 244, .82) 0 8px, transparent 9px),
            radial-gradient(circle at 79% 83%, rgba(35, 199, 244, .72) 0 8px, transparent 9px),
            radial-gradient(circle at 50% 95%, rgba(35, 199, 244, .62) 0 8px, transparent 9px),
            radial-gradient(circle at 21% 83%, rgba(35, 199, 244, .52) 0 8px, transparent 9px),
            radial-gradient(circle at 5% 50%, rgba(35, 199, 244, .42) 0 8px, transparent 9px),
            radial-gradient(circle at 21% 17%, rgba(35, 199, 244, .32) 0 8px, transparent 9px);
        filter: drop-shadow(0 0 18px rgba(35, 199, 244, 0.42));
        animation: ww-loader-spin 1.2s linear infinite;
    }
    div[data-testid="stSpinner"] p {
        color: #dcebf7 !important;
        font-size: 1.4rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        text-align: center !important;
        text-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        margin: 0 !important;
    }
    div[data-testid="stSpinner"] p::after {
        content: "Preparando datos y visualizaciones";
        display: block;
        color: rgba(220, 235, 247, 0.72);
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0;
        margin-top: 0.85rem;
        text-shadow: none;
    }
    @media (max-width: 900px) {
        div[data-testid="stSpinner"] {
            left: 0 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def loading_markup(text: str = "Cargando Water Watch...", subtext: str = "Preparando datos y visualizaciones") -> str:
    dots = "".join("<span></span>" for _ in range(10))
    return f"""
    <div class="ww-loader-overlay" aria-live="polite" aria-busy="true">
        <div class="ww-loader-panel">
            <div class="ww-loader-dots">{dots}</div>
            <div class="ww-loader-text">{text}</div>
            <div class="ww-loader-subtext">{subtext}</div>
        </div>
    </div>
    """
