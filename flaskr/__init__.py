import os

from flask import Flask, render_template
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()

KAFKA_SERVER = os.getenv('KAFKA_SERVER')
config = {
          # User-specific properties that you must set
          'bootstrap.servers': KAFKA_SERVER,

        'request.timeout.ms': 60000,

        'delivery.timeout.ms': 60000,

        'transaction.timeout.ms': 60000,

        

          # Fixed properties
          'acks': 'all'
      }

# Create Producer instance
producer = Producer(config)

# Optional per-message delivery callback (triggered by poll() or flush())
# when a message has been successfully delivered or permanently
# failed delivery (after retries).
def delivery_callback(err, msg):
    if err:
        print('ERROR: Message failed delivery: {}'.format(err))
    else:
        print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
            topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    def main():
        move = {}
        return render_template(
            'index.html'
            ,move=move
        )
    
    @app.route('/add_move/<key>/<value>', methods=['POST'])
    def add_move(key, value):
      # Produce data by selecting random values from these lists.
      topic = "moves"

      producer.produce(topic, value, key, on_delivery=delivery_callback)

      # Block until the messages are sent.
      producer.poll(10000)
      producer.flush()

      return ''
    
    @app.route('/add_game/<key>/<value>', methods=['POST'])
    def add_game(key, value):
      # Produce data by selecting random values from these lists.
      topic = "games"

      producer.produce(topic, value, key, on_delivery=delivery_callback)

      # Block until the messages are sent.
      producer.poll(10000)
      producer.flush()

      return ''

    

    return app
