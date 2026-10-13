import type {Summary} from './types';
import {format} from './api';
export default function ExperimentStatistics({data}:{data:Summary}){
 const names:Record<string,string>={voltage_v:'TEG voltage (V)',current_a:'TEG current (A)',capacitor_v:'Reservoir voltage (V)',hot_c:'Hot interface (°C)',cold_c:'Cold interface (°C)'};
 return <section className="panel"><div className="panel-head"><div><h2>Run statistics</h2><p>{format(data.energy.duration_seconds,'seconds')} sampled span · valid readings only · {data.source}</p></div></div><div className="table-wrap"><table><thead><tr><th>Measurement</th><th>Valid count</th><th>Minimum</th><th>Maximum</th><th>Mean</th></tr></thead><tbody>{Object.entries(names).map(([key,label])=>{const value=data.energy.statistics?.[key];return <tr key={key}><td>{label}</td><td>{value?.count??0}</td><td>{format(value?.min,'',6)}</td><td>{format(value?.max,'',6)}</td><td>{format(value?.mean,'',6)}</td></tr>;})}</tbody></table></div><p className="help">Statistics describe submitted samples only. They do not establish measurement accuracy, continuous availability, or energy neutrality.</p></section>;
}
