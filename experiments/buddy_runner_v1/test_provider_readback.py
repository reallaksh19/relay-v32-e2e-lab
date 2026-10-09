"""Provider-shaped data contract; NOT an actual independent GitHub witness."""
from __future__ import annotations
import base64
import json
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from runner_stage1 import Stage1Error,canonical
from provider_readback import verify_provider_snapshot

class ProviderReadbackTests(unittest.TestCase):
 def setUp(self):
  key=Ed25519PrivateKey.generate()
  self.body={'schema':'v32-buddy-external-witness-v1','witness_id':'independent-witness-1',
    'run_id':'R01','event':'PLAN_SEALED','sealed_event_mac':'1'*64,
    'manifest_digest':'sha256:'+'1'*64,'plan_receipt_digest':'sha256:'+'2'*64,
    'gate_digest':'sha256:'+'3'*64,'witness_event_id':'br8-1',
    'attested_at_utc':'2026-10-09T12:00:00Z'}
  self.signed=canonical({**self.body,'signature_b64':base64.b64encode(key.sign(canonical(self.body))).decode()})
  self.witness=self.comment(101,'other-witness', '2026-10-09T12:00:01Z',
                      'BUDDY_WITNESS_RECEIPT_V1\n'+self.signed.decode())
  self.disclosure=self.comment(102,'agent-one','2026-10-09T12:00:02Z',
                'BUDDY_STAGE2_DISCLOSED_V1\nR01\n'+'1'*64)
 def comment(self,id,actor,now,body):
  return {'id':id,'user':{'login':actor},'html_url':f'https://github.com/reallaksh19/relay-v32-e2e-lab/issues/7#issuecomment-{id}',
          'created_at':now,'updated_at':now,'body':body}
 def verify(self,w=None,d=None,**overrides):
  return verify_provider_snapshot(w or self.witness,d or self.disclosure,self.signed,
      **{**{'expected_repo':'reallaksh19/relay-v32-e2e-lab','expected_issue':7,
       'expected_witness_author':'other-witness','expected_agent_author':'agent-one',
       'expected_witness_id':'independent-witness-1'},**overrides})
 def test_nominal_provider_shaped_snapshot_but_not_live_proof(self):
  a=self.verify();self.assertEqual('STRUCTURALLY_VALIDATED_ONLY',a['provider_metadata'])
  self.assertEqual('NOT_GRANTED',a['execution_authority'])
 def test_same_actor_denied(self):
  with self.assertRaisesRegex(Stage1Error,'NOT_INDEPENDENT_ACTOR'):
   self.verify(expected_witness_author='agent-one')
 def test_missing_trusted_provider_id_denied(self):
  bad={**self.witness,'id':0}
  with self.assertRaises(Stage1Error):self.verify(w=bad)
 def test_wrong_url_denied(self):
  bad={**self.witness,'html_url':'https://evil.invalid'}
  with self.assertRaisesRegex(Stage1Error,'ORIGIN_MISMATCH'):self.verify(w=bad)
 def test_edited_comment_denied(self):
  bad={**self.witness,'updated_at':'2026-10-09T12:00:03Z'}
  with self.assertRaisesRegex(Stage1Error,'EDITED_AFTER_POST'):self.verify(w=bad)
 def test_disclosure_precedes_witness_denied(self):
  bad={**self.disclosure,'created_at':'2026-10-09T11:59:59Z','updated_at':'2026-10-09T11:59:59Z'}
  with self.assertRaisesRegex(Stage1Error,'NOT_AFTER_WITNESS'):self.verify(d=bad)
 def test_modified_witness_body_denied(self):
  bad={**self.witness,'body':self.witness['body']+'\nextra'}
  with self.assertRaisesRegex(Stage1Error,'BYTES_NOT_READ_BACK'):self.verify(w=bad)
 def test_wrong_disclosure_mac_denied(self):
  bad={**self.disclosure,'body':self.disclosure['body'][:-1]+'0'}
  with self.assertRaisesRegex(Stage1Error,'DISCLOSURE_BASIS_MISMATCH'):self.verify(d=bad)
 def test_future_signing_time_denied(self):
  bad={**self.witness,'created_at':'2026-10-09T11:59:59Z','updated_at':'2026-10-09T11:59:59Z'}
  with self.assertRaisesRegex(Stage1Error,'CLAIM_POSTDATES'):self.verify(w=bad)
 def test_actual_connector_shape_without_timestamps_fails_closed(self):
  item={**self.witness,'url':self.witness['html_url'], 'created_at':None,
        'updated_at':None}
  del item['html_url']
  with self.assertRaisesRegex(Stage1Error,'GITHUB_TIME_NOT_UTC'):
   self.verify(w=item)
 def test_mismatched_witness_id_denied(self):
  with self.assertRaisesRegex(Stage1Error,'WITNESS_ID_MISMATCH'):
   self.verify(expected_witness_id='unknown')

if __name__=='__main__':unittest.main()
