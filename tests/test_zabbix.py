from kzabbix.zabbix import ZabbixClient


class FakeZabbix(ZabbixClient):
    def __init__(self):
        pass

    def rpc(self, method, params, auth=True):
        if method == "event.get":
            if params["eventids"] == ["2"]:
                return [{"eventid": "2", "clock": "1120", "value": "0"}]
            return [
                {
                    "eventid": "1",
                    "clock": "1000",
                    "r_eventid": "2",
                    "hosts": [{"hostid": "10", "host": "server"}],
                }
            ]
        if method == "item.get":
            return [
                {
                    "itemid": "20",
                    "name": "KZabbix incident evidence snapshot",
                    "key_": "vfs.file.contents[/var/tmp/kzabbix/evidence.json]",
                    "value_type": "4",
                    "lastclock": "1100",
                    "lastvalue": '{"host":"server"}',
                },
                {
                    "itemid": "21",
                    "name": "Disk latency",
                    "key_": "vfs.dev.write.await[nvme0n1]",
                    "value_type": "0",
                    "lastclock": "1100",
                    "lastvalue": "25",
                },
            ]
        if method == "history.get":
            if params["history"] == 4:
                return [{"itemid": "20", "clock": "990", "value": '{"host":"server","logs":{}}'}]
            return [{"itemid": "21", "clock": "1000", "value": "25"}]
        if method == "problem.get":
            return []
        raise AssertionError(method)


def test_collect_incident_includes_snapshot_and_actual_duration():
    evidence = FakeZabbix().collect_incident("1")

    assert evidence["actual_duration_seconds"] == 120
    assert evidence["recovery_event"]["eventid"] == "2"
    assert evidence["evidence_snapshots"][0]["data"]["host"] == "server"
    assert evidence["items"][0]["lastvalue"] == "[captured in evidence_snapshots]"
