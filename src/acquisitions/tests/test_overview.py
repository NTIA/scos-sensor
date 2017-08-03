import pytest

from acquisitions.tests import SINGLE_ACQUISITION, EMPTY_ACQUISITIONS_RESPONSE
from acquisitions.tests.utils import (reverse_acquisitions_preview,
                                      simulate_acquisitions,
                                      get_acquisitions_overview)
from schedule.tests.utils import post_schedule
from scheduler.tests.utils import simulate_scheduler_run


@pytest.mark.django_db
def test_get_empty_acquisitions_overview(client):
    assert get_acquisitions_overview(client) == EMPTY_ACQUISITIONS_RESPONSE


@pytest.mark.django_db
def test_get_acquisitions_overview(client, testclock):
    entry1 = post_schedule(client, SINGLE_ACQUISITION)
    overview, = get_acquisitions_overview(client)
    assert overview['acquisitions_available'] == 0
    simulate_scheduler_run()
    overview, = get_acquisitions_overview(client)
    assert overview['url'] == reverse_acquisitions_preview(entry1['name'])
    assert overview['acquisitions_available'] == 1
    entry2_name = simulate_acquisitions(client, n=3)
    overview_list = get_acquisitions_overview(client)
    assert len(overview_list) == 2
    (overview1, overview2) = overview_list
    assert overview1 == overview
    assert overview2['url'] == reverse_acquisitions_preview(entry2_name)
    assert overview2['acquisitions_available'] == 3


# def test_delete_acquisitions(client, testclock):
#     edid = simulate_acquisition(client)

#     acqs_url = url_for(acqs_ov_url_ref)
#     rdata = validate_response(client.get(acqs_url), 200)
#     d, = rdata
#     assert d['acquisitions'] == 1
#     expected_url = url_for(acqs_md_pv_url_ref, event_descriptor_id=edid)
#     assert d['url'] == expected_url

#     validate_response(client.delete(acqs_url), 200)

#     rdata = validate_response(client.get(acqs_url), 200)
#     assert rdata == []


# def test_get_metadata(client, testclock):
#     edid = simulate_acquisition(client)
#     bad_url = url_for(acqs_md_pv_url_ref, event_descriptor_id='doesntexist')
#     good_url = url_for(acqs_md_pv_url_ref, event_descriptor_id=edid)
#     validate_response(client.get(bad_url), 404)
#     rdata = validate_response(client.get(good_url), 200)
#     assert rdata[0]['event_id'] == 1
#     expected_url = url_for(acq_md_url_ref, event_descriptor_id=edid,
#                            event_id=1)
#     assert rdata[0]['url'] == expected_url


# def test_delete_metadata(client, testclock):
#     edid = simulate_acquisition(client)
#     url = url_for(acqs_md_pv_url_ref, event_descriptor_id=edid)
#     rdata = validate_response(client.delete(url), 200)
#     assert rdata is None
#     validate_response(client.delete(url), 404)


# def test_get_acquisitions_preview(client, testclock):
#     edid = simulate_acquisition(client)
#     good_url = url_for(acq_md_url_ref, event_descriptor_id=edid, event_id=1)
#     bad_edid_url = url_for(acq_md_url_ref, event_descriptor_id='invalid',
#                            event_id=1)
#     bad_event_id_url = url_for(acq_md_url_ref, event_descriptor_id=edid,
#                                event_id=9999)

#     validate_response(client.get(good_url), 200)
#     validate_response(client.get(bad_edid_url), 404)
#     validate_response(client.get(bad_event_id_url), 404)


# def test_delete_acquisitions_preview(client, testclock):
#     edid = simulate_acquisitions(client, n=3)
#     url1 = url_for(acq_md_url_ref, event_descriptor_id=edid, event_id=1)
#     url2 = url_for(acq_md_url_ref, event_descriptor_id=edid, event_id=2)
#     url3 = url_for(acq_md_url_ref, event_descriptor_id=edid, event_id=3)
#     assert validate_response(client.delete(url3), 200) is None
#     validate_response(client.delete(url3), 404)
#     validate_response(client.get(url1), 200)
#     validate_response(client.get(url2), 200)


# def test_acquisition_download(client, testclock):
#     edid = simulate_acquisitions(client, n=2)
#     url = url_for(acq_dl_url_ref, event_descriptor_id=edid, event_id=1)
#     r = client.get(url)
#     assert r.status_code == 200
#     assert r.is_streamed is True
#     assert r.mimetype == 'application/x-tar'

#     with tempfile.NamedTemporaryFile() as tf:
#         tf.write(r.data)
#         sigmf_archive_contents = sigmf.sigmffile.fromarchive(tf.name)
#         md = sigmf_archive_contents._metadata
#         datafile = sigmf_archive_contents.data_file
#         datafile_actual_size = os.stat(datafile).st_size
#         nsamples = md['annotations'][0]['core:sample_count']
#         datafile_expected_size = nsamples * np.float32().nbytes
#         assert datafile_actual_size == datafile_expected_size
#         claimed_sha512 = md['global']['core:sha512']
#         actual_sha512 = sigmf.sigmf_hash.calculate_sha512(datafile)
#         assert claimed_sha512 == actual_sha512 == TEST_DATA_SHA512
