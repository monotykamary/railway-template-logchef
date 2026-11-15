#!/usr/bin/env python3
"""Logchef v2.5 -> v2.7 metadata migration proof, layered on the main API smoke."""
import json
from pathlib import Path
import runpy

core=runpy.run_path(str(Path(__file__).with_name('smoke.py')))
request=core['request'];data=core['data'];require=core['require'];phase=core['PHASE'];state_path=core['STATE']
seed=json.loads(state_path.read_text())
marker=seed['marker']
name='Railway migration '+marker
panels={'version':1,'layout':[{'id':'validation','x':0,'y':0,'w':6,'h':2}],
        'panels':[{'id':'validation','title':name,'type':'table','team_id':seed['team_id'],'source_id':seed['source_id'],
                   'query':'body~"'+marker+'"','query_language':'logchefql'}]}
if 'dashboard_id' not in seed:
 require(phase=='boot','missing boot-created dashboard; refusing to recreate after upgrade')
 dashboard=data('/api/v1/dashboards',method='POST',expected=(201,),payload={'name':name,'description':marker,'panels':panels})
 seed['dashboard_id']=dashboard['id'];seed['dashboard_description']=marker
 collection=data('/api/v1/collections',method='POST',expected=(201,),payload={'name':name,'description':marker})
 seed['collection_id']=collection['id']
 state_path.write_text(json.dumps(seed));state_path.chmod(0o600)
path='/api/v1/dashboards/'+str(seed['dashboard_id'])
dashboard=data(path)
require(dashboard['name']==name and dashboard['description']==seed['dashboard_description'],'seeded dashboard metadata lost')
blob=dashboard['panels']
require(blob['version']==1 and blob['layout']==panels['layout'],'legacy schema-1 layout not preserved')
require(len(blob['panels'])==1,'legacy dashboard panel missing')
for key,value in panels['panels'][0].items():require(blob['panels'][0].get(key)==value,'legacy panel field lost: '+key)
collection=data('/api/v1/collections/'+str(seed['collection_id']))
require(collection['name']==name and collection['description']==marker,'shared collection metadata lost')
require(collection.get('is_personal') is False,'shared collection became personal')
revision=dashboard.get('revision')
if phase!='boot':require(isinstance(revision,int) and revision>=1,'v2.7 revision migration missing')
if revision is not None:
 require(isinstance(revision,int) and revision>=1,'invalid dashboard revision')
 summaries=data('/api/v1/dashboards')
 summary=next((item for item in summaries if item['id']==seed['dashboard_id']),None)
 require(summary is not None and summary.get('panel_count')==1,'dashboard summary migration did not retain panel count')
 require(summary.get('panel_types')==['table'] and not summary.get('corrupt',False),'dashboard summary migration changed panel type or marked it corrupt')
 body={'name':name,'description':'must-not-be-written','panels':panels}
 request(path,method='PUT',expected=(428,),payload=body)
 request(path,method='PUT',expected=(409,),payload={**body,'revision':0})
 after=data(path)
 require(after['revision']==revision and after['description']==seed['dashboard_description'],'rejected writes modified dashboard')
 if not seed.get('v27_save_proven'):
  description=marker+' migrated'
  updated=data(path,method='PUT',payload={'name':name,'description':description,'panels':panels,'revision':revision})
  require(updated['revision']==revision+1,'valid revisioned save did not advance exactly once')
  seed['dashboard_description']=description;seed['dashboard_revision']=updated['revision'];seed['v27_save_proven']=True
  state_path.write_text(json.dumps(seed));state_path.chmod(0o600)
 else:
  require(revision==seed['dashboard_revision'],'dashboard revision did not persist across redeploy')
print(json.dumps({'ok':True,'phase':phase,'legacy_dashboard_preserved':True,'shared_collection_preserved':True,
                  'v27_revision_semantics':revision is not None,'delegated_link_conversion_covered':False}))
