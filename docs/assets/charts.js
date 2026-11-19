document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Plotly) return;
  for (const id of ['evolucao','distribuicao','ranking','convergencia']) {
    const el = document.getElementById(id); if (!el) continue;
    try {const r = await fetch('assets/'+id+'.json'); if(!r.ok) throw new Error('JSON indisponível');
      const fig=await r.json(); await Plotly.newPlot(el, fig.data, fig.layout, {responsive:true,displaylogo:false});}
    catch(err) {console.warn('Mostrando figura estática para',id,err);}
  }
});
