/** Bounded native mutations. No sharing or automatic retries of writes. */
export async function writeJson<T>(url: string, headers: Record<string,string>, method: string, body: unknown, message: string, timeoutMs=30_000): Promise<T> {
  const controller=new AbortController();let timer:ReturnType<typeof setTimeout>|undefined;
  try {
    return await Promise.race([
      (async()=>{
        const response=await fetch(url,{method,headers,body:body===undefined?undefined:JSON.stringify(body),signal:controller.signal});
        const data=await response.json().catch(()=>null);
        if(!response.ok) throw Object.assign(new Error(data?.detail || message), { status: response.status });
        if(data===null) throw new Error(`${message}: confirmação inválida. Atualize a lista antes de reenviar.`);
        return data as T;
      })(),
      new Promise<never>((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(new Error(`${message}: confirmação demorou demais. Atualize a lista antes de reenviar; o servidor pode ter salvo.`));},timeoutMs);}),
    ]);
  } finally {clearTimeout(timer);}
}
