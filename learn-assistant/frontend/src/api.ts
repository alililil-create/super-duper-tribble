import {defineStore} from 'pinia'
export const useAuth=defineStore('auth',{
  state:()=>({token:sessionStorage.getItem('learn-token')||'',username:''}),
  actions:{setToken(value:string){this.token=value;sessionStorage.setItem('learn-token',value)},logout(){this.token='';this.username='';sessionStorage.removeItem('learn-token')}}
})
export async function api<T=any>(path:string,method='GET',body?:unknown):Promise<T>{
 const auth=useAuth()
 const res=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json',...(auth.token?{Authorization:'Bearer '+auth.token}:{})},...(body?{body:JSON.stringify(body)}:{})})
 const data=await res.json()
 if(!res.ok){if(res.status===401 && path!=='/auth/login')auth.logout();throw new Error(typeof data.detail==='string'?data.detail:'输入格式不正确，请检查字段与长度')}
 return data
}
