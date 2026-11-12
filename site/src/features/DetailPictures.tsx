import { Stage } from '../kit/stage'
import { Card } from '../kit/parts/Card'
import { States } from '../kit/motion/States'
import type { Act } from '../kit/act'
import type { Theme } from '../kit/looks'

type Detail = 'gapless' | 'opus' | 'system' | 'playlist'
async function script(a: Act<{on:boolean}>) {
  await a.wait(900);a.mark('change');await a.set({on:true});await a.wait(2400)
}
export default function DetailPicture({theme,width,mode}:{theme:Theme;width:number;mode:Detail}) {
  return <Stage width={width} height={280} initial={{on:false}} poster={{on:true}} play="once" script={script} theme={theme} accent="var(--ce-accent)" tokens={{'--ss-font':'var(--ce-font)'}} className="ft-stage detail-stage">
    {s => <div className="detail-scene" data-detail={mode} data-on={s.on}>
      {mode==='playlist' ? <Card pad="large" gap={16} className="detail-playlist">
        <div className="detail-list-title">Evening.m3u <span>3 tracks</span></div>
        <div className="detail-tracks"><div className="detail-track-highlight" style={{transform:`translateY(${s.on?44:0}px)`}} />
        {['Evening light','Open water','Last train'].map((name,i)=><div className="detail-track" key={name}><span>0{i+1}</span><span>{name}</span><span>{['04:13','03:28','05:02'][i]}</span></div>)}
        </div><div className="detail-list-foot">Next and shuffle stay in this playlist.</div>
      </Card> : mode==='opus' ? <div className="detail-formats">
        <div className="detail-format"><span>Minimal</span><strong>.wma</strong><small>WMA retained</small></div>
        <div className="detail-format detail-format--active"><span>Standard</span><strong>.opus</strong><small>Opus replaces WMA</small></div>
      </div> : mode==='system' ? <div className="detail-timer">
        <div className="detail-bar-label"><span>Stock wheel timer</span><strong>2,500 / s</strong></div><div className="detail-bar"><i /></div>
        <div className="detail-bar-label"><span>CE wheel timer</span><strong>1,000 / s</strong></div><div className="detail-bar detail-bar--ce"><i style={{width:s.on?'40%':'100%'}} /></div>
        <p>60% fewer timer wakeups.<br/>Battery-life gains have not been measured.</p>
      </div> : <div className="detail-gapless">
        <div className="detail-wave-label"><span>Track 01.flac</span><span>Track 02.flac</span></div>
        <svg viewBox="0 0 440 90" role="img" aria-label="Two same-format tracks with a shorter gap and no decoder reload">
          {Array.from({length:44},(_,i)=><rect key={i} x={i*10+2} y={45-(14+(i*23)%60)/2} width="5" height={14+(i*23)%60} rx="2" className={i<22?'wave-first':'wave-second'}/>)}
          <rect className="detail-gap" x="212" y="0" width={s.on?'4':'16'} height="90" />
        </svg>
        <div className="detail-join"><i/><span>Track boundary</span></div>
        <States value={s.on?'ce':'stock'} states={{stock:'Stock: about 20.5 ms of reload, reboot and DAC writes',ce:'CE: about 4.7 ms, decoder kept running'}} />
      </div>}
    </div>}
  </Stage>
}
