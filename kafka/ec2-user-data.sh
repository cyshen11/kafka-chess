 #!/bin/bash
 cd kafka
 cd kafka_2.13-4.0.0
 KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
 bin/kafka-storage.sh format --standalone -t $KAFKA_CLUSTER_ID -c config/server.properties
 bin/kafka-server-start.sh config/server.properties