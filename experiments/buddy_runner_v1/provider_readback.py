"""BR-08 GitHub witness readback schema/time/actor check.

This verifies a GitHub-provider-shaped response; only an independent trusted
connector fetch can establish that the response actually came from GitHub.
GitHub comments are editable; this cannot supply WORM or a trusted clock.
"""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlsplit

from runner_stage1 import Stage1Error
from witness_anchor import load_signed_witness


def _require(ok,code):
    if not ok: raise Stage1Error(code)

def _iso(value):
    _require(type(value) is str and value.endswith('Z'), 'GITHUB_TIME_NOT_UTC')
    try: return datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc: raise Stage1Error('GITHUB_TIME_INVALID') from exc

def _comment(item,repo,number,actor):
    _require(type(item) is dict, 'GITHUB_COMMENT_INVALID')
    allowed=('id','html_url','user','body','created_at','updated_at')
    _require(all(k in item for k in allowed), 'GITHUB_COMMENT_METADATA_MISSING')
    _require(type(item['id']) is int and item['id'] > 0 and
             type(item['user']) is dict and type(item['user'].get('login')) is str and
             item['user']['login'].casefold()==actor.casefold(), 'GITHUB_COMMENT_AUTHOR_MISMATCH')
    _require(type(item['body']) is str and len(item['body']) <= 12000, 'GITHUB_COMMENT_BODY_INVALID')
    url=item['html_url']
    _require(type(url) is str and url ==
             f'https://github.com/{repo}/issues/{number}#issuecomment-{item["id"]}',
             'GITHUB_COMMENT_ORIGIN_MISMATCH')
    created,updated=_iso(item['created_at']),_iso(item['updated_at'])
    _require(created == updated, 'GITHUB_COMMENT_EDITED_AFTER_POST')
    return created


def verify_provider_snapshot(witness_comment, disclosure_comment, signed_receipt_bytes, *,
                             expected_repo, expected_issue, expected_witness_author,
                             expected_agent_author, expected_witness_id):
    _require(type(expected_repo) is str and expected_repo and
             type(expected_issue) is int and expected_issue > 0,
             'GITHUB_WITNESS_SCOPE_MISSING')
    _require(type(expected_witness_author) is str and
             type(expected_agent_author) is str and
             expected_witness_author.casefold()!=expected_agent_author.casefold(),
             'GITHUB_WITNESS_NOT_INDEPENDENT_ACTOR')
    obj,_=load_signed_witness(signed_receipt_bytes)
    _require(obj['witness_id']==expected_witness_id, 'GITHUB_WITNESS_ID_MISMATCH')
    witness_at=_comment(witness_comment,expected_repo,expected_issue,expected_witness_author)
    disclosed_at=_comment(disclosure_comment,expected_repo,expected_issue,expected_agent_author)
    _require(witness_comment['id']!=disclosure_comment['id'] and witness_at < disclosed_at,
             'GITHUB_DISCLOSURE_NOT_AFTER_WITNESS')
    expected_body='BUDDY_WITNESS_RECEIPT_V1\n'+signed_receipt_bytes.decode('utf-8')
    _require(witness_comment['body']==expected_body,'GITHUB_WITNESS_BYTES_NOT_READ_BACK')
    signed_at=_iso(obj['attested_at_utc'])
    _require(signed_at <= witness_at, 'GITHUB_SIGNATURE_CLAIM_POSTDATES_PUBLICATION')
    disclosure_body=f'BUDDY_STAGE2_DISCLOSED_V1\n{obj["run_id"]}\n{obj["sealed_event_mac"]}'
    _require(disclosure_comment['body']==disclosure_body,'GITHUB_DISCLOSURE_BASIS_MISMATCH')
    return {
      'schema':'v32-buddy-github-witness-readback-v1',
      'witness_comment_id':witness_comment['id'],
      'disclosure_comment_id':disclosure_comment['id'],
      'witness_created_at':witness_comment['created_at'],
      'disclosure_created_at':disclosure_comment['created_at'],
      'receipt_sha256':'sha256:'+hashlib.sha256(signed_receipt_bytes).hexdigest(),
      'provider_metadata':'STRUCTURALLY_VALIDATED_ONLY',
      'independent_provider_fetch':'CALLER_MUST_ATTEST_AUTHENTIC_API_READBACK',
      'immutable_provider_timestamp':'NOT_PROVEN_GITHUB_COMMENTS_EDITABLE',
      'independent_signer_key':'REQUIRES_SEPARATE_PIN_AND_CUSTODY',
      'execution_authority':'NOT_GRANTED',
    }
