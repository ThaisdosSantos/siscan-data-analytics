"""Gráfico Plotly com menu contextual de exportação PNG."""
import json
import streamlit.components.v1 as components


def chart_with_right_click_download(fig, *, filename, height=None):
    """Exibe Plotly interativo: botão direito abre a opção de baixar PNG."""
    height = int(height if height is not None else (fig.layout.height or 430))
    name = filename.removesuffix(".png")
    figure = fig.to_html(
        full_html=False, include_plotlyjs="cdn",
        config={"responsive": True, "displayModeBar": True, "displaylogo": False,
                "toImageButtonOptions": {"format": "png", "filename": name, "scale": 2}},
        default_width="100%", default_height=str(height) + "px",
    )
    html = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<style>
html,body{margin:0;background:transparent;font-family:Arial,sans-serif}
#wrap{position:relative;width:100%}
#menu{display:none;position:absolute;z-index:1000;border:1px solid #cbd9e4;
border-radius:8px;padding:5px;background:white;box-shadow:0 7px 20px #1a3b5c33}
#menu button{cursor:pointer;border:0;border-radius:5px;background:white;
color:#1A3B5C;padding:10px 12px;font-size:13px}
#menu button:hover,#menu button:focus-visible{background:#e8f3f9;outline:2px solid #006C9A}
</style></head><body><div id="wrap">
__FIGURE__
<div id="menu" role="menu" aria-label="Exportar gráfico">
<button type="button" role="menuitem" id="save">⬇ Baixar imagem PNG</button>
</div></div>
<script>
(function(){
const wrap=document.getElementById("wrap"),menu=document.getElementById("menu");
const button=document.getElementById("save"),filename=__FILENAME__;
const close=()=>{menu.style.display="none"};
wrap.addEventListener("contextmenu",event=>{
  if(!event.target.closest(".js-plotly-plot"))return;
  event.preventDefault();
  const rect=wrap.getBoundingClientRect();menu.style.display="block";
  menu.style.left=Math.max(0,Math.min(event.clientX-rect.left,rect.width-menu.offsetWidth))+"px";
  menu.style.top=Math.max(0,Math.min(event.clientY-rect.top,rect.height-menu.offsetHeight))+"px";
  button.focus();
});
button.addEventListener("click",async()=>{
  close();
  const chart=wrap.querySelector(".js-plotly-plot");
  if(chart&&window.Plotly)await Plotly.downloadImage(chart,{format:"png",filename:filename,scale:2});
});
document.addEventListener("click",e=>{if(!menu.contains(e.target))close()});
document.addEventListener("keydown",e=>{if(e.key==="Escape")close()});
})();
</script></body></html>"""
    html = html.replace("__FIGURE__", figure).replace("__FILENAME__", json.dumps(name))
    components.html(html, height=height + 12, scrolling=False)
