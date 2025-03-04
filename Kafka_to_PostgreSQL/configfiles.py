postgresql_config={
"dbname":"postgres",  # your Postgresql database name
"user":"postgres",  # your Postgresql user name
"password":"pass"   # your Postgresql password
}


api_key = 'XXXXXXXX'    # your KAFKA api_key

api_secret='XXXXXXXXXXXXXX'    # your KAFKA api_secret

Resource='XXXXXXXXXXXXX'    # your KAFKA resource

Bootstrap_server='XXXXXXXXXXXXX'    # your KAFKA bootstrap server
kafka_topic = "topic_01"    # your KAFKA topic

kafka_server_config = {
    'bootstrap.servers': Bootstrap_server,
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': api_key,
    'sasl.password': api_secret,
    'session.timeout.ms': '45000'
}
