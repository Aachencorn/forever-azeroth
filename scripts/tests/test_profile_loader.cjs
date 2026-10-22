const assert=require('node:assert/strict');const L=require('../../soop-profile-loader.js');
(async()=>{
 assert.equal(L.url('jingburger1'),'https://profile.img.sooplive.co.kr/LOGO/ji/jingburger1/jingburger1.jpg');
 for(const id of ['ecvhao','neez0611','mygomiee','hachi97','lina0108'])assert.equal(L.url(id),`https://profile.img.sooplive.co.kr/LOGO/${id.slice(0,2)}/${id}/${id}.jpg`);
 assert.throws(()=>L.url('../bad'));
 let requests=0,waits=0;const cache={};const options={cache,now:()=>1000,probe:async()=>{requests++;return true},delay:async()=>{waits++}};
 assert.equal((await L.resolve('ecvhao',options)).status,'success');assert.equal((await L.resolve('ecvhao',options)).cached,true);assert.equal(requests,1);
 const failure=await L.resolve('hachi97',{probe:async()=>{requests++;return false},delay:async()=>{waits++}});assert.equal(failure.status,'failed');assert.equal(requests,3);assert.equal(waits,1);
 const controller=new AbortController();controller.abort();assert.equal((await L.resolve('lina0108',{signal:controller.signal,probe:()=>{throw Error('must not request')}})).status,'failed');
 console.log('PASS: supplied URL, five IDs, successful probe, URL cache, retry, failure and cancellation; no LIVE dependency');
})().catch(e=>{console.error(e);process.exit(1)});
