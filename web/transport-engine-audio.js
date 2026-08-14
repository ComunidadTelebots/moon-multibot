const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, Number(value) || 0));

/** Lightweight procedural truck soundscape. One shared noise buffer and a fixed
 * node graph keep it suitable for mobile; only short UI/mechanical cues allocate
 * transient oscillators. Existing setRunning/update/dispose API remains intact. */
export function createEngineAudio(){
  let context=null,master=null,engineBus=null,low=null,high=null,intake=null,engineFilter=null;
  let roadSource=null,roadGain=null,roadFilter=null,weatherSource=null,windGain=null,rainGain=null,windFilter=null,rainFilter=null;
  let running=false,lastIndicator=0,lastIndicatorPulse=false,lastBraking=false,lastAirAt=-Infinity,volume=.72;
  const nodes=[];
  const connect=(node)=>{nodes.push(node);return node};
  function noiseBuffer(seconds=2){
    const length=Math.max(1,Math.floor(context.sampleRate*seconds)),buffer=context.createBuffer(1,length,context.sampleRate),data=buffer.getChannelData(0);
    let seed=9137;for(let index=0;index<length;index+=1){seed=(seed*16807)%2147483647;data[index]=(seed/1073741823.5-1)*(.72+Math.sin(index*.017)*.08)}return buffer;
  }
  function loopNoise(buffer,gain,filter){const source=connect(context.createBufferSource());source.buffer=buffer;source.loop=true;source.connect(filter).connect(gain);source.start();return source}
  async function ensure(){
    if(context)return;context=new (window.AudioContext||window.webkitAudioContext)();
    master=connect(context.createGain());master.gain.value=0;master.connect(context.destination);
    engineBus=connect(context.createGain());engineBus.gain.value=0;engineFilter=connect(context.createBiquadFilter());engineFilter.type="lowpass";engineFilter.frequency.value=420;engineFilter.Q.value=.65;engineFilter.connect(engineBus).connect(master);
    low=connect(context.createOscillator());low.type="sawtooth";high=connect(context.createOscillator());high.type="triangle";intake=connect(context.createOscillator());intake.type="sine";
    const lowGain=connect(context.createGain()),highGain=connect(context.createGain()),intakeGain=connect(context.createGain());lowGain.gain.value=.32;highGain.gain.value=.09;intakeGain.gain.value=.055;
    low.connect(lowGain).connect(engineFilter);high.connect(highGain).connect(engineFilter);intake.connect(intakeGain).connect(engineFilter);low.start();high.start();intake.start();
    const buffer=noiseBuffer();
    roadGain=connect(context.createGain());roadGain.gain.value=0;roadFilter=connect(context.createBiquadFilter());roadFilter.type="bandpass";roadFilter.Q.value=.55;roadSource=loopNoise(buffer,roadGain,roadFilter);roadGain.connect(master);
    windGain=connect(context.createGain());windGain.gain.value=0;windFilter=connect(context.createBiquadFilter());windFilter.type="highpass";windFilter.frequency.value=420;loopNoise(buffer,windGain,windFilter);windGain.connect(master);
    rainGain=connect(context.createGain());rainGain.gain.value=0;rainFilter=connect(context.createBiquadFilter());rainFilter.type="bandpass";rainFilter.frequency.value=2700;rainFilter.Q.value=.28;weatherSource=loopNoise(buffer,rainGain,rainFilter);rainGain.connect(master);
  }
  async function setRunning(value){await ensure();await context.resume();running=Boolean(value);const now=context.currentTime;master.gain.cancelScheduledValues(now);master.gain.setTargetAtTime(volume,now,.08);engineBus.gain.setTargetAtTime(running?.2:0,now,running?.12:.06);return running}
  function cue({frequency=700,duration=.055,gain=.035,type="square",slide=1}={}){if(!context||context.state!=="running")return;const now=context.currentTime,osc=context.createOscillator(),amp=context.createGain();osc.type=type;osc.frequency.setValueAtTime(frequency,now);osc.frequency.exponentialRampToValueAtTime(Math.max(20,frequency*slide),now+duration);amp.gain.setValueAtTime(0,now);amp.gain.linearRampToValueAtTime(gain,now+.006);amp.gain.exponentialRampToValueAtTime(.0001,now+duration);osc.connect(amp).connect(master);osc.start(now);osc.stop(now+duration+.01)}
  function triggerAirBrake(intensity=.7){if(!context||context.currentTime-lastAirAt<.28)return;lastAirAt=context.currentTime;cue({frequency:190,duration:.24,gain:.055*clamp(intensity,.2,1),type:"sawtooth",slide:.18})}
  function update({rpm=600,load=0,running:value=running,speed=0,surface="asphalt",weather="clear",windSpeed=0,braking=false,indicator=0,hazards=false}={}){
    if(!context)return;running=Boolean(value);const now=context.currentTime,normalizedRpm=clamp((Number(rpm)-550)/1650),normalizedSpeed=clamp(Math.abs(Number(speed))/110),engineLoad=clamp(load),firing=Math.max(18,Number(rpm||0)/60*3);
    low.frequency.setTargetAtTime(firing,now,.045);high.frequency.setTargetAtTime(firing*2.03,now,.04);intake.frequency.setTargetAtTime(firing*.51,now,.07);
    engineFilter.frequency.setTargetAtTime(250+normalizedRpm*930+engineLoad*420,now,.08);engineBus.gain.setTargetAtTime(running?(.14+normalizedRpm*.16+engineLoad*.1):0,now,.07);
    const loose=/gravel|dirt|soil|grass|shoulder/.test(String(surface));roadFilter.frequency.setTargetAtTime(loose?520:190+normalizedSpeed*290,now,.12);roadGain.gain.setTargetAtTime(normalizedSpeed*(loose?.16:.075),now,.12);
    windFilter.frequency.setTargetAtTime(380+normalizedSpeed*1150,now,.15);windGain.gain.setTargetAtTime(clamp(normalizedSpeed*.09+Number(windSpeed)*.0015,0,.16),now,.18);
    rainGain.gain.setTargetAtTime(/rain|storm/.test(String(weather))?.105:0,now,.22);
    const indicatorState=hazards?2:Math.sign(Number(indicator)||0),pulse=indicatorState!==0&&Math.floor(now/.46)%2===0;
    if(pulse&&!lastIndicatorPulse)cue({frequency:indicatorState===2?760:690,duration:.045,gain:.025,type:"square",slide:.92});lastIndicatorPulse=pulse;lastIndicator=indicatorState;
    if(lastBraking&&!braking&&normalizedSpeed<.18)triggerAirBrake(.55);lastBraking=Boolean(braking);
  }
  function dispose(){try{nodes.forEach(node=>{if(typeof node.stop==="function")node.stop();node.disconnect?.()});context?.close()}catch{}context=master=engineBus=low=high=intake=engineFilter=roadSource=roadGain=roadFilter=weatherSource=windGain=rainGain=windFilter=rainFilter=null}
  function setVolume(value){volume=clamp(value);if(master&&context)master.gain.setTargetAtTime(volume,context.currentTime,.06);return volume}
  return {setRunning,setVolume,update,triggerAirBrake,dispose,get running(){return running},get volume(){return volume}};
}
