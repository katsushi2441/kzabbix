var params = JSON.parse(value);
var request = new HttpRequest();
request.addHeader('Content-Type: application/json');
request.addHeader('X-KZabbix-Token: ' + params.token);

var payload = {
    event_id: params.event_id,
    event_name: params.event_name,
    event_status: params.event_status,
    event_severity: params.event_severity,
    host_id: params.host_id,
    host_name: params.host_name,
    trigger_id: params.trigger_id,
    trigger_expression: params.trigger_expression,
    event_date: params.event_date,
    event_time: params.event_time
};

var response = request.post(params.url, JSON.stringify(payload));
if (request.getStatus() < 200 || request.getStatus() >= 300) {
    throw 'kzabbix webhook failed: HTTP ' + request.getStatus() + ' ' + response;
}
return response;

