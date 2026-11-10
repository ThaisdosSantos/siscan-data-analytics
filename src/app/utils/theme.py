"""Identidade visual PET-Saúde e funções comuns de apresentação."""
import html
import io
import pandas as pd
import streamlit as st
import plotly.express as px

NAVY = "#1A3B5C"
OCEAN = "#006C9A"
SKY = "#4A9FD8"
ORANGE = "#EE5325"
GRAY = "#D9D9D9"
LIGHT_BG = "#F4F6F8"
PALETTE = [OCEAN, SKY, ORANGE, NAVY]

def apply_custom_css():
    """Identidade Lovable: sidebar escura, hero em gradiente e cartões claros."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
    html,body,[data-testid="stAppViewContainer"] {font-family:'Manrope',system-ui,sans-serif;}
    .pet-hero-title,h1,h2,h3 {font-family:'Fraunces',Georgia,serif;}
    :root {--navy:#1A3B5C;--ocean:#006C9A;--sky:#4A9FD8;
           --orange:#EE5325;--gray:#D9D9D9;--light:#F4F6F8;}
    html,body,[data-testid="stAppViewContainer"] {background:#fff;color:#1A3B5C;}
    .block-container {padding:1.25rem 2.1rem 3rem;max-width:1480px;}
    h1,h2,h3,h4 {color:var(--navy)!important;letter-spacing:-.015em;}
    h2,h3 {font-weight:730!important;}
    .pet-hero {background:radial-gradient(120% 140% at 100% 0%,#006C9A 0%,#1A3B5C 66%);
        border-radius:19px;padding:36px 40px 74px;color:white;
        box-shadow:0 16px 36px -22px rgba(26,59,92,.35);margin:0 0 -43px;}
    .pet-hero-kicker {font-weight:750;letter-spacing:.22em;color:#89c8ee;
        font-size:.71rem;text-transform:uppercase;margin:0 0 13px;}
    .pet-hero-title {color:#fff!important;font-size:clamp(1.8rem,3.4vw,3rem);
        font-weight:760;line-height:1.13;letter-spacing:-.035em;margin:0 0 12px;}
    /* Descrição dos cabeçalhos: mesmo padrão de Exames Alterados para todas as páginas. */
    .pet-hero .pet-hero-desc {
        font-family:Manrope,Arial,sans-serif!important;
        font-size:1.15rem!important;
        line-height:1.65!important;
        font-weight:500!important;
        color:#FFFFFF!important;
        max-width:920px!important;
    }
    @media(max-width:768px) {
        .pet-hero .pet-hero-desc {
            font-size:1rem!important;
            line-height:1.55!important;
        }
    }
    .pet-kicker {color:var(--orange);font-size:.73rem;font-weight:780;
                 letter-spacing:.13em;text-transform:uppercase;}
    .pet-note,.pet-highlight {background:#F4F6F8;border-radius:14px;padding:16px 20px;
        border-left:4px solid var(--orange);line-height:1.6;margin:12px 0 20px;}
    .pet-section-label {color:var(--ocean);font-size:.73rem;font-weight:780;letter-spacing:.12em;}
    [data-testid="stSidebar"] {background:#1A3B5C!important;border-right:0!important;color:#e8f3fa;}
    [data-testid="stSidebar"] * {color:#e8f3fa;}
    [data-testid="stSidebar"] [data-testid="stImage"] {background:white;padding:8px;
         border-radius:14px;margin:4px auto 16px;max-width:220px;}
    [data-testid="stSidebar"] [data-testid="stExpander"] {background:#244d70;
        border:1px solid #38617d;border-radius:12px;}
    [data-testid="stSidebar"] [data-testid="stCheckbox"] {padding:1px 0;}
    [data-testid="stSidebar"] button {background:#244d70;color:#fff;border:1px solid #456b87;}
    [data-testid="stSidebar"] button:hover {background:#006C9A;color:white;border-color:#4A9FD8;}
    [data-testid="stSidebarNav"] a {border-radius:11px;padding:.56rem .75rem;}
    [data-testid="stSidebarNav"] a[aria-current="page"] {background:#006C9A!important;}
    [data-testid="stSidebarNav"] a:hover {background:#244d70;}
    [data-testid="stSidebar"] hr {border-color:#456b87;}
    div[data-testid="stMetric"] {background:white;border:1px solid #dfe6ec;
        border-radius:16px;padding:18px 20px;min-height:120px;
        box-shadow:0 1px 2px rgba(26,59,92,.04),0 15px 32px -24px rgba(26,59,92,.3);}
    div[data-testid="stMetricLabel"] {font-weight:700;color:#50667b;font-size:.85rem;}
    div[data-testid="stMetricValue"] {color:#1A3B5C;font-weight:760;}
    /* KPIs das páginas analíticas: mantém a identidade PET-Saúde.
       A Visão Executiva possui cartões HTML próprios e permanece branca. */
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
      [data-testid="stMetric"] {background:#006C9A;border-color:#006C9A;}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
      [data-testid="stMetric"] {background:#EE5325;border-color:#EE5325;}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
      [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
      [data-testid="stMetric"] [data-testid="stMetricValue"],
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
      [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
      [data-testid="stMetric"] [data-testid="stMetricValue"] {color:white!important;}

    [data-testid="stPlotlyChart"] {background:#fff;border:1px solid #e5eaf0;
        padding:12px;border-radius:16px;box-shadow:0 12px 28px -24px rgba(26,59,92,.24);}
    [data-testid="stDataFrame"] {border:1px solid #dfe6ec;border-radius:13px;}
    [data-testid="stExpander"] {border-radius:12px;border-color:#dfe6ec;}
    .stButton button[kind="primary"] {background:#EE5325;color:white;border-color:#EE5325;}
    .stDownloadButton button {background:#EE5325!important;color:white!important;
        border:0!important;border-radius:20px!important;}
    @media(max-width:900px) {
      .block-container {padding:1rem .85rem 2rem;}
      .pet-hero {padding:24px 22px 60px;border-radius:13px;}
    }

    [data-testid="stSidebarNav"] {display:none!important;}
    [data-testid="stAppViewContainer"] {background:#f8fafb!important;}
    [data-testid="stSidebar"][aria-expanded="true"] {width:300px!important;min-width:300px!important;}
    .lovable-brand {display:flex;align-items:center;gap:12px;padding:14px 6px 22px;}
    .lovable-mark {
      display:grid;place-items:center;flex:0 0 46px;
      width:46px;height:46px;background:#fff;
      border:1px solid rgba(255,255,255,.25);
      border-radius:12px;overflow:hidden;padding:3px;
    }
    .lovable-mark img {
      display:block;width:100%;height:100%;object-fit:contain;
      border-radius:7px;background:#fff;
    }
    .lovable-brand strong {display:block;font-size:1.3rem;color:white;font-weight:800;}
    .lovable-brand small {display:block;color:#c3d7e6;font-size:.74rem;}
    .lovable-label {font-weight:800;color:#9cc5de!important;font-size:.68rem;letter-spacing:.15em;margin:14px 0 9px;}
    .lovable-footer {font-size:.72rem;line-height:1.8;color:#bad0df!important;border-top:1px solid #456b87;margin-top:20px;padding-top:18px;}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a {padding:10px 13px;border-radius:10px;font-weight:650;text-decoration:none;}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {background:#285778;}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {background:#006c9a!important;}
    [data-testid="stSidebar"] [data-testid="stButton"] button {min-height:34px;border-radius:9px;font-size:.8rem;padding:4px;}
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {background:#006c9a!important;border-color:#4a9fd8!important;}
    .pet-hero {min-height:185px;padding-bottom:75px;}
    [data-testid="stMetricValue"] {font-size:1.85rem;}

    /* Responsividade compartilhada — desktop, tablet e smartphone. */
    *, *::before, *::after {box-sizing:border-box;}
    [data-testid="stAppViewContainer"], .block-container {min-width:0;}
    .block-container {width:100%;max-width:1480px;margin:0 auto;}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width:0;}
    [data-testid="stPlotlyChart"],[data-testid="stPlotlyChart"] > div {max-width:100%;min-width:0;}
    [data-testid="stImage"] img {max-width:100%;height:auto;}
    .pet-hero-title,.pet-hero-desc,.exec-title,.exec-sub {overflow-wrap:anywhere;}
    .pet-table-scroller,.q3-matrix-scroll {max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;}
    @media (max-width:1100px) {
      .block-container {padding:1.1rem 1.2rem 2rem;}
      [data-testid="stSidebar"][aria-expanded="true"] {width:min(300px,85vw)!important;min-width:0!important;}
    }
    @media (max-width:768px) {
      .block-container {padding:0.85rem 0.8rem 2rem;}
      .pet-hero {padding:23px 20px 42px;min-height:0;margin-bottom:0;}
      .pet-hero-title {font-size:clamp(1.55rem,6vw,2.2rem);}
      .pet-hero-desc {font-size:.84rem;}
      [data-testid="stMetric"] {min-height:100px;padding:14px 15px;}
      [data-testid="stMetricValue"] {font-size:clamp(1.35rem,5vw,1.85rem)!important;}
      [data-testid="stPlotlyChart"] {padding:5px;border-radius:12px;}
      .stDownloadButton button {max-width:100%;white-space:normal;}
      .pet-table th,.pet-table td,.q3-matrix th,.q3-matrix td {padding:10px 9px;}
    }
    @media (max-width:480px) {
      .block-container {padding:0.65rem 0.55rem 2rem;}
      .pet-hero {padding:18px 15px 28px;}
      .pet-hero-title {font-size:1.55rem;}
      [data-testid="stSidebar"][aria-expanded="true"] {width:min(300px,92vw)!important;}
      [data-testid="stSidebar"] [data-testid="stButton"] button {min-height:42px;}
      [data-testid="stPageLink"] a {overflow-wrap:anywhere;}
    }

    /* Resumo do recorte — padrão compartilhado de todas as páginas. */
    .pet-active-scope{display:flex;align-items:center;flex-wrap:wrap;gap:8px;
      margin-top:17px;max-width:100%;font-family:Manrope,Arial,sans-serif;}
    .pet-scope-label{font-size:.65rem;letter-spacing:.17em;font-weight:800;
      color:#b0d3e9!important;margin-right:3px;white-space:nowrap;}
    .pet-scope-chip{display:inline-flex;align-items:center;gap:7px;
      border-radius:999px;background:rgba(255,255,255,.11);
      border:1px solid rgba(194,222,241,.19);color:#f5fbff!important;
      padding:6px 12px;font-size:.74rem;font-weight:600;line-height:1.25;
      max-width:100%;white-space:normal;}
    .pet-scope-icon{color:#8ac9ee!important;display:inline-flex;align-items:center;justify-content:center;flex:0 0 15px;line-height:1;}\n    .pet-scope-icon svg{display:block;width:15px;height:15px;}
    @media(max-width:550px){
      .pet-active-scope{gap:6px;margin-top:14px;}
      .pet-scope-label{flex-basis:100%;margin-bottom:2px;}
      .pet-scope-chip{padding:6px 10px;font-size:.71rem;}
    }

    /* Painel de filtros, inspirado nos estados compacto/expandido. */
    .st-key-siscan_filter_panel{
      background:#20496b;border:1px solid #355d7d;border-radius:18px;
      padding:11px 10px 12px;margin:8px 0 15px;
    }
    .st-key-siscan_filter_panel .filter-panel-title{
      font-size:.67rem;letter-spacing:.17em;font-weight:800;color:#9fc8e2!important;
      padding:3px 5px 10px;
    }
    .st-key-siscan_filter_panel [data-testid="stExpander"]{
      background:#1c4161!important;border:1px solid #37617f!important;
      border-radius:14px!important;margin:4px 0 8px;overflow:hidden;
    }
    .st-key-siscan_filter_panel [data-testid="stExpander"] summary{
      padding:11px 10px!important;color:#f1f8fd!important;
      font-size:.83rem;font-weight:650;
    }
    .st-key-siscan_filter_panel [data-testid="stExpander"] summary:hover{
      background:#265579!important;
    }
    .st-key-siscan_filter_panel [data-testid="stExpander"] [data-testid="stCaptionContainer"]{
      color:#b8d0e2!important;font-size:.7rem!important;
    }
    .st-key-siscan_filter_panel [data-testid="stButton"] button{
      min-height:32px!important;padding:3px 5px!important;border-radius:18px!important;
      font-size:.74rem!important;border:1px solid #3a6685!important;
      background:#214769!important;color:#d3e7f3!important;
      box-shadow:none!important;
    }
    .st-key-siscan_filter_panel [data-testid="stButton"] button[kind="primary"]{
      background:#006C9A!important;border-color:#55a4cc!important;
      color:white!important;
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"]{
      border-bottom:1px solid rgba(162,194,214,.10);
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] label{
      min-height:31px!important;padding:3px 4px!important;
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] input{
      accent-color:#EE5325!important;
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] label:hover{
      background:#295776;border-radius:7px;
    }
    @media(max-width:480px){
      .st-key-siscan_filter_panel{padding:10px 8px;}
      .st-key-siscan_filter_panel [data-testid="stButton"] button{min-height:40px!important;}
    }

    /* Estado visual dos filtros de acordo com a referência: laranja = selecionado. */
    .st-key-siscan_filter_panel .filter-progress{
      height:4px;width:100%;border-radius:99px;background:#183a57;
      overflow:hidden;margin:4px 0 13px;
    }
    .st-key-siscan_filter_panel .filter-progress span{
      display:block;height:100%;background:#EE5325;border-radius:99px;
      transition:width .18s ease-out;
    }
    .st-key-siscan_filter_panel .filter-period-label{
      margin:8px 2px 3px;font-size:.71rem;color:#a3bbcf!important;
      line-height:1.4;
    }
    .st-key-siscan_filter_panel [data-testid="stPills"]{
      width:100%;
    }
    .st-key-siscan_filter_panel [data-testid="stPills"] > div{
      display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));
      gap:8px!important;width:100%;
    }
    .st-key-siscan_filter_panel [data-testid="stPills"] button{
      width:100%!important;min-width:0!important;
      border-radius:999px!important;
      min-height:35px!important;padding:6px 3px!important;
      background:#1d4262!important;border:1px solid #386584!important;
      color:#9bb5c8!important;font-size:.77rem!important;
      font-weight:650!important;box-shadow:none!important;
    }
    .st-key-siscan_filter_panel [data-testid="stPills"] button[aria-pressed="true"],
    .st-key-siscan_filter_panel [data-testid="stPills"] button[data-selected="true"],
    .st-key-siscan_filter_panel [data-testid="stPills"] button[aria-checked="true"]{
      background:#EE5325!important;border-color:#EE5325!important;
      color:white!important;
    }
    .st-key-siscan_filter_panel [data-testid="stPills"] button:hover{
      border-color:#6a99b4!important;color:white!important;
    }
    .st-key-siscan_filter_panel [data-testid="stPills"] button[aria-pressed="true"]:hover,
    .st-key-siscan_filter_panel [data-testid="stPills"] button[data-selected="true"]:hover{
      background:#e64c20!important;border-color:#e64c20!important;
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"]{
      background:transparent;border-bottom:none!important;
      margin:2px 0!important;padding:0!important;
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] label{
      display:flex;align-items:center;border:1px solid #345a77!important;
      background:#1b405e!important;border-radius:99px!important;
      padding:4px 10px!important;min-height:33px!important;
      transition:border-color .15s,background .15s;
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] label:hover{
      background:#255174!important;border-color:#5785a3!important;
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] label:has(input:checked),
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] label:has([aria-checked="true"]){
      border-color:#477390!important;
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] [data-baseweb="checkbox"]>div:first-child,
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] [role="checkbox"]{
      border-radius:50%!important;
    }
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] input:checked + div,
    .st-key-siscan_filter_panel [data-testid="stCheckbox"] [aria-checked="true"]{
      background-color:#EE5325!important;border-color:#EE5325!important;
    }
    .st-key-siscan_filter_panel [data-testid="stFormSubmitButton"] button[kind="primary"]{
      background:#EE5325!important;border-color:#EE5325!important;
      color:#fff!important;min-height:41px!important;border-radius:10px!important;
    }

    /* Correção de contraste no cabeçalho aberto e seleção por pílulas. */
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stExpander"] details,
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stExpander"] details > summary,
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stExpander"] summary,
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stExpander"] summary[aria-expanded="true"] {
        background:#1c4161!important;color:#f0f8ff!important;
        border-color:#37617f!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stExpander"] summary *,
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stExpander"] summary p {
        color:#f0f8ff!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button[data-testid="stBaseButton-pillsActive"],
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button[aria-pressed="true"],
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button[aria-selected="true"] {
        background:#EE5325!important;color:white!important;
        border:1px solid #EE5325!important;box-shadow:none!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button[data-testid="stBaseButton-pills"],
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button[aria-pressed="false"] {
        background:#1c4161!important;color:#a8bfd0!important;
        border:1px solid #37617f!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button[data-testid="stBaseButton-pillsActive"]:hover{
        background:#db491e!important;color:white!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stCheckbox"] [data-testid="stCheckbox"]{
        accent-color:#EE5325;
    }

    /* Painel de filtros — estados compacto e expandido da referência. */
    [data-testid="stSidebar"] .st-key-siscan_filter_panel {
      background:#204767!important;border:1px solid #315a78!important;
      border-radius:22px!important;padding:11px 10px 12px!important;
      box-shadow:none!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel .filter-panel-title{
      color:#a3c3d8!important;font-size:11px!important;
      font-weight:700!important;letter-spacing:.17em!important;
      margin:0!important;padding:0 8px 10px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel,
    [data-testid="stSidebar"] .st-key-siscan_city_panel{
      min-width:0;margin:0 0 8px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel [data-testid="stExpander"],
    [data-testid="stSidebar"] .st-key-siscan_city_panel [data-testid="stExpander"]{
      border:1px solid #376282!important;border-radius:18px!important;
      background:#1b405f!important;overflow:hidden!important;
      box-shadow:none!important;margin:0!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details{
      border:0!important;background:#1b405f!important;color:#f1f7fc!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary{
      position:relative!important;box-sizing:border-box!important;
      display:flex!important;align-items:center!important;
      padding:0 46px 0 49px!important;min-height:51px!important;
      background:#1b405f!important;color:#f1f7fc!important;
      border:0!important;outline-offset:-2px!important;
      font-size:12px!important;line-height:1.1!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details:not([open])>summary,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details:not([open])>summary{
      min-height:59px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary:hover,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary:hover{
      background:#214c6b!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary svg,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary svg{
      color:#54a4d5!important;fill:none!important;
    }
    /* O expander mantém o ícone do calendário/localização, ocultando só a seta padrão. */
    [data-testid="stSidebar"] .st-key-siscan_filter_panel summary [data-testid="stExpanderToggleIcon"]{
      display:none!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary::before,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary::before{
      content:"+"!important;position:absolute!important;left:11px!important;
      top:50%!important;transform:translateY(-50%)!important;
      display:grid!important;place-items:center!important;
      width:19px!important;height:19px!important;
      border:1px solid #317eac!important;border-radius:5px!important;
      color:#69b8e5!important;background:rgba(23,91,133,.24)!important;
      font:600 16px/1 Manrope,Arial,sans-serif!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details[open]>summary::before,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details[open]>summary::before{
      content:"−"!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary::after,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary::after{
      position:absolute!important;right:10px!important;top:50%!important;
      transform:translateY(-50%)!important;display:block!important;
      padding:4px 8px!important;border-radius:999px!important;
      border:1px solid #315979!important;background:#1a3d5b!important;
      color:#5aa8d7!important;letter-spacing:.02em!important;
      font:650 10px/1.1 Manrope,Arial,sans-serif!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stMarkdownContainer"]{
      position:static!important;min-width:0!important;
      font-weight:650!important;color:white!important;
      overflow:visible!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details:not([open])>summary [data-testid="stMarkdownContainer"]::after,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details:not([open])>summary [data-testid="stMarkdownContainer"]::after{
      position:absolute!important;left:49px!important;top:35px!important;
      display:block!important;max-width:calc(100% - 105px)!important;
      overflow:hidden!important;white-space:nowrap!important;text-overflow:ellipsis!important;
      color:#86a9c0!important;font:400 10px/1.1 Manrope,Arial,sans-serif!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel [data-testid="stExpanderDetails"],
    [data-testid="stSidebar"] .st-key-siscan_city_panel [data-testid="stExpanderDetails"]{
      border-top:1px solid #335d7b!important;
      padding:11px 11px 12px!important;background:#1b405f!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel .filter-progress{
      height:4px!important;margin:2px 0 12px!important;
      background:#183953!important;border-radius:99px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel .filter-progress span{
      background:#EE5325!important;border-radius:99px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"]{
      width:100%!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"]>div{
      display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;
      width:100%!important;gap:6px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button{
      width:100%!important;min-width:0!important;min-height:33px!important;
      padding:5px 2px!important;border-radius:999px!important;
      font:650 11px Manrope,Arial,sans-serif!important;
      background:#1d4160!important;color:#7b9ab1!important;
      border:1px solid #315977!important;box-shadow:none!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button[data-testid="stBaseButton-pillsActive"],
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button[aria-pressed="true"]{
      background:#EE5325!important;color:white!important;border-color:#EE5325!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stPills"] button[data-testid="stBaseButton-pillsActive"]:hover{
      background:#e84e22!important;border-color:#e84e22!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stButton"] button{
      background:#1c405f!important;color:#dcecf5!important;
      border:1px solid #315b78!important;border-radius:999px!important;
      min-height:27px!important;font:500 11px Manrope,Arial,sans-serif!important;
      box-shadow:none!important;
    }
    /* Lista de municípios: cada linha ocupa 100% do painel, sem cápsulas
       de largura variável nem o espaçamento padrão entre widgets. */
    [data-testid="stSidebar"] .st-key-siscan_city_scroll,
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stVerticalBlock"],
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stElementContainer"],
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"],
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] > div {
      width:100%!important;max-width:100%!important;min-width:0!important;
      align-self:stretch!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stVerticalBlock"]{
      gap:2px!important;row-gap:2px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stElementContainer"]{
      margin:0!important;padding:0!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label{
      width:100%!important;min-width:0!important;max-width:100%!important;
      justify-content:flex-start!important;box-sizing:border-box!important;
      border-radius:13px!important;padding:5px 8px!important;
      min-height:32px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label > div {
      min-width:0!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label p{
      white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;
      font-size:11px!important;
    }
    /* Em algumas versões do Streamlit o checkbox nativo é um quadrado
       interno: arredondar o elemento real, mantendo o check laranja. */
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:first-child,
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] [role="checkbox"]{
      border-radius:50%!important;width:17px!important;height:17px!important;
      flex:0 0 17px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] [data-baseweb="checkbox"]:has(input:checked) > div:first-child{
      background:#EE5325!important;border-color:#EE5325!important;
    }
    /* Municípios: linhas largas, alinhadas e com seleção legível. */
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"]{
      display:block!important;width:100%!important;
      margin:2px 0!important;padding:0!important;border:0!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label{
      display:flex!important;align-items:center!important;gap:9px!important;
      width:100%!important;max-width:100%!important;
      border:1px solid #345c7b!important;background:#1b405f!important;
      border-radius:13px!important;min-height:35px!important;
      padding:6px 10px!important;box-sizing:border-box!important;
      cursor:pointer!important;transition:background .15s,border-color .15s!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label:hover{
      background:#244e70!important;border-color:#4c7b9b!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label p{
      font-size:12px!important;line-height:1.35!important;
      color:#dbe9f4!important;white-space:normal!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] [role="checkbox"]{
      width:17px!important;height:17px!important;flex-shrink:0!important;
      border-radius:50%!important;border:1px solid #416785!important;
      background:transparent!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"]{
      background:#EE5325!important;border-color:#EE5325!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] svg{
      color:#fff!important;fill:none!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_filter_panel [data-testid="stButton"] button[kind="primary"]{
      background:#EE5325!important;border-color:#EE5325!important;
      color:white!important;border-radius:10px!important;min-height:39px!important;
    }

    /* Indicador de seleção circular: substitui visual nativo quadrado.
       O checkbox continua sendo o widget acessível do Streamlit. */
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label {
      position:relative!important;display:flex!important;align-items:center!important;
      justify-content:flex-start!important;gap:0!important;
      padding:5px 10px 5px 32px!important;width:100%!important;
      min-height:32px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label::before {
      content:""!important;position:absolute!important;left:9px!important;
      top:50%!important;transform:translateY(-50%)!important;
      width:17px!important;height:17px!important;
      border-radius:50%!important;border:1px solid #416785!important;
      background:transparent!important;display:grid!important;place-items:center!important;
      color:#fff!important;font:700 12px/1 Arial,sans-serif!important;
      box-sizing:border-box!important;pointer-events:none!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label:has(input:checked)::before,
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label:has([aria-checked="true"])::before {
      content:"✓"!important;background:#EE5325!important;border-color:#EE5325!important;
    }
    /* Oculta somente o desenho quadrado do BaseWeb, preservando input e rótulo. */
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label > span:first-child,
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label > div:first-child:has(input),
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] [data-baseweb="checkbox"] > span:first-child {
      position:absolute!important;left:0!important;top:0!important;
      width:1px!important;height:1px!important;opacity:0!important;
      overflow:hidden!important;pointer-events:none!important;
    }
    /* Remove o quadrado branco real do Streamlit/BaseWeb, sem esconder o texto.
       O ::before do label é o único marcador visual. */
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label > div:first-child:not(:has(p)),
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label > span:first-child,
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label [role="checkbox"],
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label input[type="checkbox"] ~ div,
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label input[type="checkbox"] ~ span {
      opacity:0!important;visibility:hidden!important;
      position:absolute!important;width:1px!important;height:1px!important;
      min-width:0!important;min-height:0!important;padding:0!important;
      margin:0!important;border:0!important;pointer-events:none!important;
      overflow:hidden!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label > div:has(p){
      margin:0!important;padding:0!important;flex:1 1 auto!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stCheckbox"] label:focus-within {
      outline:2px solid #54a4d5!important;outline-offset:1px!important;
    }

    /* Oculta apenas o chevron nativo do expander: + / − já indicam o estado. */
    [data-testid="stSidebar"] .st-key-siscan_year_panel summary [data-testid="stExpanderToggleIcon"],
    [data-testid="stSidebar"] .st-key-siscan_city_panel summary [data-testid="stExpanderToggleIcon"],
    [data-testid="stSidebar"] .st-key-siscan_year_panel summary > svg:first-child,
    [data-testid="stSidebar"] .st-key-siscan_city_panel summary > svg:first-child,
    [data-testid="stSidebar"] .st-key-siscan_year_panel summary > span:first-child:has(svg),
    [data-testid="stSidebar"] .st-key-siscan_city_panel summary > span:first-child:has(svg) {
      display:none!important;width:0!important;min-width:0!important;
      margin:0!important;padding:0!important;
    }

    /* Opções de municípios agora são botões, sem nenhum checkbox quadrado. */
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"]{
      width:100%!important;margin:1px 0!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button{
      display:flex!important;align-items:center!important;justify-content:flex-start!important;
      text-align:left!important;gap:9px!important;width:100%!important;
      min-height:31px!important;margin:0!important;padding:5px 9px!important;
      background:#1b405f!important;color:#dce9f3!important;
      border:1px solid #345b79!important;border-radius:13px!important;
      font:500 12px/1.3 Manrope,Arial,sans-serif!important;
      box-shadow:none!important;transition:background .15s,border-color .15s!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button::before{
      content:""!important;display:grid!important;place-items:center!important;
      flex:0 0 17px!important;width:17px!important;height:17px!important;
      border:1px solid #416785!important;border-radius:50%!important;
      background:transparent!important;color:white!important;
      font:700 11px/1 Arial,sans-serif!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button[kind="primary"],
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button[data-testid="stBaseButton-primary"]{
      background:#1b405f!important;color:#fff!important;
      border-color:#3b6684!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button[kind="primary"]::before,
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button[data-testid="stBaseButton-primary"]::before{
      content:"✓"!important;background:#EE5325!important;border-color:#EE5325!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button:hover{
      background:#254e6e!important;border-color:#537e9b!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button:focus-visible{
      outline:2px solid #5aaee0!important;outline-offset:1px!important;
    }

    /* Nome do município alinhado imediatamente após o círculo de seleção. */
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button {
      justify-content:flex-start!important;
      text-align:left!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button p,
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button span {
      text-align:left!important;
      margin-left:0!important;
      margin-right:0!important;
      width:auto!important;
      flex:0 1 auto!important;
    }

    /* Marcador e nome com posições fixas: evita centralização do texto pelo Streamlit. */
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button{
      position:relative!important;display:flex!important;
      justify-content:flex-start!important;align-items:center!important;
      text-align:left!important;padding:5px 8px 5px 36px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button::before{
      position:absolute!important;left:9px!important;top:50%!important;
      transform:translateY(-50%)!important;margin:0!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button [data-testid="stMarkdownContainer"]{
      position:absolute!important;left:36px!important;right:8px!important;
      top:50%!important;transform:translateY(-50%)!important;
      display:block!important;width:auto!important;max-width:none!important;
      margin:0!important;padding:0!important;text-align:left!important;
      flex:none!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_scroll [data-testid="stButton"] button [data-testid="stMarkdownContainer"] p{
      margin:0!important;padding:0!important;text-align:left!important;
      white-space:nowrap!important;overflow:hidden!important;
      text-overflow:ellipsis!important;
    }

    /* Cabeçalhos de filtros: ocultar a seta nativa em ambos os estados.
       Os ícones de calendário/localização ficam fixos via SVG, sem duplicação. */
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary svg,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary svg,
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stExpanderToggleIcon"],
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stExpanderToggleIcon"],
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stIconMaterial"],
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stIconMaterial"]{
      display:none!important;visibility:hidden!important;width:0!important;
      min-width:0!important;margin:0!important;padding:0!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stMarkdownContainer"]::before,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stMarkdownContainer"]::before{
      content:""!important;position:absolute!important;
      display:block!important;left:33px!important;top:50%!important;
      transform:translateY(-50%)!important;width:15px!important;height:15px!important;
      background-size:contain!important;background-position:center!important;
      background-repeat:no-repeat!important;pointer-events:none!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stMarkdownContainer"]::before{
      background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2354a4d5' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='5' width='18' height='16' rx='2'/%3E%3Cpath d='M7 3v4M17 3v4M3 10h18'/%3E%3C/svg%3E")!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stMarkdownContainer"]::before{
      background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2354a4d5' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 0 1 16 0Z'/%3E%3Ccircle cx='12' cy='10' r='2.5'/%3E%3C/svg%3E")!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary{
      padding-left:57px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details:not([open])>summary [data-testid="stMarkdownContainer"]::after,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details:not([open])>summary [data-testid="stMarkdownContainer"]::after{
      left:57px!important;
    }

    /* Cabeçalhos compactos: + | ícone | título/subtítulo | contador.
       Mesmas dimensões nos dois filtros e sem a seta nativa. */
    [data-testid="stSidebar"] .st-key-siscan_filter_panel{
      padding:10px 9px 11px!important;border-radius:20px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel,
    [data-testid="stSidebar"] .st-key-siscan_city_panel{
      margin:0 0 6px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary{
      height:51px!important;min-height:51px!important;
      padding:0 52px 0 49px!important;align-items:center!important;
      border-radius:16px!important;line-height:1!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details:not([open])>summary,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details:not([open])>summary{
      height:55px!important;min-height:55px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stMarkdownContainer"]{
      display:block!important;position:static!important;
      width:auto!important;min-width:0!important;max-width:100%!important;
      margin:0!important;padding:0!important;align-self:center!important;
      line-height:1!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stMarkdownContainer"] p{
      margin:0!important;padding:0!important;
      color:#f5f9fd!important;font:650 12px/1.2 Manrope,Arial,sans-serif!important;
      text-align:left!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details:not([open])>summary [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details:not([open])>summary [data-testid="stMarkdownContainer"] p{
      transform:translateY(-6px)!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details:not([open])>summary [data-testid="stMarkdownContainer"]::after,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details:not([open])>summary [data-testid="stMarkdownContainer"]::after{
      top:32px!important;left:49px!important;
      max-width:calc(100% - 110px)!important;
      line-height:1.25!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary::before,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary::before{
      left:10px!important;width:19px!important;height:19px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stMarkdownContainer"]::before,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stMarkdownContainer"]::before{
      left:34px!important;top:50%!important;
      width:14px!important;height:14px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary::after,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary::after{
      right:10px!important;padding:4px 8px!important;
      background:#1b405f!important;border:1px solid #315977!important;
    }

    /* Estrutura definitiva do cabeçalho compacto: ícones e texto posicionados
       em coordenadas próprias, sem os deslocamentos dos wrappers do Streamlit. */
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary {
      position:relative!important;display:block!important;
      box-sizing:border-box!important;
      padding:0!important;margin:0!important;height:48px!important;
      min-height:48px!important;
      background:#1b405f!important;border:0!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details:not([open])>summary,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details:not([open])>summary{
      height:56px!important;min-height:56px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary::before,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary::before{
      left:11px!important;top:50%!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stMarkdownContainer"]{
      display:contents!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stMarkdownContainer"] p{
      position:absolute!important;top:50%!important;left:59px!important;
      transform:translateY(-50%)!important;
      margin:0!important;padding:0!important;
      width:calc(100% - 118px)!important;
      color:#f3f8fc!important;font:400 13px/1.1 Georgia,serif!important;
      letter-spacing:0!important;text-align:left!important;
      white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details:not([open])>summary [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details:not([open])>summary [data-testid="stMarkdownContainer"] p{
      top:20px!important;transform:none!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary [data-testid="stMarkdownContainer"]::before,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary [data-testid="stMarkdownContainer"]::before{
      left:36px!important;top:50%!important;width:14px!important;height:14px!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details:not([open])>summary [data-testid="stMarkdownContainer"]::after,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details:not([open])>summary [data-testid="stMarkdownContainer"]::after{
      position:absolute!important;left:59px!important;top:35px!important;
      display:block!important;width:calc(100% - 119px)!important;
      max-width:none!important;
      font:400 10px/1.1 Manrope,Arial,sans-serif!important;
      color:#8aaac1!important;
      overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;
    }
    [data-testid="stSidebar"] .st-key-siscan_year_panel details>summary::after,
    [data-testid="stSidebar"] .st-key-siscan_city_panel details>summary::after{
      top:50%!important;right:10px!important;
    }

    /* Ícones Lucide-style correspondentes à referência do menu lateral. */
    [data-testid="stSidebar"] .st-key-nav_panorama_icon [data-testid="stPageLink"] a,
    [data-testid="stSidebar"] .st-key-nav_outubro_icon [data-testid="stPageLink"] a,
    [data-testid="stSidebar"] .st-key-nav_exames_icon [data-testid="stPageLink"] a{
      display:flex!important;align-items:center!important;
      gap:10px!important;min-height:39px!important;
    }
    [data-testid="stSidebar"] .st-key-nav_panorama_icon [data-testid="stPageLink"] a::before,
    [data-testid="stSidebar"] .st-key-nav_outubro_icon [data-testid="stPageLink"] a::before,
    [data-testid="stSidebar"] .st-key-nav_exames_icon [data-testid="stPageLink"] a::before{
      content:""!important;display:inline-block!important;
      flex:0 0 17px!important;width:17px!important;height:17px!important;
      background-color:currentColor!important;
      -webkit-mask-size:contain!important;mask-size:contain!important;
      -webkit-mask-position:center!important;mask-position:center!important;
      -webkit-mask-repeat:no-repeat!important;mask-repeat:no-repeat!important;
    }
    [data-testid="stSidebar"] .st-key-nav_panorama_icon [data-testid="stPageLink"] a::before{
      -webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M3%203v18h18%22%2F%3E%3Cpath%20d%3D%22M8%2016v-5M13%2016V7M18%2016v-9%22%2F%3E%3C%2Fsvg%3E")!important;
      mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M3%203v18h18%22%2F%3E%3Cpath%20d%3D%22M8%2016v-5M13%2016V7M18%2016v-9%22%2F%3E%3C%2Fsvg%3E")!important;
    }
    [data-testid="stSidebar"] .st-key-nav_outubro_icon [data-testid="stPageLink"] a::before{
      -webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.7%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M12%203c-3.5%200-6%202.2-6%205.4%200%202.5%202%205.2%206%209.2%204-4%206-6.7%206-9.2C18%205.2%2015.5%203%2012%203Z%22%2F%3E%3Cpath%20d%3D%22M9.4%205.6c-1%202.9%202%206.7%204.9%209.1M14.6%205.6c1%202.9-2%206.7-4.9%209.1%22%2F%3E%3Cpath%20d%3D%22M10.4%2014.2%207.6%2021l4.4-2.5L16.4%2021l-2.8-6.8%22%2F%3E%3C%2Fsvg%3E")!important;
      mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.7%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M12%203c-3.5%200-6%202.2-6%205.4%200%202.5%202%205.2%206%209.2%204-4%206-6.7%206-9.2C18%205.2%2015.5%203%2012%203Z%22%2F%3E%3Cpath%20d%3D%22M9.4%205.6c-1%202.9%202%206.7%204.9%209.1M14.6%205.6c1%202.9-2%206.7-4.9%209.1%22%2F%3E%3Cpath%20d%3D%22M10.4%2014.2%207.6%2021l4.4-2.5L16.4%2021l-2.8-6.8%22%2F%3E%3C%2Fsvg%3E")!important;
    }
    [data-testid="stSidebar"] .st-key-nav_exames_icon [data-testid="stPageLink"] a::before{
      -webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M2%2012h4l3-7%204.3%2014%203.1-7H22%22%2F%3E%3C%2Fsvg%3E")!important;
      mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M2%2012h4l3-7%204.3%2014%203.1-7H22%22%2F%3E%3C%2Fsvg%3E")!important;
    }

    /* Responsividade real: telefones 320–480px, tablets e desktop.
       Isola a rolagem horizontal de tabelas, sem alargar a página inteira. */
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
      max-width:100%; min-width:0;
    }
    [data-testid="stMain"] {overflow-x:clip;}
    [data-testid="stMainBlockContainer"] {
      box-sizing:border-box!important;
      width:100%!important;
      min-width:0!important;
      max-width:1480px!important;
    }
    [data-testid="stMain"] [data-testid="stVerticalBlock"],
    [data-testid="stMain"] [data-testid="stElementContainer"],
    [data-testid="stMain"] [data-testid="stColumn"],
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
      min-width:0!important;max-width:100%;
    }
    [data-testid="stMain"] [data-testid="stPlotlyChart"],
    [data-testid="stMain"] [data-testid="stPlotlyChart"] > div,
    [data-testid="stMain"] [data-testid="stIFrame"],
    [data-testid="stMain"] iframe,
    [data-testid="stMain"] [data-testid="stDataFrame"] {
      max-width:100%!important;min-width:0!important;
    }
    .pet-table-scroller, .q3-table-scroller {
      width:100%!important;max-width:100%!important;
      overflow-x:auto!important;-webkit-overflow-scrolling:touch;
    }
    .pet-hero, .exec-hero, .exec-card, .exec-metric,
    .st-key-exec-nav-panorama, .st-key-exec-nav-outubro,
    .st-key-exec-nav-alterados {max-width:100%;min-width:0;}
    .pet-hero-title, .exec-title, .exec-card-title, h1, h2, h3 {
      overflow-wrap:anywhere;
    }
    @media (max-width:768px) {
      [data-testid="stMainBlockContainer"], .block-container {
        padding:0.9rem 0.9rem 2.5rem!important;
      }
      [data-testid="stSidebar"][aria-expanded="true"] {
        width:min(300px,86vw)!important;
        min-width:0!important;max-width:86vw!important;
      }
      [data-testid="stHorizontalBlock"] {
        flex-wrap:wrap!important;gap:0.75rem!important;
      }
      [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex:1 1 calc(50% - 0.75rem)!important;
        width:auto!important;min-width:0!important;
      }
      [data-testid="stMain"] [data-testid="stMetric"] {
        min-height:105px!important;padding:14px!important;
      }
      [data-testid="stMain"] [data-testid="stMetricValue"] {
        font-size:clamp(1.25rem,4vw,1.7rem)!important;
      }
      [data-testid="stMain"] [data-testid="stPlotlyChart"] {overflow:hidden;}
      [data-testid="stMain"] .pet-active-scope {flex-wrap:wrap!important;}
    }
    @media (max-width:480px) {
      [data-testid="stMainBlockContainer"], .block-container {
        padding:0.75rem 0.65rem 2rem!important;
      }
      [data-testid="stHorizontalBlock"] {gap:0.7rem!important;}
      [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex:1 1 100%!important;width:100%!important;
        max-width:100%!important;min-width:0!important;
      }
      [data-testid="stMain"] [data-testid="stMetric"] {
        min-height:0!important;padding:13px 14px!important;
      }
      .pet-hero {padding:19px 16px 27px!important;margin-bottom:0!important;}
      .pet-hero-title, .exec-title {
        font-size:clamp(1.45rem,6.2vw,1.9rem)!important;
        line-height:1.18!important;
      }
      .pet-hero-desc {font-size:0.83rem!important;}
      .pet-active-scope {gap:6px!important;}
      .pet-scope-chip {
        font-size:.7rem!important;padding:6px 9px!important;
        white-space:normal!important;overflow-wrap:anywhere!important;
      }
      .pet-table-scroller th, .pet-table-scroller td {
        padding:9px 8px!important;font-size:.75rem!important;
      }
      [data-testid="stMain"] .stDownloadButton button,
      [data-testid="stMain"] .stButton button {
        max-width:100%;white-space:normal;
      }
      .st-key-exec-nav-panorama,
      .st-key-exec-nav-outubro,
      .st-key-exec-nav-alterados {
        padding:14px!important;min-height:75px!important;
      }
    }
    </style>""", unsafe_allow_html=True)


