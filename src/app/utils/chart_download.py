"""Gráfico Plotly com menu contextual de exportação PNG."""
import json
from plotly.utils import PlotlyJSONEncoder
import streamlit.components.v1 as components


def chart_with_right_click_download(fig, *, filename, height=None, export_fig=None):
    """Exibe Plotly interativo: botão direito abre a opção de baixar PNG."""
    height = int(height if height is not None else (fig.layout.height or 430))
    name = filename.removesuffix(".png")
    export_spec = json.dumps((export_fig or fig).to_plotly_json(), cls=PlotlyJSONEncoder)
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
const exportSpec=__EXPORT_SPEC__;
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
  if(!window.Plotly)return;
  const temp=document.createElement("div");
  temp.style.cssText="position:absolute;left:-20000px;top:0;width:1500px;height:720px;pointer-events:none";
  document.body.appendChild(temp);
  try{
    const layout={...exportSpec.layout,width:1500,height:720,autosize:false,
      paper_bgcolor:"#ffffff",plot_bgcolor:"#ffffff",
      font:{...exportSpec.layout.font,color:"#1A3B5C"},
      margin:{l:100,r:185,t:95,b:90,...exportSpec.layout.margin}};
    await Plotly.newPlot(temp,exportSpec.data,layout,{staticPlot:true,displayModeBar:false,responsive:false});
    await Plotly.downloadImage(temp,{format:"png",filename:filename,scale:2,width:1500,height:720});
  }catch(err){
    console.error("Falha ao exportar imagem:",err);
    const chart=wrap.querySelector(".js-plotly-plot");
    if(chart) await Plotly.downloadImage(chart,{format:"png",filename:filename,scale:2});
  }finally{
    Plotly.purge(temp);
    temp.remove();
  }
});
document.addEventListener("click",e=>{if(!menu.contains(e.target))close()});
document.addEventListener("keydown",e=>{if(e.key==="Escape")close()});
})();
</script></body></html>"""
    html = (html.replace("__FIGURE__", figure)
            .replace("__FILENAME__", json.dumps(name))
            .replace("__EXPORT_SPEC__", export_spec))
    components.html(html, height=height + 12, scrolling=False)
