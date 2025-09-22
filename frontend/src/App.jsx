import React, { useState } from "react";
import Chatbot from "./components/Chatbot";
import { strings } from "./i18n";

export default function App(){
  const [lang, setLang] = useState("en");
  const s = strings[lang];
  return (
    <div style={{maxWidth:900, margin:"1rem auto", fontFamily:"sans-serif", padding:"1rem"}}>
      <header style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
        <h1>Punjab Farm Advisor</h1>
        <div>
          <button onClick={()=>setLang("en")} disabled={lang==="en"}>EN</button>
          <button onClick={()=>setLang("hi")} disabled={lang==="hi"} style={{marginLeft:8}}>हिंदी</button>
        </div>
      </header>

      <main style={{marginTop:20}}>
        <p>{s.greet}</p>
        <Chatbot lang={lang} />
      </main>
    </div>
  );
}