def active_scope_html():
    """Chips compactos do recorte aplicado, sincronizados com os filtros globais."""
    from utils.data_loader import MUNICIPIOS, selected_years, years_label

    years = selected_years()
    selected_cities = st.session_state.get("city_preference", list(MUNICIPIOS.values()))
    count = len(selected_cities)
    period = years_label(years)
    city_text = "Todos os 11 municípios" if count == len(MUNICIPIOS) else f"{count} de 11 municípios"

    return (
        '<div class="pet-active-scope" role="status" aria-label="Recorte ativo">'
        '<span class="pet-scope-label">RECORTE ATIVO</span>'
        '<span class="pet-scope-chip"><span class="pet-scope-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18M7 14h2M12 14h2M17 14h0M7 18h2M12 18h2"/></svg></span>'
        + html.escape(period) + '</span>'
        '<span class="pet-scope-chip"><span class="pet-scope-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg></span>'
        + html.escape(city_text) + '</span>'
        '</div>'
    )


def page_header(kicker, title, description=""):
    """Cabeçalho comum com indicadores do recorte ativo em todas as páginas."""
    description_html = (
        '<div class="pet-hero-desc">' + html.escape(str(description)) + '</div>'
        if description else ""
    )
    st.markdown(
        '<header class="pet-hero"><p class="pet-hero-kicker">'
        + html.escape(str(kicker)) + '</p><h1 class="pet-hero-title">'
        + html.escape(str(title)) + '</h1>' + description_html
        + active_scope_html() + '</header>',
        unsafe_allow_html=True,
    )


