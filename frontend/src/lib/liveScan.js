export async function liveScan(target, {signal, onEvent}) {
    const token=localStorage.getItem("wevnsec-token");
    const response=await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/scan/stream`, {
        method:"POST",headers:{"Content-Type":"application/json",...(token ? {Authorization:`Bearer ${token}`} : {})},
        body:JSON.stringify({target,advanced:false}),signal,
    });
    if(!response.ok){let detail;try{detail=(await response.json()).detail;}catch{ /* A proxy may return a non-JSON error response. */ }throw new Error(typeof detail==="string" ? detail : detail?.message || "Unable to start the scan. Please try again.");}
    const reader=response.body.getReader(),decoder=new TextDecoder();let buffer="",complete=false;
    try {while(true){const {value,done}=await reader.read();buffer+=decoder.decode(value || new Uint8Array(),{stream:!done});const lines=buffer.split("\n");buffer=lines.pop();if(done && buffer.trim())lines.push(buffer);
        for(const line of lines){if(!line.trim())continue;const event=JSON.parse(line);if(event.type==="error")throw new Error(event.message);if(event.type==="complete")complete=true;onEvent(event);}if(done)break;
    }}finally{reader.releaseLock();}
    if(!complete)throw new Error("The scan connection ended before a report was saved. Please try again.");
}