import React, {useState, useEffect, useRef} from "react";
import axios from "axios";
import { strings } from "../i18n";

/**
 * Chatbot component:
 * - Proactively starts the conversation by asking for location and crop.
 * - Gathers farmer inputs, requests /api/fact-bundle and /api/chat.
 * - Displays Gemini response (raw) and a compact actionable card.
 */
export default function Chatbot({ lang="en" }){
  const s = strings[lang];
  const [latlon, setLatlon] = useState("");
  const [village, setVillage] = useState("");
  const [commodity, setCommodity] = useState("wheat");
  const [district, setDistrict] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [bundle, setBundle] = useState(null);
  const [userMsg, setUserMsg] = useState("");
  const chatRef = useRef();

  useEffect(()=>{
    // Proactively greet & ask for location if empty
    if(messages.length===0){
      setMessages([{from:"bot", text: s.greet}]);
    }
  },[]);

  useEffect(()=>{ chatRef.current?.scrollIntoView({behavior:"smooth"}) }, [messages]);

  const gatherAndFetchBundle = async ()=>{
    // parse latlon if user provided "lat,lon"
    let lat=null, lon=null;
    if(latlon.includes(",")){
      const parts = latlon.split(",").map(p=>p.trim());
      lat = parseFloat(parts[0]); lon = parseFloat(parts[1]);
    } else {
      // try to geocode village? For MVP, ask the user to enter lat,lon
    }
    if(!lat || !lon){
      setMessages(m => [...m, {from:"bot", text: lang==="hi" ? "कृपया अक्षांश,देशांतर (lat,lon) दर्ज करें।" : "Please enter lat,lon coordinates."}]);
      return;
    }
    setLoading(true);
    const farmer_inputs = { commodity, district, village };
    try{
      const resp = await axios.post("/api/fact-bundle", { lat, lon, farmer_inputs });
      setBundle(resp.data);
      setMessages(m => [...m, {from:"bot", text: lang==="hi" ? "डेटा मिला — सलाह देता हूँ। अब प्रश्न पूछें या 'सिफारिश' टाइप करें।" : "Fact bundle compiled — you can ask a question or type 'recommend'."}]);
    }catch(e){
      setMessages(m => [...m, {from:"bot", text: "Failed to fetch data: " + (e.response?.data?.error || e.message)}]);
    }finally{
      setLoading(false);
    }
  };

  const askGemini = async (msg)=>{
    if(!bundle){
      setMessages(m => [...m, {from:"bot", text: lang==="hi" ? "पहले स्थान और फसल जानकारी दें।" : "Please provide location and crop first."}]);
      return;
    }
    setMessages(m => [...m, {from:"user", text: msg}]);
    setUserMsg("");
    setLoading(true);
    try{
      const lat = bundle.location.lat, lon = bundle.location.lon;
      const resp = await axios.post("/api/chat", {
        lat, lon, farmer_inputs: bundle.farmer_inputs, user_message: msg, lang
      });
      const gem = resp.data.gemini_raw;
      // Simplified: show the model's top text output if present
      const textOut = (gem?.candidates && gem.candidates[0] && gem.candidates[0].output) ? gem.candidates[0].output : JSON.stringify(gem);
      setMessages(m => [...m, {from:"bot", text: textOut}]);
    }catch(e){
      setMessages(m => [...m, {from:"bot", text: "Error contacting model: " + (e.response?.data?.error || e.message)}]);
    }finally{
      setLoading(false);
    }
  };

  return (
    <div style={{border:"1px solid #ddd", padding:12, borderRadius:8}}>
      <div style={{display:"flex", gap:8, marginBottom:8}}>
        <input value={village} onChange={e=>setVillage(e.target.value)} placeholder={s.enter_location} style={{flex:1}}/>
        <input value={latlon} onChange={e=>setLatlon(e.target.value)} placeholder="30.9000,75.8573 or leave blank" style={{width:220}} />
      </div>
      <div style={{display:"flex", gap:8, marginBottom:8}}>
        <input value={commodity} onChange={e=>setCommodity(e.target.value)} placeholder="Commodity (e.g., wheat)" />
        <input value={district} onChange={e=>setDistrict(e.target.value)} placeholder="District" />
        <button onClick={gatherAndFetchBundle} disabled={loading}>{loading ? "Working..." : s.submit}</button>
      </div>

      <div style={{minHeight:220, maxHeight:420, overflow:"auto", padding:8, background:"#fafafa", borderRadius:6}}>
        {messages.map((m,i)=>(
          <div key={i} style={{marginBottom:10}}>
            <div style={{fontSize:12, color:"#666"}}>{m.from}</div>
            <div style={{padding:8, borderRadius:6, background: m.from==="bot" ? "#fff" : "#e6f7ff"}}>{m.text}</div>
          </div>
        ))}
        <div ref={chatRef} />
      </div>

      <div style={{display:"flex", gap:8, marginTop:8}}>
        <input value={userMsg} onChange={e=>setUserMsg(e.target.value)} placeholder={s.chat_placeholder} style={{flex:1}} />
        <button onClick={()=>askGemini(userMsg || "Please give an actionable plan for my farm")} disabled={loading}>{loading ? "..." : s.start_chat}</button>
      </div>

      {bundle && (
        <details style={{marginTop:12}}>
          <summary>Fact bundle (compact)</summary>
          <pre style={{maxHeight:200, overflow:"auto", background:"#111", color:"#fff", padding:8}}>{JSON.stringify(bundle, null, 2)}</pre>
        </details>
      )}
    </div>
  );
}