def note(message, highlight=False):
    css = "pet-highlight" if highlight else "pet-note"
    st.markdown(f'<div class="{css}">{html.escape(str(message))}</div>', unsafe_allow_html=True)


def style_chart(fig, height=430, percent=False):
    fig.update_layout(
        template="plotly_white", font=dict(family="Arial", color=NAVY),
        colorway=PALETTE,
        margin=dict(l=15,r=15,t=30,b=20), height=height,
        hoverlabel=dict(bgcolor="white",font_color=NAVY),
        legend_title_text="", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e9edf1")
    return fig

def format_percent_chart(fig, axis="y"):
    """Formata percentuais nos eixos e no tooltip sem arredondar os cálculos."""
    if axis == "y":
        fig.update_yaxes(tickformat=".2f", ticksuffix="%")
        fig.update_traces(hovertemplate="%{x}<br>%{y:.2f}%<extra>%{fullData.name}</extra>")
    elif axis == "x":
        fig.update_xaxes(tickformat=".2f", ticksuffix="%")
        fig.update_traces(hovertemplate="%{y}<br>%{x:.2f}%<extra>%{fullData.name}</extra>")
    return fig

def display_chart(fig, filename="grafico_siscan.png"):
    """Exibe gráfico interativo com exportação PNG pelo botão direito."""
    from utils.chart_download import chart_with_right_click_download
    styled = style_chart(fig)
    chart_with_right_click_download(
        styled, filename=filename, height=styled.layout.height,
    )

def metric_row(items):
    cols = st.columns(len(items))
    for col, (label,value) in zip(cols,items):
        col.metric(label,value)


def display_table(df, *, percent_columns=None, integer_columns=None, large=False, consolidated_style=False):
    """Tabela PET-Saúde: HTML acessível e responsivo, sem alterar os dados."""
    percent_columns = set(percent_columns or [])
    integer_columns = set(integer_columns or [])
    css = """
    <style>
    .pet-table-scroller{width:100%;overflow-x:auto;border-radius:8px;
      box-shadow:0 2px 7px rgba(26,59,92,.09);margin:12px 0 17px}
    table.pet-table{border-collapse:collapse;width:100%;background:#fff;color:#1A3B5C;
      font:500 .83rem Manrope,Arial,sans-serif}
    .pet-table th{background:#1A3B5C;color:#fff;padding:13px 12px;text-align:left;
      font-size:.76rem;line-height:1.35;font-weight:750;white-space:normal}
    .pet-table td{padding:13px 12px;border-bottom:1px solid #e7ebef;white-space:nowrap}
    /* Variante ampliada, ativada somente nas tabelas que precisam de mais leitura. */
    table.pet-table.pet-table-large{
      min-width:1130px;font-size:1.03rem;line-height:1.5}
    .pet-table.pet-table-large th{
      font-size:.94rem;line-height:1.45;padding:17px 16px;
      min-width:125px;vertical-align:middle}
    .pet-table.pet-table-large th:first-child{min-width:165px}
    .pet-table.pet-table-large td{
      font-size:1.02rem;padding:17px 16px;line-height:1.45}
    .pet-table.pet-table-large th:not(:first-child),
    .pet-table.pet-table-large td:not(:first-child){
      text-align:center}
    .pet-table.pet-table-large th:first-child,
    .pet-table.pet-table-large td:first-child{
      text-align:left}
    /* Destaques exclusivos da tabela consolidada Q3. */
    .pet-table.pet-table-consolidated .pet-deficit{
      color:#C24A20;font-weight:750}
    .pet-table.pet-table-consolidated .pet-attainment{
      display:inline-block;padding:5px 10px;border-radius:6px;
      font-weight:700;white-space:nowrap}
    .pet-table.pet-table-consolidated .pet-attainment-critical{
      color:#A33B15;background:#FDE9DD}
    .pet-table.pet-table-consolidated .pet-attainment-low{
      color:#245577;background:#E9F2FA}
    .pet-table.pet-table-consolidated tr.pet-region-total,
    .pet-table.pet-table-consolidated tr.pet-region-total:hover{
      background:#DDEAF3}
    .pet-table.pet-table-consolidated tr.pet-region-total td{
      border-top:2px solid #1A3B5C;
      border-bottom:2px solid #AFC7D8;
      font-weight:800}
    .pet-table tbody tr:nth-child(even){background:#f6f8fa}
    .pet-table tbody tr:hover{background:#ecf5fa}
    .pet-table td:first-child{font-weight:700}
    .pet-table .pet-badge{display:inline-block;border-radius:5px;padding:5px 9px;
      font-size:.76rem;font-weight:750;white-space:normal}
    .pet-badge.ok{color:#385723;background:#e2f0d9}
    .pet-badge.low{color:#856404;background:#fff3cd}
    .pet-badge.bad{color:#b72323;background:#ffe6e6}
    .pet-badge.unknown{color:#4a5968;background:#e9edf1}
    </style>
    """
    def br_number(value, decimals):
        return f"{value:,.{decimals}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    def cell(value, column):
        if pd.isna(value):
            return "N/D"
        if isinstance(value, (bool,)):
            return "Sim" if value else "Não"
        if consolidated_style and column == "Atingimento da referência (%)" and isinstance(value, (int, float)):
            classe = ("pet-attainment-critical" if value < 15
                      else "pet-attainment-low" if value < 40 else "")
            return '<span class="pet-attainment ' + classe + '">' + br_number(value, 2) + '%</span>'
        if consolidated_style and column == "Diferença anual média de exames" and isinstance(value, (int, float)):
            valor = br_number(value, 0)
            return '<span class="pet-deficit">' + valor + '</span>' if value < 0 else valor
        if column in percent_columns and isinstance(value, (int, float)):
            return br_number(value, 2) + "%"
        if column in integer_columns and isinstance(value, (int, float)):
            return br_number(value, 0)
        if isinstance(value, (int, float)):
            return br_number(value, 2 if isinstance(value, float) and not value.is_integer() else 0)
        content = html.escape(str(value))
        if column.lower().startswith(("classificação", "classificacao", "alerta")):
            mode = "unknown"
            if "🟢" in content or "boa" in content.lower(): mode = "ok"
            elif "🟡" in content or "baixo" in content.lower(): mode = "low"
            elif "🔴" in content or "alto" in content.lower(): mode = "bad"
            return '<span class="pet-badge ' + mode + '">' + content + '</span>'
        return content
    header = "".join("<th scope='col'>" + html.escape(str(c)) + "</th>" for c in df.columns)
    rows = []
    for values in df.itertuples(index=False, name=None):
        is_total = consolidated_style and str(values[0]).startswith("TOTAL")
        classe_linha = ' class="pet-region-total"' if is_total else ""
        rows.append("<tr" + classe_linha + ">" + "".join(
            "<td>" + cell(v, c) + "</td>" for c, v in zip(df.columns, values)
        ) + "</tr>")
    if not rows:
        rows = ['<tr><td colspan="' + str(max(1,len(df.columns))) + '">Nenhum registro.</td></tr>']
    table_class = "pet-table pet-table-large" if large else "pet-table"
    if consolidated_style:
        table_class += " pet-table-consolidated"
    markup = ('<div class="pet-table-scroller" role="region" aria-label="Tabela de dados" tabindex="0">'
              '<table class="' + table_class + '"><thead><tr>' + header + '</tr></thead><tbody>'
              + "".join(rows) + '</tbody></table></div>')
    st.markdown(css + markup, unsafe_allow_html=True)


def export_table(df, name):
    """Exibe tabela estilizada, mantendo exportação dos dados originais."""
    from pandas.api.types import is_numeric_dtype
    percentage = [
        c for c in df.columns if is_numeric_dtype(df[c]) and
        (c.lower() in {"percentual", "taxa", "variacao_pct"} or
         c.lower().endswith(("_pct", "_percentual", "_percentual_pct")) or
         c.lower().startswith(("taxa_", "proporcao_")))
    ]
    display_table(df, percent_columns=percentage)
    st.download_button("⬇️ Exportar CSV", df.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       file_name=name, mime="text/csv", key="csv_" + name)

def fmt_num(v):
    return f"{int(v):,}".replace(",", ".")

def fmt_pct(v):
    if v is None or v != v: return "N/D"
    return f"{v:.2f}%".replace(".", ",")

def pct(n, d):
    return 100*n/d if d and d > 0 else float("nan")
