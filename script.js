const API = "http://127.0.0.1:5000";
const $ = id => document.getElementById(id);

$("location_score").addEventListener("input", e => $("locationValue").textContent = e.target.value);

async function checkAPI(){
  try{
    const r = await fetch(`${API}/api/health`);
    if(!r.ok) throw new Error();
    $("apiStatus").textContent = "● API Connected";
    $("apiStatus").style.color = "#35794d";
  }catch{
    $("apiStatus").textContent = "● Start Flask backend";
    $("apiStatus").style.color = "#b36b2c";
  }
}

async function loadMetrics(){
  try{
    const r = await fetch(`${API}/api/metrics`);
    const m = await r.json();
    const vals = [m.mae, m.mse, m.rmse, m.r2];
    document.querySelectorAll(".metric b").forEach((el,i)=>el.textContent=vals[i]);
  }catch{}
}

$("predictionForm").addEventListener("submit", async e=>{
  e.preventDefault();
  const btn = $("predictBtn");
  btn.disabled = true; btn.textContent = "Predicting...";
  $("errorBox").classList.add("hidden");

  const payload = {
    area_sqft: Number($("area_sqft").value),
    bedrooms: Number($("bedrooms").value),
    bathrooms: Number($("bathrooms").value),
    age_years: Number($("age_years").value),
    location_score: Number($("location_score").value),
    parking: Number($("parking").value)
  };

  try{
    const r = await fetch(`${API}/api/predict`, {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload)
    });
    const data = await r.json();
    if(!r.ok) throw new Error(data.error || "Prediction failed");
    $("price").textContent = "₹" + Number(data.predicted_price_inr).toLocaleString("en-IN");
    $("priceLakh").textContent = `${data.predicted_price_lakh} lakh`;
    $("resultEmpty").classList.add("hidden");
    $("resultReady").classList.remove("hidden");
  }catch(err){
    $("errorBox").textContent = err.message + " — Make sure the Flask server is running.";
    $("errorBox").classList.remove("hidden");
  }finally{
    btn.disabled = false; btn.textContent = "Predict House Price";
  }
});

$("againBtn").addEventListener("click", ()=>{
  $("resultReady").classList.add("hidden");
  $("resultEmpty").classList.remove("hidden");
  document.querySelector("#predict").scrollIntoView({behavior:"smooth"});
});

$("retrainBtn").addEventListener("click", async ()=>{
  const btn = $("retrainBtn"); btn.disabled = true; btn.textContent = "Retraining...";
  try{
    await fetch(`${API}/api/retrain`, {method:"POST"});
    await loadMetrics();
    btn.textContent = "Model Retrained ✓";
    setTimeout(()=>btn.textContent="Retrain Model",1800);
  }catch{ btn.textContent="Backend Offline"; }
  btn.disabled=false;
});

checkAPI(); loadMetrics();
