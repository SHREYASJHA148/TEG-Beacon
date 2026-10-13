const base=import.meta.env.VITE_API_URL || '';
export async function api<T>(path:string, method='GET', data?:unknown):Promise<T> {
  const token=sessionStorage.getItem('thermotrack-admin-token');
  const response=await fetch(`${base}/api/v1${path}`,{method,headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{})},body:data===undefined?undefined:JSON.stringify(data)});
  if(!response.ok){const error=await response.json().catch(()=>({detail:'Backend unavailable. Start the local server and retry.'})); const message=typeof error.detail==='string'?error.detail:Array.isArray(error.detail)?error.detail.map((item:{msg?:string})=>(item.msg||'Invalid input').replace(/^Value error, /,'')).join('; '):'Unable to process the request';throw new Error(message);}
  return response.json();
}
export function format(value:number|null|undefined, unit='', decimals=2){return value==null?'—':`${value.toLocaleString(undefined,{maximumFractionDigits:decimals})}${unit ? ' '+unit : ''}`;}
export function time(value:string|undefined){return value?new Date(value).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'}):'No readings yet';}
export async function download(id:string){const token=sessionStorage.getItem('thermotrack-admin-token'); const response=await fetch(`${base}/api/v1/experiments/${id}/export`,{headers:token?{Authorization:`Bearer ${token}`}:{}}); if(!response.ok)throw new Error('Export failed'); const url=URL.createObjectURL(await response.blob()); const link=document.createElement('a');link.href=url;link.download=`thermotrack-${id}.csv`;link.click();URL.revokeObjectURL(url);}
