"""Offline repair-spending contract tests; provider calls are mocked."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import agentic_pipeline as ap
import kie_tasks as kie
import repair_runner as repair


class RepairRunnerTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        for obj,key,value in [(ap,'ROOT',self.root),(kie,'ROOT',self.root),(kie,'STATE',self.root/'File/generation')]:
            p=patch.object(obj,key,value);p.start();self.addCleanup(p.stop)
        p=patch.object(kie,'config',side_effect=lambda:{'KIE_API_KEY':'test-only-not-real','KIE_PROJECT_CAP_CREDITS':os.environ.get('KIE_PROJECT_CAP_CREDITS','0')})
        p.start();self.addCleanup(p.stop)
        p=patch.object(kie,'api',return_value={'code':200,'data':{'taskId':'mock-task'}});self.api=p.start();self.addCleanup(p.stop)
        for name in ('original.png','reference.png','take.png'): (self.root/name).write_text(name)
        self.policy={'version':1,'id':'repairs','producer_id':'parent','repairCapCredits':'12','perAttemptCapCredits':'6','projectCapCredits':'24',
                     'maxAttemptsPerAsset':2,'models':['image-edit-model'],'allowedChecks':['framing','anatomy'],
                     'requiredReviewChecks':['framing','anatomy'],
                     'modelTemplates':{'image-edit-model':{'payload':{'model':'image-edit-model','input':{'prompt':'','image_urls':[]}},'prompt_field':'input.prompt','images_field':'input.image_urls'}},
                     'assets':[{'id':'frame1','source':'original.png','references':['reference.png'],'preserve':'Same character, scene, style and story'}]}
        self.write('policy.json',self.policy)

    def write(self,path,value):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));return path

    def authorize(self):
        packet=repair.proposal('policy.json');repair.authorize('policy.json',packet['approvalHash'],'user:one-time-repair-allowance')

    def request(self,n=1,cap='6',model='image-edit-model'):
        state={'policy':repair.proposal('policy.json')}
        media='original.png'
        if (repair.folder()/'state.json').exists():
            state=repair.load_state()
            attempts=state['attempts']
            if attempts and attempts[-1].get('disposition'): media=attempts[-1]['disposition']['selected_media']['path']
        report={'reviewer_id':'reviewer'+str(n),'delegation_id':'review'+str(n),'asset_id':'frame1','media':ap.fingerprint(media),
                'checks':{'framing':{'status':'fail','evidence':'Observed required hand outside frame'},
                          'anatomy':{'status':'pass','evidence':'Fixture anatomy inspection'}}}
        completion={'status':'completed','taskId':report['delegation_id'],'childThreadId':report['reviewer_id']}
        self.write('review'+str(n)+'.json',report);self.write('completion'+str(n)+'.json',completion)
        receipt=self.write('upload-receipt'+str(n)+'.json',{'tool_evidence':'Synthetic fixture upload binding'})
        uploads=[{'media':ap.fingerprint(path),'url':'https://example.com/'+path,'receipt':ap.fingerprint(receipt)} for path in (media,'reference.png')]
        self.write('uploads'+str(n)+'.json',uploads)
        req={'id':'fix'+str(n),'asset_id':'frame1','correction':'Restore required hand visibility','media':media,
             'report':'review'+str(n)+'.json','completion':'completion'+str(n)+'.json','failed_checks':['framing'],
             'model':'image-edit-model','uploads':'uploads'+str(n)+'.json'}
        payload=repair.bound_payload(state,req);payload['model']=model;req['model']=model
        preview=kie.preview(self.write('payload'+str(n)+'.json',payload),cap);req['preview_id']=preview['id']
        self.write('request'+str(n)+'.json',req)
        return 'request'+str(n)+'.json',preview

    def finish(self,n=1,selection='retain_previous'):
        req=ap.load('request'+str(n)+'.json');preview=req['preview_id'];_,op=kie.paths(preview);operation=kie.load(op)
        url='https://example.com/result'+str(n)+'.png'
        receipt=self.write('provider-result'+str(n)+'.json',{'operationId':preview,'receipt':{'taskId':operation['taskId'],'state':'success','resultJson':{'resultUrls':[url]}}})
        operation.update(status='succeeded',latestReceipt=receipt);kie.replace(op,operation)
        media='Assets/result'+str(n)+'.png';(self.root/'Assets').mkdir(exist_ok=True);(self.root/media).write_text('result'+str(n))
        self.write(media+'.download.json',{'urlHash':ap.digest(url),'media':ap.fingerprint(media)})
        report=ap.load(req['report']);report.update(media=ap.fingerprint(media),reviewer_id='rereviewer'+str(n),delegation_id='rereview'+str(n))
        if selection=='accepted':report['checks']['framing']['status']='pass'
        self.write('rereview'+str(n)+'.json',report)
        self.write('recomplete'+str(n)+'.json',{'status':'completed','taskId':report['delegation_id'],'childThreadId':report['reviewer_id']})
        record={'preview_id':preview,'media':media,'report':'rereview'+str(n)+'.json','completion':'recomplete'+str(n)+'.json','selection':selection,'reason':'Preserve better prior version in fixture'}
        repair.record_result(self.write('result-record'+str(n)+'.json',record),'parent')

    def test_standing_1000_credit_default_is_bound_without_spending(self):
        self.write('File/repair_defaults.json',{'version':1,'repairCapCredits':'1000','maxAttemptsPerAsset':2})
        self.policy.pop('repairCapCredits');self.policy.pop('maxAttemptsPerAsset')
        self.policy['projectCapCredits']='1012';self.write('policy.json',self.policy)
        proposal=repair.proposal('policy.json')
        self.assertEqual(proposal['scope']['repairCapCredits'],'1000')
        self.assertEqual(proposal['scope']['maxAttemptsPerAsset'],2)
        self.assertIn(ap.fingerprint('File/repair_defaults.json'),proposal['inputs'])
        self.api.assert_not_called()
        self.assertFalse((repair.folder()/'state.json').exists())
        repair.authorize('policy.json',proposal['approvalHash'],'user:standing-1000-repair-limit')
        self.write('File/repair_defaults.json',{'version':1,'repairCapCredits':'600','maxAttemptsPerAsset':2})
        with self.assertRaises(ValueError):repair.load_state()

    def test_one_allowance_automatically_covers_two_new_payloads(self):
        self.authorize()
        for n in (1,2):
            req,_=self.request(n); result=repair.submit(req,'parent');self.assertEqual(result['submission']['paidRequests'],1)
            self.finish(n)
        self.assertEqual(self.api.call_count,2);self.assertEqual(result['remainingCredits'],'0')

    def test_same_request_never_submits_twice(self):
        self.authorize();req,_=self.request();repair.submit(req,'parent');result=repair.submit(req,'parent')
        self.assertEqual(self.api.call_count,1);self.assertEqual(result['attempts'],1);self.assertEqual(result['submission']['paidRequests'],0)

    def test_no_allowance_no_submission(self):
        req,_=self.request()
        with self.assertRaises(FileNotFoundError):repair.submit(req,'parent')
        self.api.assert_not_called()

    def test_wrong_approval_cannot_enable_allowance(self):
        with self.assertRaises(ValueError):repair.authorize('policy.json','wrong','user:reference')
        self.assertFalse((repair.folder()/'state.json').exists())

    def test_attempt_limit_cannot_reset_using_new_preview(self):
        self.authorize()
        for n in (1,2):
            req,_=self.request(n);repair.submit(req,'parent');self.finish(n)
        req,_=self.request(3)
        with self.assertRaisesRegex(ValueError,'attempt limit'):repair.submit(req,'parent')
        self.assertEqual(self.api.call_count,2)

    def test_total_budget_blocks_before_attempt_limit(self):
        self.policy['repairCapCredits']='6';self.write('policy.json',self.policy);self.authorize()
        req,_=self.request(1);repair.submit(req,'parent');self.finish(1);req,_=self.request(2)
        with self.assertRaisesRegex(ValueError,'allowance exhausted'):repair.submit(req,'parent')
        self.assertEqual(self.api.call_count,1)

    def test_model_and_per_attempt_limit_enforced(self):
        self.authorize()
        for n,cap,model in [(1,'6','other-model'),(2,'7','image-edit-model')]:
            req,_=self.request(n,cap,model)
            with self.subTest(n=n),self.assertRaises(ValueError):repair.submit(req,'parent')
        self.api.assert_not_called()

    def test_uncertain_or_self_review_cannot_authorize_repair(self):
        self.authorize();req,_=self.request()
        report=ap.load('review1.json');report['checks']['framing']['status']='uncertain';self.write('review1.json',report)
        with self.assertRaises(ValueError):repair.submit(req,'parent')
        report['checks']['framing']['status']='fail';report['reviewer_id']='parent';self.write('review1.json',report)
        self.write('completion1.json',{'status':'completed','taskId':'review1','childThreadId':'parent'})
        with self.assertRaises(ValueError):repair.submit(req,'parent')
        self.api.assert_not_called()

    def test_changed_scope_or_references_block(self):
        self.authorize();req,_=self.request();(self.root/'reference.png').write_text('new identity')
        with self.assertRaises(ValueError):repair.submit(req,'parent')
        self.api.assert_not_called()

    def test_unknown_outcome_keeps_reservation_and_no_new_attempt(self):
        self.authorize();req,_=self.request();self.api.side_effect=TimeoutError()
        with self.assertRaises(kie.Refused):repair.submit(req,'parent')
        self.assertEqual(repair.summary(repair.load_state())['reservedOrReportedCredits'],'6')
        retry=repair.submit(req,'parent');self.assertEqual(retry['submission']['paidRequests'],0)
        req,_=self.request(2)
        with self.assertRaisesRegex(ValueError,'previous repair|unknown repair'):repair.submit(req,'parent')
        self.assertEqual(self.api.call_count,1)

    def test_crash_after_reservation_reuses_existing_attempt(self):
        self.authorize();req,_=self.request()
        with patch.object(kie,'submit',side_effect=OSError('interruption before provider call')):
            with self.assertRaises(OSError):repair.submit(req,'parent')
        result=repair.submit(req,'parent');self.assertEqual(result['attempts'],1);self.assertEqual(self.api.call_count,1)

    def test_project_cap_counts_original_spend_and_restores_environment(self):
        self.policy['projectCapCredits']='12';self.write('policy.json',self.policy);self.authorize();req,preview=self.request()
        original=kie.preview(self.write('original-payload.json',{'model':'image-edit-model','input':{}}),'12')
        _,p=kie.paths(original['id']);kie.write_new(p,{'id':original['id'],'status':'succeeded','capCredits':'12','reportedCredits':'12'})
        with patch.dict(os.environ,{'KIE_PROJECT_CAP_CREDITS':'999'}):
            with self.assertRaises(kie.Refused):repair.submit(req,'parent')
            self.assertEqual(os.environ['KIE_PROJECT_CAP_CREDITS'],'999')
        self.api.assert_not_called()

    def test_changed_request_or_different_caller_refused(self):
        self.authorize();req,_=self.request()
        with self.assertRaises(ValueError):repair.submit(req,'other')
        repair.submit(req,'parent');value=ap.load(req);value['correction']='Replace character';self.write(req,value)
        with self.assertRaises(ValueError):repair.submit(req,'parent')
        self.assertEqual(self.api.call_count,1)

    def test_unrelated_payload_or_reference_binding_is_rejected(self):
        self.authorize();req,preview=self.request()
        payload=preview['payload'];payload['input']['prompt']='Generate an unrelated scene'
        modified=kie.preview(self.write('unrelated.json',payload),'6')
        value=ap.load(req);value['preview_id']=modified['id'];self.write(req,value)
        with self.assertRaisesRegex(ValueError,'not bound'):repair.submit(req,'parent')
        value['preview_id']=preview['id'];self.write(req,value)
        uploads=ap.load(value['uploads']);uploads[1]['media']=ap.fingerprint('take.png');self.write(value['uploads'],uploads)
        with self.assertRaisesRegex(ValueError,'bindings differ'):repair.submit(req,'parent')
        self.api.assert_not_called()

    def test_next_attempt_waits_for_reviewed_result(self):
        self.authorize();req,_=self.request(1);repair.submit(req,'parent');req,_=self.request(2)
        with self.assertRaisesRegex(ValueError,'previous repair'):repair.submit(req,'parent')
        self.assertEqual(self.api.call_count,1)

    def test_accepted_result_blocks_further_paid_repairs(self):
        self.authorize();req,_=self.request(1);repair.submit(req,'parent');self.finish(1,'accepted');req,_=self.request(2)
        with self.assertRaisesRegex(ValueError,'Accepted asset'):repair.submit(req,'parent')
        self.assertEqual(self.api.call_count,1)

    def test_corrected_result_is_the_next_input_lineage(self):
        self.authorize();req,_=self.request(1);repair.submit(req,'parent');self.finish(1,'use_corrected')
        req,_=self.request(2);self.assertEqual(ap.load(req)['media'],'Assets/result1.png')
        repair.submit(req,'parent');self.assertEqual(self.api.call_count,2)

    def test_existing_allowance_cannot_be_reauthorized_to_reset_spend(self):
        self.authorize();req,_=self.request();repair.submit(req,'parent')
        self.authorize();self.assertEqual(repair.summary(repair.load_state())['attempts'],1)
        self.policy['id']='reset';self.write('policy.json',self.policy)
        with self.assertRaises(ValueError):self.authorize()


if __name__=='__main__':unittest.main()
