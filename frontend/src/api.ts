export type User = {id:number;username:string;role:'user'|'admin'};
export type Note = {id:number;owner_id:number;title:string;body:string;collection:string;pinned:number;archived:number;deleted:number;version:number;created_at:number;updated_at:number};
export type Config = {team:string;slug:string;theme:string;edition:string;welcome:string;collections:string[];demo:boolean;marker:string};
export type Session = {user:User|null;csrf:string|null};
let csrf:string|null = null;
const apiRoot = import.meta.env.BASE_URL.replace(/\/$/, '') + '/api';
export function setCsrf(value:string|null){csrf=value;}
export class ApiError extends Error { constructor(message:string, public status:number){super(message);} }
export async function api<T>(path:string, method='GET', data?:unknown):Promise<T>{
  const response=await fetch(apiRoot+path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-NoteVault-Client':'web',...(csrf?{'X-CSRF-Token':csrf}:{})},...(data!==undefined?{body:JSON.stringify(data)}:{})});
  const body=await response.json().catch(()=>({error:'The server returned an unexpected response.'}));
  if(!response.ok)throw new ApiError(body.error||'The request could not be completed.',response.status);
  return body;
}
export async function downloadNotes(format:string){
  const response=await fetch(apiRoot+'/export?fmt='+encodeURIComponent(format),{credentials:'same-origin'});
  if(!response.ok)throw new ApiError('Export failed. Please sign in and try again.',response.status);
  const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');
  link.href=url;link.download=response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1]||'notes.'+format;
  link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
